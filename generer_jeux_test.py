"""
Génère plusieurs jeux de données de test pour Boutik.

Chaque fichier reproduit un commerce réel différent, afin d'éprouver
l'application sur des situations que la boutique de démonstration ne
couvre pas : gros paniers, ardoise lourde, activité en déclin,
historique court, fichier mal formé.

Usage : python generer_jeux_test.py
Produit : un dossier jeux_test/ contenant 5 classeurs Excel.
"""

import os

import numpy as np
import pandas as pd

PRENOMS = [
    "Awa", "Moussa", "Fatou", "Ibrahima", "Aminata", "Cheikh", "Mariama",
    "Ousmane", "Ndèye", "Modou", "Khady", "Alioune", "Sokhna", "Babacar",
    "Rokhaya", "Lamine", "Bineta", "Serigne", "Coumba", "Pape", "Astou",
    "Malick", "Dieynaba", "Souleymane", "Adama", "Mame Diarra",
]
NOMS = [
    "Diop", "Ndiaye", "Fall", "Sow", "Ba", "Gueye", "Sarr", "Faye", "Diallo",
    "Mbaye", "Seck", "Cissé", "Thiam", "Sy", "Kane", "Diouf", "Camara", "Dieng",
]
QUARTIERS = [
    "Grand Yoff", "Ouakam", "Parcelles Assainies", "Médina", "Yoff", "Liberté 6",
    "Sacré-Cœur", "Pikine", "Guédiawaye", "Ngor", "Thiaroye", "Rufisque",
]

# --------------------------------------------------------------------------
# Catalogues par secteur : nom, catégorie, prix d'achat, prix de vente, popularité
# --------------------------------------------------------------------------

PHARMACIE = [
    ("Paracétamol 500 mg (boîte)", "Médicaments", 600, 900, 12),
    ("Ibuprofène 400 mg (boîte)", "Médicaments", 900, 1400, 8),
    ("Sirop antitussif 125 ml", "Médicaments", 1800, 2600, 6),
    ("Sels de réhydratation x10", "Médicaments", 800, 1200, 7),
    ("Antipaludique (cure)", "Médicaments", 3500, 5000, 9),
    ("Vitamine C effervescente", "Médicaments", 1200, 1800, 5),
    ("Pansements adhésifs x20", "Parapharmacie", 700, 1100, 6),
    ("Alcool à 70° 250 ml", "Parapharmacie", 500, 800, 7),
    ("Thermomètre digital", "Matériel", 2500, 4000, 2),
    ("Tensiomètre bras", "Matériel", 12000, 18500, 1),
    ("Lait infantile 400 g", "Puériculture", 4200, 5500, 5),
    ("Couches bébé x30", "Puériculture", 4500, 6000, 6),
    ("Crème hydratante 200 ml", "Cosmétique", 2200, 3200, 4),
    ("Savon dermatologique", "Cosmétique", 1100, 1700, 5),
    ("Moustiquaire imprégnée", "Parapharmacie", 3000, 4500, 3),
    ("Test de glycémie x25", "Matériel", 6500, 9500, 2),
]

QUINCAILLERIE = [
    ("Ciment 50 kg", "Matériaux", 3800, 4500, 11),
    ("Fer à béton 8 mm (barre)", "Matériaux", 3200, 4000, 8),
    ("Sable (m³)", "Matériaux", 12000, 16000, 4),
    ("Peinture blanche 20 L", "Peinture", 22000, 29000, 3),
    ("Rouleau + pinceau", "Peinture", 2500, 3800, 5),
    ("Carreaux 40x40 (m²)", "Revêtement", 4500, 6500, 5),
    ("Tuyau PVC 3 m", "Plomberie", 2800, 4000, 6),
    ("Robinet mélangeur", "Plomberie", 8500, 13000, 3),
    ("Câble électrique 2,5 mm (10 m)", "Électricité", 5500, 8000, 5),
    ("Disjoncteur 20 A", "Électricité", 3500, 5500, 4),
    ("Ampoule LED 12 W", "Électricité", 900, 1500, 9),
    ("Serrure de porte", "Quincaillerie", 6500, 10000, 3),
    ("Cadenas 50 mm", "Quincaillerie", 2200, 3500, 4),
    ("Marteau", "Outillage", 3000, 4800, 3),
    ("Brouette", "Outillage", 18000, 25000, 2),
    ("Clous 1 kg", "Quincaillerie", 800, 1300, 7),
]

ALIMENTAIRE = [
    ("Riz brisé 50 kg", "Alimentaire", 19000, 22500, 6),
    ("Huile végétale 1 L", "Alimentaire", 1100, 1400, 9),
    ("Sucre en poudre 1 kg", "Alimentaire", 650, 850, 9),
    ("Lait en poudre 400 g", "Alimentaire", 2200, 2800, 5),
    ("Thé Ataya 250 g", "Alimentaire", 900, 1250, 8),
    ("Pain (baguette)", "Alimentaire", 125, 175, 12),
    ("Pâtes alimentaires 500 g", "Alimentaire", 400, 600, 7),
    ("Eau minérale 1,5 L", "Boissons", 350, 500, 10),
    ("Soda 33 cl", "Boissons", 400, 600, 8),
    ("Jus de bissap 1 L", "Boissons", 700, 1000, 4),
    ("Savon de ménage", "Hygiène", 300, 450, 7),
    ("Détergent 500 g", "Hygiène", 900, 1300, 5),
    ("Recharge téléphonique 1000", "Divers", 950, 1000, 11),
    ("Charbon de bois 5 kg", "Divers", 1500, 2000, 4),
]

MODES = ["Espèces", "Wave", "Orange Money", "Crédit"]


def construire(
    catalogue,
    n_clients,
    n_ventes,
    jours,
    poids_modes,
    part_credit_regle,
    tendance=0.0,
    stock_bas=False,
    quantite_max=6,
    seed=1,
):
    """Fabrique un triplet (clients, produits, ventes) cohérent.

    tendance : croissance mensuelle du volume (+0.04 = +4 %/mois, -0.05 = déclin).
    stock_bas : force des stocks faibles pour déclencher les alertes de rupture.
    part_credit_regle : probabilités de règlement d'une vente à crédit.
    """
    rng = np.random.default_rng(seed)
    fin = pd.Timestamp.today().normalize()
    debut = fin - pd.Timedelta(days=jours)

    clients = pd.DataFrame({
        "client_id": [f"C{i:03d}" for i in range(1, n_clients + 1)],
        "nom_client": [f"{rng.choice(PRENOMS)} {rng.choice(NOMS)}" for _ in range(n_clients)],
        "quartier": rng.choice(QUARTIERS, n_clients),
        "date_inscription": [
            debut + pd.Timedelta(days=int(d)) for d in rng.integers(0, jours, n_clients)
        ],
    })

    produits = pd.DataFrame(
        catalogue,
        columns=["nom_produit", "categorie", "prix_achat", "prix_vente", "popularite"],
    )
    produits.insert(0, "produit_id", [f"P{i:03d}" for i in range(1, len(produits) + 1)])
    if stock_bas:
        produits["stock_actuel"] = rng.integers(0, 14, len(produits))
        # Force quelques ruptures franches pour éprouver les alertes
        en_rupture = rng.choice(len(produits), max(3, len(produits) // 4), replace=False)
        produits.loc[en_rupture, "stock_actuel"] = 0
    else:
        produits["stock_actuel"] = rng.integers(5, 95, len(produits))
    produits["seuil_alerte"] = rng.integers(8, 25, len(produits))

    poids_prod = produits["popularite"].to_numpy() / produits["popularite"].sum()
    idx_prod = rng.choice(len(produits), n_ventes, p=poids_prod)

    poids_clients = rng.pareto(1.4, n_clients) + 1
    poids_clients /= poids_clients.sum()
    idx_client = rng.choice(n_clients, n_ventes, p=poids_clients)

    offsets = rng.integers(0, jours, n_ventes)
    dates = pd.to_datetime([debut + pd.Timedelta(days=int(d)) for d in offsets])

    # Tendance : plus la vente est récente, plus (ou moins) elle a de chances d'exister
    mois_ecoules = offsets / 30.0
    proba = np.clip((1 + tendance) ** mois_ecoules, 0.15, 1.0)
    proba = proba / proba.max()
    # Pic de fin de mois et de week-end
    proba = proba * np.where((dates.day >= 26) | (dates.dayofweek >= 5), 1.0, 0.78)
    garder = rng.random(n_ventes) < proba

    ventes = pd.DataFrame({
        "date_vente": dates,
        "client_id": clients.loc[idx_client, "client_id"].to_numpy(),
        "produit_id": produits.loc[idx_prod, "produit_id"].to_numpy(),
        "quantite": rng.integers(1, quantite_max, n_ventes),
        "prix_unitaire": produits.loc[idx_prod, "prix_vente"].to_numpy(),
        "mode_paiement": rng.choice(MODES, n_ventes, p=poids_modes),
    })[garder].reset_index(drop=True)

    ventes.insert(0, "vente_id", [f"V{i:05d}" for i in range(1, len(ventes) + 1)])
    ventes["montant_total"] = ventes["quantite"] * ventes["prix_unitaire"]

    part = np.where(
        ventes["mode_paiement"] == "Crédit",
        rng.choice([0.0, 0.3, 0.5, 1.0], len(ventes), p=part_credit_regle),
        1.0,
    )
    ventes["montant_paye"] = (ventes["montant_total"] * part).round(0)
    ventes = ventes.sort_values("date_vente").reset_index(drop=True)

    return clients, produits.drop(columns=["popularite"]), ventes


def ecrire(dossier, nom_fichier, clients, produits, ventes):
    chemin = os.path.join(dossier, nom_fichier)
    with pd.ExcelWriter(chemin, engine="openpyxl") as writer:
        ventes.to_excel(writer, sheet_name="ventes", index=False)
        produits.to_excel(writer, sheet_name="produits", index=False)
        clients.to_excel(writer, sheet_name="clients", index=False)
    return chemin


def main():
    dossier = "jeux_test"
    os.makedirs(dossier, exist_ok=True)
    resume = []

    # 1. Pharmacie : gros volume, activité en croissance, très peu de crédit
    jeu = construire(
        PHARMACIE, n_clients=220, n_ventes=4200, jours=540,
        poids_modes=[0.45, 0.28, 0.22, 0.05],
        part_credit_regle=[0.15, 0.20, 0.25, 0.40],
        tendance=0.035, quantite_max=4, seed=11,
    )
    ecrire(dossier, "pharmacie_dakar.xlsx", *jeu)
    resume.append(("pharmacie_dakar.xlsx", jeu))

    # 2. Quincaillerie : peu de ventes, montants élevés, ardoise très lourde
    jeu = construire(
        QUINCAILLERIE, n_clients=70, n_ventes=900, jours=365,
        poids_modes=[0.30, 0.15, 0.15, 0.40],
        part_credit_regle=[0.45, 0.25, 0.20, 0.10],
        tendance=0.0, quantite_max=12, seed=22,
    )
    ecrire(dossier, "quincaillerie_pikine.xlsx", *jeu)
    resume.append(("quincaillerie_pikine.xlsx", jeu))

    # 3. Commerce en difficulté : chiffre d'affaires en déclin, stocks à sec
    jeu = construire(
        ALIMENTAIRE, n_clients=150, n_ventes=2400, jours=450,
        poids_modes=[0.40, 0.15, 0.12, 0.33],
        part_credit_regle=[0.50, 0.25, 0.15, 0.10],
        tendance=-0.06, stock_bas=True, seed=33,
    )
    ecrire(dossier, "boutique_en_difficulte.xlsx", *jeu)
    resume.append(("boutique_en_difficulte.xlsx", jeu))

    # 4. Nouvelle boutique : trois mois d'historique, petit volume
    jeu = construire(
        ALIMENTAIRE, n_clients=35, n_ventes=280, jours=95,
        poids_modes=[0.60, 0.22, 0.13, 0.05],
        part_credit_regle=[0.20, 0.25, 0.25, 0.30],
        tendance=0.10, seed=44,
    )
    ecrire(dossier, "nouvelle_boutique.xlsx", *jeu)
    resume.append(("nouvelle_boutique.xlsx", jeu))

    # 5. Fichier volontairement incomplet : la colonne montant_paye est absente
    clients, produits, ventes = construire(
        ALIMENTAIRE, n_clients=40, n_ventes=400, jours=180,
        poids_modes=[0.55, 0.20, 0.15, 0.10],
        part_credit_regle=[0.35, 0.25, 0.20, 0.20], seed=55,
    )
    ecrire(dossier, "fichier_incomplet.xlsx",
           clients, produits, ventes.drop(columns=["montant_paye"]))

    print(f"Dossier « {dossier} » créé.\n")
    for nom, (_, prods, v) in resume:
        ca = v["montant_total"].sum()
        du = (v["montant_total"] - v["montant_paye"]).sum()
        print(f"{nom:32} {len(v):>5} ventes | CA {ca:>12,.0f} | dû {du:>10,.0f} FCFA"
              .replace(",", " "))
    print(f"{'fichier_incomplet.xlsx':32} colonne montant_paye retirée volontairement")


if __name__ == "__main__":
    main()
