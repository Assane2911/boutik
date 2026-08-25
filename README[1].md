# Boutik — tableau de bord pour commerces et PME

Un commerçant enregistre ses ventes dans un cahier ou un fichier Excel, puis
n'en fait rien. Boutik lit ce fichier et lui rend quatre réponses qu'il n'a pas :
ce qu'il a réellement gagné, ce qui va manquer en rayon, quels clients ont
disparu, et qui lui doit de l'argent.

---

## Lancer le projet

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. Elle démarre en mode
démonstration, avec les données simulées d'une boutique de quartier
dakaroise — utile pour les captures d'écran du portfolio et pour les
démonstrations commerciales avant d'avoir un vrai client.

Pour régénérer le fichier de démonstration :

```bash
python generer_donnees.py
```

## Structure du projet

| Fichier | Rôle |
| --- | --- |
| `app.py` | L'application Streamlit (4 onglets : Ventes, Stock, Clients, Impayés) |
| `generer_donnees.py` | Génère la boutique fictive : 120 clients, 20 produits, ~2 200 ventes sur 12 mois |
| `donnees_demo.xlsx` | Le classeur de démonstration, qui sert aussi de modèle client |
| `requirements.txt` | Dépendances |

## Format attendu des données

Un classeur Excel à trois feuilles. C'est le même modèle relationnel que ton
projet SQL — les jointures et agrégations que tu écris en SQL sont ici en
pandas, ce qui rend les deux exercices complémentaires.

**ventes** : `vente_id`, `date_vente`, `client_id`, `produit_id`, `quantite`,
`prix_unitaire`, `mode_paiement`, `montant_total`, `montant_paye`

**produits** : `produit_id`, `nom_produit`, `categorie`, `prix_achat`,
`prix_vente`, `stock_actuel`, `seuil_alerte`

**clients** : `client_id`, `nom_client`, `quartier`, `date_inscription`

Le chargeur vérifie la présence des feuilles et des colonnes, et affiche un
message précis quand il en manque une. C'est le premier point de friction chez
un vrai client : ses colonnes ne s'appelleront jamais comme les tiennes.

## Ce que l'application calcule

- **Ventes** — chiffre d'affaires et marge brute par mois, top 10 produits,
  répartition par mode de paiement (utile localement : espèces, Wave,
  Orange Money, crédit).
- **Stock** — vitesse d'écoulement par produit, jours de stock restants,
  quantité à commander pour tenir 30 jours, valeur du capital immobilisé.
- **Clients** — meilleurs clients, clients dormants avec seuil réglable,
  chiffre d'affaires par quartier.
- **Impayés** — balance âgée (0-30, 31-60, 61-90, 90+ jours), montant dû par
  client, export CSV pour la relance.

---

## Mettre en ligne (gratuit)

1. Crée un dépôt GitHub avec ces fichiers.
2. Va sur [share.streamlit.io](https://share.streamlit.io), connecte ton compte
   GitHub, sélectionne le dépôt et `app.py`.
3. Tu obtiens une URL publique en quelques minutes.

Cette URL est ton meilleur atout en entretien : un recruteur clique et voit
l'outil tourner, au lieu de lire un notebook.

## Feuille de route : du portfolio au produit

**Phase 1 — Portfolio (2 à 3 semaines).** Ce que tu as ici. Déploie-le, écris
un article LinkedIn qui montre le problème avant la solution (« 60 % des
boutiques de quartier ignorent le montant réel de leur ardoise »), et intègre
une capture d'écran dans ton CV.

**Phase 2 — Premier utilisateur réel (1 mois).** Trouve un commerçant, un
pharmacien ou un distributeur que tu connais. Ne vends rien : propose d'analyser
gratuitement ses trois derniers mois. Tu apprendras plus en une séance sur ses
vrais fichiers qu'en dix projets simulés — surtout sur le désordre des données,
qui est le cœur du métier.

**Phase 3 — Ce qui transforme l'outil en produit.**
- Saisie des ventes directement dans l'application, pour les commerçants sans Excel
- Comptes utilisateurs et base de données (PostgreSQL via Supabase, gratuit au départ)
- Rappel automatique des impayés par SMS ou WhatsApp — c'est la fonction qui
  fait payer, parce qu'elle rapporte de l'argent immédiatement au commerçant
- Prévision de la demande (modèle simple de moyenne mobile, puis Prophet)
- Version multi-boutiques pour les gérants qui en ont plusieurs

**Phase 4 — Modèle économique.** Un abonnement mensuel de l'ordre de
5 000 à 15 000 FCFA par boutique reste accessible et devient significatif à
partir de quelques dizaines de clients. Une alternative plus rapide à monétiser :
la prestation d'analyse ponctuelle pour PME, facturée au rapport, avec l'outil
comme moyen de production.

## Limites actuelles, à assumer en entretien

- Aucune persistance : les données ne sont pas sauvegardées entre deux sessions
- Un seul utilisateur, pas d'authentification
- Le stock est une photo à l'instant T, pas un historique de mouvements
- Les prévisions de rupture supposent une demande stable, sans saisonnalité

Savoir énoncer les limites de son propre travail est un signal de sérieux plus
fort que la longue liste des fonctionnalités.
