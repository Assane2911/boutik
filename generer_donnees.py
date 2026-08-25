"""
Génère un jeu de données simulé pour une boutique de quartier à Dakar.
Sert de mode démo dans l'application, et de fichier modèle pour les vrais clients.

Usage : python generer_donnees.py
Produit : donnees_demo.xlsx (3 feuilles : clients, produits, ventes)
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

QUARTIERS = [
    "Grand Yoff", "Ouakam", "Parcelles Assainies", "Médina", "Yoff",
    "Liberté 6", "Sacré-Cœur", "Pikine", "Guédiawaye", "Ngor",
]

PRODUITS = [
    # nom, catégorie, prix d'achat, prix de vente, popularité relative
    ("Riz brisé 50 kg", "Alimentaire", 19000, 22500, 6),
    ("Huile végétale 1 L", "Alimentaire", 1100, 1400, 9),
    ("Sucre en poudre 1 kg", "Alimentaire", 650, 850, 9),
    ("Lait en poudre 400 g", "Alimentaire", 2200, 2800, 5),
    ("Café soluble 100 g", "Alimentaire", 1800, 2400, 4),
    ("Thé Ataya 250 g", "Alimentaire", 900, 1250, 8),
    ("Pain (baguette)", "Alimentaire", 125, 175, 12),
    ("Pâtes alimentaires 500 g", "Alimentaire", 400, 600, 7),
    ("Eau minérale 1,5 L", "Boissons", 350, 500, 10),
    ("Soda 33 cl", "Boissons", 400, 600, 8),
    ("Jus de bissap 1 L", "Boissons", 700, 1000, 4),
    ("Savon de ménage", "Hygiène", 300, 450, 7),
    ("Détergent 500 g", "Hygiène", 900, 1300, 5),
    ("Dentifrice 75 ml", "Hygiène", 800, 1150, 3),
    ("Papier hygiénique x4", "Hygiène", 950, 1400, 4),
    ("Piles LR6 x2", "Divers", 500, 800, 3),
    ("Cahier 100 pages", "Divers", 350, 550, 3),
    ("Recharge téléphonique 1000", "Divers", 950, 1000, 11),
    ("Charbon de bois 5 kg", "Divers", 1500, 2000, 4),
    ("Allumettes x10", "Divers", 200, 300, 5),
]

PRENOMS = [
    "Awa", "Moussa", "Fatou", "Ibrahima", "Aminata", "Cheikh", "Mariama",
    "Ousmane", "Ndèye", "Modou", "Khady", "Alioune", "Sokhna", "Babacar",
    "Rokhaya", "Lamine", "Bineta", "Serigne", "Coumba", "Pape",
]
NOMS = [
    "Diop", "Ndiaye", "Fall", "Sow", "Ba", "Gueye", "Sarr", "Faye",
    "Diallo", "Mbaye", "Seck", "Cissé", "Thiam", "Sy", "Kane",
]

MODES = ["Espèces", "Wave", "Orange Money", "Crédit"]
POIDS_MODES = [0.55, 0.20, 0.15, 0.10]


def generer(n_clients: int = 120, n_ventes: int = 2600, jours: int = 365, seed: int = 42):
    rng = np.random.default_rng(seed)

    # --- Clients ---
    fin = pd.Timestamp.today().normalize()
    debut = fin - pd.Timedelta(days=jours)

    clients = pd.DataFrame({
        "client_id": [f"C{i:03d}" for i in range(1, n_clients + 1)],
        "nom_client": [
            f"{rng.choice(PRENOMS)} {rng.choice(NOMS)}" for _ in range(n_clients)
        ],
        "quartier": rng.choice(QUARTIERS, n_clients),
        "date_inscription": [
            debut + pd.Timedelta(days=int(d))
            for d in rng.integers(0, jours, n_clients)
        ],
    })

    # --- Produits ---
    produits = pd.DataFrame(
        PRODUITS, columns=["nom_produit", "categorie", "prix_achat", "prix_vente", "popularite"]
    )
    produits.insert(0, "produit_id", [f"P{i:03d}" for i in range(1, len(produits) + 1)])
    produits["stock_actuel"] = rng.integers(0, 90, len(produits))
    produits["seuil_alerte"] = rng.integers(8, 25, len(produits))

    # --- Ventes ---
    poids_prod = produits["popularite"].to_numpy() / produits["popularite"].sum()
    idx_prod = rng.choice(len(produits), n_ventes, p=poids_prod)

    # Les clients fidèles achètent plus souvent (loi de Pareto adoucie)
    poids_clients = rng.pareto(1.4, n_clients) + 1
    poids_clients /= poids_clients.sum()
    idx_client = rng.choice(n_clients, n_ventes, p=poids_clients)

    # Saisonnalité : pic en fin de mois (paie) et le week-end
    offsets = rng.integers(0, jours, n_ventes)
    dates = pd.to_datetime([debut + pd.Timedelta(days=int(d)) for d in offsets])
    bonus = (dates.day >= 26) | (dates.dayofweek >= 5)
    garder = rng.random(n_ventes) < np.where(bonus, 1.0, 0.75)

    ventes = pd.DataFrame({
        "date_vente": dates,
        "client_id": clients.loc[idx_client, "client_id"].to_numpy(),
        "produit_id": produits.loc[idx_prod, "produit_id"].to_numpy(),
        "quantite": rng.integers(1, 6, n_ventes),
        "prix_unitaire": produits.loc[idx_prod, "prix_vente"].to_numpy(),
        "mode_paiement": rng.choice(MODES, n_ventes, p=POIDS_MODES),
    })[garder].reset_index(drop=True)

    ventes.insert(0, "vente_id", [f"V{i:05d}" for i in range(1, len(ventes) + 1)])
    ventes["montant_total"] = ventes["quantite"] * ventes["prix_unitaire"]

    # Paiements : le crédit est partiellement, voire pas du tout, réglé
    part = np.where(
        ventes["mode_paiement"] == "Crédit",
        rng.choice([0.0, 0.3, 0.5, 1.0], len(ventes), p=[0.35, 0.25, 0.20, 0.20]),
        1.0,
    )
    ventes["montant_paye"] = (ventes["montant_total"] * part).round(0)

    ventes = ventes.sort_values("date_vente").reset_index(drop=True)
    produits = produits.drop(columns=["popularite"])
    return clients, produits, ventes


def main():
    clients, produits, ventes = generer()
    with pd.ExcelWriter("donnees_demo.xlsx", engine="openpyxl") as writer:
        ventes.to_excel(writer, sheet_name="ventes", index=False)
        produits.to_excel(writer, sheet_name="produits", index=False)
        clients.to_excel(writer, sheet_name="clients", index=False)
    print(f"donnees_demo.xlsx créé — {len(ventes)} ventes, "
          f"{len(produits)} produits, {len(clients)} clients.")


if __name__ == "__main__":
    main()
