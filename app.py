"""
Boutik — tableau de bord pour commerces et PME.

Le gérant dépose son fichier de ventes ; l'application lui rend
son chiffre d'affaires, ses ruptures de stock à venir, ses clients
qui ne reviennent plus et ses impayés.

Lancer : streamlit run app.py
"""

import io
from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from generer_donnees import generer

# --------------------------------------------------------------------------
# Configuration et style
# --------------------------------------------------------------------------

st.set_page_config(page_title="Boutik", page_icon="🧾", layout="wide")

ENCRE = "#12291F"      # vert très sombre, fond des cartes
VERT = "#1F7A5A"       # accent principal
SABLE = "#E8DFC8"      # fond neutre chaud
AMBRE = "#D89A2E"      # alertes
BRIQUE = "#B24A38"     # ruptures / impayés
PALETTE = [VERT, AMBRE, BRIQUE, "#4E8FA8", "#7A6A9B"]

st.markdown(
    f"""
    <style>
      .stApp {{ background: {SABLE}; }}
      h1, h2, h3 {{ color: {ENCRE}; letter-spacing: -0.02em; }}
      div[data-testid="stMetric"] {{
          background: {ENCRE}; border-radius: 10px; padding: 16px 18px;
      }}
      div[data-testid="stMetric"] label p {{
          color: #A9BFB4 !important; font-size: 0.78rem;
          text-transform: uppercase; letter-spacing: 0.08em;
      }}
      div[data-testid="stMetricValue"] {{ color: #FFFFFF; font-size: 1.6rem; }}
      section[data-testid="stSidebar"] {{ background: {ENCRE}; }}
      section[data-testid="stSidebar"] * {{ color: #E8DFC8; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def fcfa(valeur) -> str:
    """Formate un montant en francs CFA, séparateur d'espace."""
    return f"{valeur:,.0f}".replace(",", " ") + " FCFA"


# --------------------------------------------------------------------------
# Chargement des données
# --------------------------------------------------------------------------

COLONNES_REQUISES = {
    "ventes": ["date_vente", "client_id", "produit_id", "quantite",
               "montant_total", "montant_paye"],
    "produits": ["produit_id", "nom_produit", "categorie", "prix_achat",
                 "prix_vente", "stock_actuel", "seuil_alerte"],
    "clients": ["client_id", "nom_client", "quartier"],
}


@st.cache_data
def charger_demo():
    clients, produits, ventes = generer()
    return clients, produits, ventes


@st.cache_data
def charger_fichier(contenu: bytes):
    """Lit un classeur Excel à trois feuilles : ventes, produits, clients."""
    feuilles = pd.read_excel(io.BytesIO(contenu), sheet_name=None)
    manquantes = [f for f in COLONNES_REQUISES if f not in feuilles]
    if manquantes:
        raise ValueError(
            "Feuilles absentes du classeur : " + ", ".join(manquantes)
            + ". Le fichier doit contenir les feuilles ventes, produits et clients."
        )
    for feuille, colonnes in COLONNES_REQUISES.items():
        absentes = [c for c in colonnes if c not in feuilles[feuille].columns]
        if absentes:
            raise ValueError(
                f"Colonnes absentes dans la feuille « {feuille} » : "
                + ", ".join(absentes)
            )
    ventes = feuilles["ventes"].copy()
    ventes["date_vente"] = pd.to_datetime(ventes["date_vente"])
    return feuilles["clients"], feuilles["produits"], ventes


def modele_excel(clients, produits, ventes) -> bytes:
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as writer:
        ventes.to_excel(writer, sheet_name="ventes", index=False)
        produits.to_excel(writer, sheet_name="produits", index=False)
        clients.to_excel(writer, sheet_name="clients", index=False)
    return tampon.getvalue()


# --------------------------------------------------------------------------
# Barre latérale
# --------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## Boutik")
    st.caption("Vos ventes, lues à votre place.")

    source = st.radio(
        "Données", ["Boutique de démonstration", "Mon fichier Excel"],
        label_visibility="collapsed",
    )

    clients = produits = ventes = None

    if source == "Mon fichier Excel":
        fichier = st.file_uploader("Déposez votre classeur", type=["xlsx", "xls"])
        if fichier is not None:
            try:
                clients, produits, ventes = charger_fichier(fichier.getvalue())
                st.success(f"{len(ventes)} ventes chargées.")
            except Exception as erreur:  # noqa: BLE001
                st.error(str(erreur))
        else:
            st.info("Aucun fichier chargé. Téléchargez le modèle ci-dessous "
                    "et remplissez-le avec vos données.")
            clients, produits, ventes = charger_demo()
            st.download_button(
                "Télécharger le modèle",
                modele_excel(*charger_demo()),
                file_name="modele_boutik.xlsx",
            )
    else:
        clients, produits, ventes = charger_demo()

# --------------------------------------------------------------------------
# Préparation
# --------------------------------------------------------------------------

if ventes is None or produits is None or clients is None:
    st.title("Boutik")
    st.info(
        "Aucune donnée à analyser pour l'instant. Choisissez « Boutique de "
        "démonstration » dans la barre latérale, ou corrigez votre classeur "
        "d'après le message affiché à gauche."
    )
    st.stop()

ventes = ventes.merge(produits, on="produit_id", how="left").merge(
    clients, on="client_id", how="left"
)
ventes["reste_a_payer"] = ventes["montant_total"] - ventes["montant_paye"]
ventes["marge"] = ventes["montant_total"] - ventes["quantite"] * ventes["prix_achat"]

date_max = ventes["date_vente"].max()
date_min = ventes["date_vente"].min()

with st.sidebar:
    st.markdown("---")
    periode = st.selectbox(
        "Période analysée",
        ["30 derniers jours", "90 derniers jours", "12 derniers mois", "Tout l'historique"],
        index=2,
    )

jours = {"30 derniers jours": 30, "90 derniers jours": 90,
         "12 derniers mois": 365}.get(periode)
if jours:
    debut = date_max - timedelta(days=jours)
    periode_ventes = ventes[ventes["date_vente"] >= debut]
else:
    debut = date_min
    periode_ventes = ventes

# --------------------------------------------------------------------------
# En-tête et indicateurs
# --------------------------------------------------------------------------

st.title("Tableau de bord")
st.caption(
    f"Du {debut:%d/%m/%Y} au {date_max:%d/%m/%Y} — "
    f"{len(periode_ventes)} ventes enregistrées."
)

ca = periode_ventes["montant_total"].sum()
marge = periode_ventes["marge"].sum()
panier = periode_ventes["montant_total"].mean() if len(periode_ventes) else 0
impaye = periode_ventes["reste_a_payer"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chiffre d'affaires", fcfa(ca))
c2.metric("Marge brute", fcfa(marge),
          f"{marge / ca * 100:.1f} % du CA" if ca else "—")
c3.metric("Panier moyen", fcfa(panier))
c4.metric("Reste à encaisser", fcfa(impaye))

onglet_ca, onglet_stock, onglet_clients, onglet_impayes = st.tabs(
    ["Ventes", "Stock", "Clients", "Impayés"]
)

# --------------------------------------------------------------------------
# Ventes
# --------------------------------------------------------------------------

with onglet_ca:
    par_mois = (
        periode_ventes.set_index("date_vente")
        .resample("MS")[["montant_total", "marge"]].sum().reset_index()
    )
    fig = go.Figure()
    fig.add_bar(x=par_mois["date_vente"], y=par_mois["montant_total"],
                name="Chiffre d'affaires", marker_color=VERT)
    fig.add_scatter(x=par_mois["date_vente"], y=par_mois["marge"],
                    name="Marge", mode="lines+markers", line=dict(color=AMBRE, width=3))
    fig.update_layout(
        height=340, margin=dict(t=30, b=0, l=0, r=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.15, x=0),
    )
    st.subheader("Évolution mensuelle")
    st.plotly_chart(fig, width="stretch")

    gauche, droite = st.columns([3, 2])

    with gauche:
        st.subheader("Produits les plus vendus")
        top = (
            periode_ventes.groupby("nom_produit")
            .agg(chiffre=("montant_total", "sum"), unites=("quantite", "sum"))
            .sort_values("chiffre", ascending=False).head(10).reset_index()
        )
        fig_top = px.bar(top.sort_values("chiffre"), x="chiffre", y="nom_produit",
                         orientation="h", color_discrete_sequence=[VERT])
        fig_top.update_layout(
            height=380, margin=dict(t=10, b=0, l=0, r=0),
            xaxis_title="", yaxis_title="",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_top, width="stretch")

    with droite:
        st.subheader("Par mode de paiement")
        modes = periode_ventes.groupby("mode_paiement")["montant_total"].sum().reset_index()
        fig_modes = px.pie(modes, values="montant_total", names="mode_paiement",
                           hole=0.55, color_discrete_sequence=PALETTE)
        fig_modes.update_layout(height=380, margin=dict(t=10, b=0, l=0, r=0),
                                paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_modes, width="stretch")

# --------------------------------------------------------------------------
# Stock
# --------------------------------------------------------------------------

with onglet_stock:
    st.subheader("Ce qui va manquer en premier")

    jours_observes = max((date_max - debut).days, 1)
    vitesse = (
        periode_ventes.groupby("produit_id")["quantite"].sum() / jours_observes
    ).rename("ventes_par_jour")

    stock = produits.merge(vitesse, on="produit_id", how="left").fillna({"ventes_par_jour": 0})
    stock["jours_restants"] = stock.apply(
        lambda r: r["stock_actuel"] / r["ventes_par_jour"]
        if r["ventes_par_jour"] > 0 else float("inf"), axis=1,
    )
    stock["a_commander"] = (stock["ventes_par_jour"] * 30 - stock["stock_actuel"]).clip(lower=0).round()

    def etat(ligne):
        if ligne["stock_actuel"] == 0:
            return "Rupture"
        if ligne["jours_restants"] <= 7 or ligne["stock_actuel"] <= ligne["seuil_alerte"]:
            return "À commander"
        return "Suffisant"

    stock["etat"] = stock.apply(etat, axis=1)

    urgents = stock[stock["etat"] != "Suffisant"].sort_values("jours_restants")
    a1, a2 = st.columns(2)
    a1.metric("Produits en rupture", int((stock["etat"] == "Rupture").sum()))
    a2.metric("Produits à recommander", int((stock["etat"] == "À commander").sum()))

    if urgents.empty:
        st.success("Aucune rupture prévue sur les 7 prochains jours.")
    else:
        affichage = urgents[[
            "nom_produit", "categorie", "stock_actuel", "ventes_par_jour",
            "jours_restants", "a_commander", "etat",
        ]].copy()
        affichage["ventes_par_jour"] = affichage["ventes_par_jour"].round(2)
        affichage["jours_restants"] = affichage["jours_restants"].replace(
            float("inf"), None
        ).round(1)
        st.dataframe(
            affichage.rename(columns={
                "nom_produit": "Produit", "categorie": "Catégorie",
                "stock_actuel": "En stock", "ventes_par_jour": "Vendu / jour",
                "jours_restants": "Jours restants", "a_commander": "À commander (30 j)",
                "etat": "État",
            }),
            width="stretch", hide_index=True,
        )

    st.subheader("Capital immobilisé en rayon")
    stock["valeur_stock"] = stock["stock_actuel"] * stock["prix_achat"]
    par_cat = stock.groupby("categorie")["valeur_stock"].sum().reset_index()
    fig_cat = px.bar(par_cat, x="categorie", y="valeur_stock",
                     color_discrete_sequence=[ENCRE])
    fig_cat.update_layout(height=300, margin=dict(t=10, b=0, l=0, r=0),
                          xaxis_title="", yaxis_title="FCFA",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_cat, width="stretch")
    st.caption(f"Valeur totale du stock : {fcfa(stock['valeur_stock'].sum())}")

# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------

with onglet_clients:
    profil = ventes.groupby("client_id").agg(
        dernier_achat=("date_vente", "max"),
        nombre_achats=("vente_id", "count"),
        total_depense=("montant_total", "sum"),
        du=("reste_a_payer", "sum"),
    ).reset_index().merge(clients, on="client_id", how="left")

    profil["jours_absence"] = (date_max - profil["dernier_achat"]).dt.days
    profil["panier_moyen"] = profil["total_depense"] / profil["nombre_achats"]

    seuil = st.slider("Un client est considéré dormant après (jours sans achat)",
                      15, 180, 60, step=15)
    dormants = profil[profil["jours_absence"] >= seuil].sort_values(
        "total_depense", ascending=False
    )

    b1, b2, b3 = st.columns(3)
    b1.metric("Clients actifs", int((profil["jours_absence"] < seuil).sum()))
    b2.metric("Clients dormants", len(dormants))
    b3.metric("CA en sommeil", fcfa(dormants["total_depense"].sum()))

    gauche, droite = st.columns(2)

    with gauche:
        st.subheader("Meilleurs clients")
        st.dataframe(
            profil.nlargest(10, "total_depense")[[
                "nom_client", "quartier", "nombre_achats", "total_depense"
            ]].rename(columns={
                "nom_client": "Client", "quartier": "Quartier",
                "nombre_achats": "Achats", "total_depense": "Total dépensé",
            }),
            width="stretch", hide_index=True,
        )

    with droite:
        st.subheader("À rappeler en priorité")
        st.caption("Bons clients qui ne sont plus revenus depuis longtemps.")
        st.dataframe(
            dormants.head(10)[[
                "nom_client", "quartier", "jours_absence", "total_depense"
            ]].rename(columns={
                "nom_client": "Client", "quartier": "Quartier",
                "jours_absence": "Jours d'absence", "total_depense": "Total dépensé",
            }),
            width="stretch", hide_index=True,
        )

    st.subheader("Chiffre d'affaires par quartier")
    par_quartier = (
        ventes.groupby("quartier")["montant_total"].sum()
        .sort_values(ascending=False).reset_index()
    )
    fig_q = px.bar(par_quartier, x="quartier", y="montant_total",
                   color_discrete_sequence=[VERT])
    fig_q.update_layout(height=300, margin=dict(t=10, b=0, l=0, r=0),
                        xaxis_title="", yaxis_title="FCFA",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_q, width="stretch")

# --------------------------------------------------------------------------
# Impayés
# --------------------------------------------------------------------------

with onglet_impayes:
    ardoise = ventes[ventes["reste_a_payer"] > 0].copy()
    ardoise["anciennete"] = (date_max - ardoise["date_vente"]).dt.days

    def tranche(jours_):
        if jours_ <= 30:
            return "0 à 30 jours"
        if jours_ <= 60:
            return "31 à 60 jours"
        if jours_ <= 90:
            return "61 à 90 jours"
        return "Plus de 90 jours"

    ardoise["tranche"] = ardoise["anciennete"].apply(tranche)

    d1, d2, d3 = st.columns(3)
    d1.metric("Total à encaisser", fcfa(ardoise["reste_a_payer"].sum()))
    d2.metric("Clients concernés", ardoise["client_id"].nunique())
    d3.metric("Créances de plus de 90 jours",
              fcfa(ardoise.loc[ardoise["anciennete"] > 90, "reste_a_payer"].sum()))

    ordre = ["0 à 30 jours", "31 à 60 jours", "61 à 90 jours", "Plus de 90 jours"]
    par_tranche = (
        ardoise.groupby("tranche")["reste_a_payer"].sum()
        .reindex(ordre).fillna(0).reset_index()
    )
    fig_age = px.bar(par_tranche, x="tranche", y="reste_a_payer",
                     color="tranche",
                     color_discrete_sequence=[VERT, "#6FA98F", AMBRE, BRIQUE])
    fig_age.update_layout(height=300, showlegend=False,
                          margin=dict(t=10, b=0, l=0, r=0),
                          xaxis_title="", yaxis_title="FCFA",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.subheader("Ancienneté des créances")
    st.plotly_chart(fig_age, width="stretch")

    st.subheader("Qui doit quoi")
    par_client = (
        ardoise.groupby(["client_id", "nom_client", "quartier"])
        .agg(du=("reste_a_payer", "sum"),
             plus_ancienne=("anciennete", "max"),
             factures=("vente_id", "count"))
        .reset_index().sort_values("du", ascending=False)
    )
    st.dataframe(
        par_client[["nom_client", "quartier", "factures", "plus_ancienne", "du"]]
        .rename(columns={
            "nom_client": "Client", "quartier": "Quartier",
            "factures": "Ventes non soldées",
            "plus_ancienne": "Créance la plus ancienne (jours)", "du": "Reste dû",
        }),
        width="stretch", hide_index=True,
    )

    st.download_button(
        "Exporter la liste des impayés (CSV)",
        par_client.to_csv(index=False).encode("utf-8"),
        file_name="impayes.csv",
        mime="text/csv",
    )
