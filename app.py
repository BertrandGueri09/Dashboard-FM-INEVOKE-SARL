
import os
import base64
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


st.set_page_config(
    page_title="INEVOKE — Dashboard Facility Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

BLUE = "#2196F3"
ORANGE = "#F9A825"
NAVY = "#0D47A1"
LIGHT = "#E3F2FD"
GREEN = "#2E7D32"
RED = "#C62828"
DARK = "#1A1A2E"

PALETTE = [BLUE, ORANGE, "#26C6DA", "#66BB6A", "#AB47BC", "#EF5350", "#26A69A", "#FFA726"]
KOBO_FORM_LINK = "https://ee.kobotoolbox.org/x/pScq0zr4"

try:
    KOBO_API_URL = st.secrets.get("KOBO_API_URL", "https://kf.kobotoolbox.org")
    KOBO_ASSET_UID = st.secrets.get("KOBO_ASSET_UID", "pScq0zr4")
    KOBO_API_TOKEN = st.secrets.get("KOBO_API_TOKEN", "")
except Exception:
    KOBO_API_URL = "https://kf.kobotoolbox.org"
    KOBO_ASSET_UID = "pScq0zr4"
    KOBO_API_TOKEN = ""


st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {{font-family:'Barlow',sans-serif;}}

.main-header {{
    background:linear-gradient(135deg,{NAVY} 0%,{BLUE} 100%);
    padding:22px 28px;border-radius:18px;margin-bottom:1.4rem;
    display:flex;align-items:center;gap:20px;
    box-shadow:0 8px 28px rgba(33,150,243,.25);
}}
.main-header h1 {{color:white;font-size:28px;font-weight:800;margin:0;}}
.main-header p {{color:rgba(255,255,255,.88);font-size:14px;margin:5px 0 0;}}

.kpi-card {{
    background:white;border-radius:15px;padding:18px 16px;
    border-top:5px solid {BLUE};box-shadow:0 3px 15px rgba(0,0,0,.08);
    text-align:center;min-height:112px;
}}
.kpi-card.orange {{border-top-color:{ORANGE};}}
.kpi-card.green {{border-top-color:{GREEN};}}
.kpi-card.red {{border-top-color:{RED};}}
.kpi-card.navy {{border-top-color:{NAVY};}}

.kpi-label {{
    font-size:11px;color:#666;text-transform:uppercase;
    letter-spacing:.08em;font-weight:700;
}}
.kpi-value {{font-size:27px;color:{NAVY};font-weight:800;margin-top:8px;}}

.section-title {{
    font-size:17px;font-weight:800;color:{NAVY};
    border-left:5px solid {ORANGE};padding-left:12px;margin:1.1rem 0 .8rem;
}}
.alert-box {{
    background:{LIGHT};border-left:5px solid {BLUE};border-radius:12px;
    padding:14px 18px;color:{NAVY};font-size:14px;margin-bottom:1rem;
}}
.empty-box {{
    background:white;border:2px dashed {BLUE};border-radius:16px;
    padding:30px;color:{NAVY};text-align:center;margin-top:1rem;
}}
section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,{NAVY} 0%,#1565C0 100%);
}}
section[data-testid="stSidebar"] * {{color:white !important;}}
.stDownloadButton>button {{
    background:{ORANGE};color:{DARK};border:none;border-radius:8px;font-weight:800;
}}
.stButton>button {{
    background:{BLUE};color:white;border:none;border-radius:8px;font-weight:800;
}}
</style>
""",
    unsafe_allow_html=True,
)


def image_to_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def empty_dataframe():
    cols = [
        "id_contrat", "client", "type_site", "type_service",
        "date_visite", "date_debut", "responsable_operationnel",
        "frequence_intervention", "nb_interventions",
        "statut_service", "niveau_urgence", "revenu_genere",
        "modalite_paiement", "satisfaction_client",
        "commercial", "technicien", "ville", "observations",
        "latitude", "longitude", "date_soumission"
    ]
    return pd.DataFrame(columns=cols)


def normalize_yes_no(value):
    value = str(value).strip().lower()
    if value in ["oui", "yes", "true", "1", "disponible", "ok"]:
        return "Oui"
    if value in ["non", "no", "false", "0", "indisponible"]:
        return "Non"
    if value in ["nan", "none", ""]:
        return "Non renseigné"
    return str(value).strip()


def normalize_columns(df):
    if df is None or len(df) == 0:
        return empty_dataframe()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    mapping = {
        "ID du contrat / Intervention": "id_contrat",
        "ID contrat": "id_contrat",
        "id_contrat": "id_contrat",
        "Client": "client",
        "client": "client",
        "Type de site": "type_site",
        "type_site": "type_site",
        "Type de service": "type_service",
        "Service FM": "type_service",
        "type_service": "type_service",
        "Date de visite": "date_visite",
        "Date de visite de chantier": "date_visite",
        "date_visite": "date_visite",
        "Date de début": "date_debut",
        "Date de debut": "date_debut",
        "Date de début de chantier": "date_debut",
        "date_debut": "date_debut",
        "Responsable opérationnel": "responsable_operationnel",
        "Responsable operationnel": "responsable_operationnel",
        "Responsable technique en charge du chantier": "responsable_operationnel",
        "responsable_operationnel": "responsable_operationnel",
        "Fréquence intervention": "frequence_intervention",
        "Frequence intervention": "frequence_intervention",
        "frequence_intervention": "frequence_intervention",
        "Nombre d’interventions": "nb_interventions",
        "Nombre d'interventions": "nb_interventions",
        "nb_interventions": "nb_interventions",
        "Statut intervention": "statut_service",
        "Statut service": "statut_service",
        "statut_service": "statut_service",
        "Niveau urgence": "niveau_urgence",
        "Niveau d’urgence": "niveau_urgence",
        "Niveau d'urgence": "niveau_urgence",
        "niveau_urgence": "niveau_urgence",
        "Revenu généré (FCFA)": "revenu_genere",
        "Revenu genere (FCFA)": "revenu_genere",
        "revenu_genere": "revenu_genere",
        "Modalité de paiement": "modalite_paiement",
        "Modalite de paiement": "modalite_paiement",
        "modalite_paiement": "modalite_paiement",
        "Satisfaction client": "satisfaction_client",
        "satisfaction_client": "satisfaction_client",
        "Commercial en charge": "commercial",
        "commercial": "commercial",
        "Technicien": "technicien",
        "technicien": "technicien",
        "Ville": "ville",
        "ville": "ville",
        "Observations": "observations",
        "observations": "observations",
        "_submission_time": "date_soumission",
        "_geolocation": "geolocation",
    }

    df = df.rename(columns={c: mapping.get(c, c) for c in df.columns})

    for col in empty_dataframe().columns:
        if col not in df.columns:
            df[col] = np.nan

    if "geolocation" in df.columns:
        def get_lat(x):
            if isinstance(x, list) and len(x) >= 2:
                return x[0]
            return np.nan
        def get_lon(x):
            if isinstance(x, list) and len(x) >= 2:
                return x[1]
            return np.nan
        df["latitude"] = df["geolocation"].apply(get_lat)
        df["longitude"] = df["geolocation"].apply(get_lon)

    for col in ["date_visite", "date_debut", "date_soumission"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["revenu_genere"] = pd.to_numeric(df["revenu_genere"], errors="coerce").fillna(0)
    df["nb_interventions"] = pd.to_numeric(df["nb_interventions"], errors="coerce").fillna(0)

    text_cols = [
        "id_contrat", "client", "type_site", "type_service",
        "responsable_operationnel", "frequence_intervention",
        "statut_service", "niveau_urgence", "modalite_paiement",
        "satisfaction_client", "commercial", "technicien", "ville", "observations",
    ]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["annee"] = df["date_debut"].dt.year
    df["mois"] = df["date_debut"].dt.month
    df["mois_label"] = df["date_debut"].dt.strftime("%Y-%m")
    df["delai_visite_debut"] = (df["date_debut"] - df["date_visite"]).dt.days

    return df


@st.cache_data(ttl=60, show_spinner=False)
def fetch_kobo_data(api_url, asset_uid, token):
    if not asset_uid or not token:
        return empty_dataframe()

    url = f"{api_url.rstrip('/')}/api/v2/assets/{asset_uid}/data.json"
    headers = {"Authorization": f"Token {token}"}

    rows = []
    next_url = url

    try:
        while next_url:
            response = requests.get(next_url, headers=headers, timeout=35)
            response.raise_for_status()
            payload = response.json()
            rows.extend(payload.get("results", []))
            next_url = payload.get("next")
            if next_url and next_url.startswith("/"):
                next_url = api_url.rstrip("/") + next_url

        return normalize_columns(pd.DataFrame(rows))

    except Exception as e:
        st.error(f"Erreur de connexion à Kobo : {e}")
        return empty_dataframe()


def format_fcfa(value):
    try:
        value = float(value)
    except Exception:
        value = 0
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.1f} M"
    return f"{value:,.0f}"


def kpi_card(label, value, color_class="blue"):
    st.markdown(
        f"""
        <div class="kpi-card {color_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def value_counts_df(df, col, count_name="Nombre"):
    if len(df) == 0 or col not in df.columns:
        return pd.DataFrame({col: [], count_name: []})
    temp = df[col].replace("", "Non renseigné").value_counts().reset_index()
    temp.columns = [col, count_name]
    return temp


with st.sidebar:
    st.markdown("### 🔄 Actualisation automatique")
    refresh_seconds = st.selectbox(
        "Fréquence",
        [30, 60, 120, 300],
        index=1,
        format_func=lambda x: f"Toutes les {x} secondes",
    )

if st_autorefresh is not None:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh_fm")


logo_b64 = image_to_base64("assets/logo_inevoke.jpeg")
logo_html = (
    f'<img src="data:image/jpeg;base64,{logo_b64}" style="height:72px;background:white;border-radius:12px;padding:6px;">'
    if logo_b64 else "🏢"
)

st.markdown(
    f"""
<div class="main-header">
    <div>{logo_html}</div>
    <div>
        <h1>Dashboard Marché — Facility Management</h1>
        <p>INEVOKE SARL · Suivi des contrats, interventions, revenus, urgences, équipes et satisfaction client</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔗 Formulaire Kobo")
    st.markdown(f"[Ouvrir le formulaire]({KOBO_FORM_LINK})")
    st.caption("Le dashboard lit les données via API Kobo.")
    if st.button("Forcer l’actualisation maintenant"):
        st.cache_data.clear()
        st.rerun()

df_all = fetch_kobo_data(KOBO_API_URL, KOBO_ASSET_UID, KOBO_API_TOKEN)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Filtres")

    df = df_all.copy()

    if len(df_all) > 0 and df_all["date_debut"].notna().any():
        date_min = df_all["date_debut"].min().date()
        date_max = df_all["date_debut"].max().date()
        date_range = st.date_input("Période service", value=(date_min, date_max), min_value=date_min, max_value=date_max)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["date_debut"].dt.date >= start_date) & (df["date_debut"].dt.date <= end_date)]
    else:
        st.caption("Aucune date de service disponible.")

    statuts = ["Tous"] + sorted([x for x in df_all["statut_service"].dropna().unique().tolist() if x])
    statut_sel = st.selectbox("Statut service", statuts)
    if statut_sel != "Tous":
        df = df[df["statut_service"] == statut_sel]

    sites = ["Tous"] + sorted([x for x in df_all["type_site"].dropna().unique().tolist() if x])
    site_sel = st.selectbox("Type de site", sites)
    if site_sel != "Tous":
        df = df[df["type_site"] == site_sel]

    services = ["Tous"] + sorted([x for x in df_all["type_service"].dropna().unique().tolist() if x])
    service_sel = st.selectbox("Type de service", services)
    if service_sel != "Tous":
        df = df[df["type_service"] == service_sel]

    urgences = ["Tous"] + sorted([x for x in df_all["niveau_urgence"].dropna().unique().tolist() if x])
    urgence_sel = st.selectbox("Niveau urgence", urgences)
    if urgence_sel != "Tous":
        df = df[df["niveau_urgence"] == urgence_sel]

    commerciaux = ["Tous"] + sorted([x for x in df_all["commercial"].dropna().unique().tolist() if x])
    commercial_sel = st.selectbox("Commercial", commerciaux)
    if commercial_sel != "Tous":
        df = df[df["commercial"] == commercial_sel]


if len(df) == 0:
    nb_contrats = nb_clients = nb_interventions_total = services_actifs = sites_suivis = villes = 0
    revenu_total = revenu_moyen = delai_moyen = satisfaction_count = 0
    urgences_hautes = 0
else:
    statut_lower = df["statut_service"].str.lower()
    urgence_lower = df["niveau_urgence"].str.lower()
    nb_contrats = len(df)
    nb_clients = df["client"].replace("", np.nan).nunique()
    nb_interventions_total = int(df["nb_interventions"].sum()) if df["nb_interventions"].sum() > 0 else len(df)
    revenu_total = df["revenu_genere"].sum()
    revenu_moyen = df["revenu_genere"].mean()
    delai_moyen = df["delai_visite_debut"].dropna().mean() if df["delai_visite_debut"].notna().any() else 0
    services_actifs = statut_lower.str.contains("cours|actif|execution|exécution|ouvert", regex=True, na=False).sum()
    sites_suivis = df["type_site"].replace("", np.nan).nunique()
    villes = df["ville"].replace("", np.nan).nunique()
    urgences_hautes = urgence_lower.str.contains("haut|haute|urgent|critique|élev|elev", regex=True, na=False).sum()

st.markdown(
    f"""
<div class="alert-box">
    <b>Mode automatique Kobo :</b> actualisation toutes les {refresh_seconds} secondes.
    <br><b>Dernière actualisation :</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    <br><b>Soumissions reçues :</b> {len(df_all)}
</div>
""",
    unsafe_allow_html=True,
)

if not KOBO_API_TOKEN:
    st.warning("Connexion Kobo non configurée. Ajoute KOBO_ASSET_UID et KOBO_API_TOKEN dans .streamlit/secrets.toml ou dans les Secrets Streamlit Cloud.")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Contrats / dossiers", nb_contrats, "blue")
with c2: kpi_card("Clients uniques", nb_clients, "navy")
with c3: kpi_card("Interventions", nb_interventions_total, "orange")
with c4: kpi_card("Revenu total", f"{format_fcfa(revenu_total)} FCFA", "green")
with c5: kpi_card("Revenu moyen", f"{format_fcfa(revenu_moyen)} FCFA", "blue")
with c6: kpi_card("Urgences hautes", urgences_hautes, "red")

st.markdown("<br>", unsafe_allow_html=True)

c7, c8, c9, c10 = st.columns(4)
with c7: kpi_card("Services actifs", services_actifs, "green")
with c8: kpi_card("Sites suivis", sites_suivis, "navy")
with c9: kpi_card("Villes couvertes", villes, "blue")
with c10: kpi_card("Délai moyen", f"{delai_moyen:.1f} j", "orange")

if len(df) == 0:
    st.markdown(
        """
<div class="empty-box">
    <h3>Aucune donnée Facility Management pour le moment</h3>
    <p>Le dashboard est initialisé à zéro. Dès que le formulaire Kobo est soumis et que l’API est configurée,
    les indicateurs, graphiques et tableaux se mettront à jour automatiquement.</p>
</div>
""",
        unsafe_allow_html=True,
    )


tabs = st.tabs([
    "Vue d’ensemble",
    "Services FM",
    "Revenus & paiements",
    "Urgences & statut",
    "Équipe & performance",
    "Carte Côte d’Ivoire",
    "Données",
])


with tabs[0]:
    st.markdown("<div class='section-title'>Vue d’ensemble Facility Management</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 1])

    with col1:
        if len(df) > 0 and df["mois_label"].notna().any():
            evo = df.dropna(subset=["date_debut"]).groupby("mois_label").agg(
                dossiers=("id_contrat", "count"),
                interventions=("nb_interventions", "sum"),
                revenu=("revenu_genere", "sum"),
            ).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=evo["mois_label"], y=evo["dossiers"], name="Dossiers", marker_color=BLUE))
            fig.add_trace(go.Scatter(
                x=evo["mois_label"], y=evo["revenu"] / 1_000_000,
                name="Revenu (M FCFA)", mode="lines+markers",
                line=dict(color=ORANGE, width=3), yaxis="y2",
            ))
            fig.update_layout(
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h"),
                yaxis=dict(title="Dossiers"),
                yaxis2=dict(title="M FCFA", overlaying="y", side="right", showgrid=False),
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune évolution à afficher pour le moment.")

    with col2:
        if len(df) > 0:
            stat = value_counts_df(df, "statut_service", "Nombre")
            fig = px.pie(stat, values="Nombre", names="statut_service", hole=.45, color_discrete_sequence=PALETTE)
            fig.update_layout(height=380, paper_bgcolor="white", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun statut à afficher.")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Dossiers par type de site</div>", unsafe_allow_html=True)
        if len(df) > 0:
            site_df = value_counts_df(df, "type_site", "Dossiers")
            fig = px.bar(site_df, x="Dossiers", y="type_site", orientation="h", color_discrete_sequence=[BLUE], text="Dossiers")
            fig.update_layout(height=330, plot_bgcolor="white", paper_bgcolor="white", yaxis_title="", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun site à afficher.")

    with col4:
        st.markdown("<div class='section-title'>Dossiers par type de service FM</div>", unsafe_allow_html=True)
        if len(df) > 0:
            service_df = value_counts_df(df, "type_service", "Dossiers")
            fig = px.bar(service_df, x="Dossiers", y="type_service", orientation="h", color_discrete_sequence=[ORANGE], text="Dossiers")
            fig.update_layout(height=330, plot_bgcolor="white", paper_bgcolor="white", yaxis_title="", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun service à afficher.")


with tabs[1]:
    st.markdown("<div class='section-title'>Analyse des services Facility Management</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if len(df) > 0:
            freq = value_counts_df(df, "frequence_intervention", "Nombre")
            fig = px.pie(freq, values="Nombre", names="frequence_intervention", hole=.45, color_discrete_sequence=PALETTE)
            fig.update_layout(title="Fréquence des interventions", height=350, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune fréquence à afficher.")

    with col2:
        if len(df) > 0:
            interventions = df.groupby("type_service").agg(
                interventions=("nb_interventions", "sum"),
                dossiers=("id_contrat", "count"),
            ).reset_index().sort_values("interventions", ascending=False)
            fig = px.bar(interventions, x="type_service", y="interventions", color_discrete_sequence=[BLUE], text="interventions")
            fig.update_layout(title="Interventions par service", height=350, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Interventions")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune intervention à afficher.")

    st.markdown("<div class='section-title'>Tableau services FM</div>", unsafe_allow_html=True)
    if len(df) > 0:
        service_table = df.groupby("type_service").agg(
            dossiers=("id_contrat", "count"),
            interventions=("nb_interventions", "sum"),
            revenu=("revenu_genere", "sum"),
            revenu_moyen=("revenu_genere", "mean"),
        ).reset_index().sort_values("revenu", ascending=False)
        st.dataframe(service_table, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun service FM enregistré.")


with tabs[2]:
    st.markdown("<div class='section-title'>Revenus & modalités de paiement</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if len(df) > 0:
            rev_site = df.groupby("type_site").agg(revenu=("revenu_genere", "sum"), dossiers=("id_contrat", "count")).reset_index().sort_values("revenu")
            fig = px.bar(
                rev_site, x="revenu", y="type_site", orientation="h",
                color_discrete_sequence=[GREEN],
                text=rev_site["revenu"].apply(lambda x: f"{x/1e6:.1f}M"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="FCFA", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun revenu par site.")

    with col2:
        if len(df) > 0:
            paiement = value_counts_df(df, "modalite_paiement", "Nombre")
            fig = px.pie(paiement, values="Nombre", names="modalite_paiement", hole=.45, color_discrete_sequence=PALETTE)
            fig.update_layout(height=370, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune modalité de paiement.")

    st.markdown("<div class='section-title'>Revenu par type de service FM</div>", unsafe_allow_html=True)
    if len(df) > 0:
        rev_service = df.groupby("type_service").agg(
            revenu=("revenu_genere", "sum"),
            revenu_moyen=("revenu_genere", "mean"),
            dossiers=("id_contrat", "count"),
            interventions=("nb_interventions", "sum"),
        ).reset_index().sort_values("revenu", ascending=False)
        st.dataframe(rev_service, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun revenu à afficher.")


with tabs[3]:
    st.markdown("<div class='section-title'>Urgences & statut opérationnel</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if len(df) > 0:
            urgence = value_counts_df(df, "niveau_urgence", "Nombre")
            fig = px.pie(urgence, values="Nombre", names="niveau_urgence", hole=.45, color_discrete_sequence=[RED, ORANGE, GREEN, BLUE])
            fig.update_layout(title="Répartition des urgences", height=360, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune urgence à afficher.")

    with col2:
        if len(df) > 0:
            matrix = df.pivot_table(index="niveau_urgence", columns="statut_service", values="id_contrat", aggfunc="count", fill_value=0)
            fig = px.imshow(matrix, text_auto=True, aspect="auto", color_continuous_scale=[[0, "white"], [.5, LIGHT], [1, BLUE]])
            fig.update_layout(title="Matrice urgence × statut", height=360, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune matrice à afficher.")

    st.markdown("<div class='section-title'>Dossiers urgents à suivre</div>", unsafe_allow_html=True)
    if len(df) > 0:
        urgent_df = df[df["niveau_urgence"].str.lower().str.contains("haut|haute|urgent|critique|élev|elev", regex=True, na=False)]
        st.dataframe(
            urgent_df[["id_contrat", "client", "type_site", "type_service", "statut_service", "niveau_urgence", "responsable_operationnel", "technicien", "ville", "observations"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucun dossier urgent.")


with tabs[4]:
    st.markdown("<div class='section-title'>Performance équipe & satisfaction</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if len(df) > 0:
            ops = df.groupby("responsable_operationnel").agg(
                dossiers=("id_contrat", "count"),
                interventions=("nb_interventions", "sum"),
                revenu=("revenu_genere", "sum"),
            ).reset_index().sort_values("dossiers", ascending=False)
            st.dataframe(ops, use_container_width=True, hide_index=True)
            fig = px.bar(ops, x="responsable_operationnel", y="dossiers", color_discrete_sequence=[BLUE], text="dossiers")
            fig.update_layout(title="Dossiers par responsable opérationnel", height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Dossiers")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune performance opérationnelle.")

    with col2:
        if len(df) > 0:
            com = df.groupby("commercial").agg(
                dossiers=("id_contrat", "count"),
                revenu=("revenu_genere", "sum"),
                revenu_moyen=("revenu_genere", "mean"),
            ).reset_index().sort_values("revenu", ascending=False)
            st.dataframe(com, use_container_width=True, hide_index=True)
            fig = px.bar(com, x="commercial", y="revenu", color_discrete_sequence=[ORANGE], text=com["revenu"].apply(lambda x: f"{x/1e6:.1f}M"))
            fig.update_traces(textposition="outside")
            fig.update_layout(title="Revenu par commercial", height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="FCFA")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune performance commerciale.")

    st.markdown("<div class='section-title'>Satisfaction client</div>", unsafe_allow_html=True)
    if len(df) > 0:
        sat = value_counts_df(df, "satisfaction_client", "Nombre")
        fig = px.bar(sat, x="satisfaction_client", y="Nombre", color_discrete_sequence=[GREEN], text="Nombre")
        fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Nombre")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune satisfaction client enregistrée.")


with tabs[5]:
    st.markdown("<div class='section-title'>Carte Côte d’Ivoire — Facility Management</div>", unsafe_allow_html=True)

    coords = pd.DataFrame([
        {"ville": "Abidjan", "lat": 5.3599517, "lon": -4.0082563},
        {"ville": "Bouaké", "lat": 7.6906, "lon": -5.0391},
        {"ville": "Yamoussoukro", "lat": 6.8276, "lon": -5.2893},
        {"ville": "San-Pédro", "lat": 4.7485, "lon": -6.6363},
        {"ville": "Daloa", "lat": 6.8774, "lon": -6.4502},
        {"ville": "Korhogo", "lat": 9.4578, "lon": -5.6296},
        {"ville": "Divo", "lat": 5.8390, "lon": -5.3570},
        {"ville": "Gagnoa", "lat": 6.1319, "lon": -5.9506},
        {"ville": "Man", "lat": 7.4125, "lon": -7.5538},
        {"ville": "Abengourou", "lat": 6.7297, "lon": -3.4964},
        {"ville": "Bondoukou", "lat": 8.0402, "lon": -2.8000},
        {"ville": "Odienné", "lat": 9.5104, "lon": -7.5692},
        {"ville": "Séguéla", "lat": 7.9611, "lon": -6.6731},
    ])

    if len(df) > 0:
        geo_df = df.copy()
        geo_df["latitude"] = pd.to_numeric(geo_df["latitude"], errors="coerce")
        geo_df["longitude"] = pd.to_numeric(geo_df["longitude"], errors="coerce")
        geo_df = geo_df.dropna(subset=["latitude", "longitude"])

        fig = None

        if len(geo_df) > 0:
            map_df = geo_df.rename(columns={"latitude": "lat", "longitude": "lon"})
            fig = px.scatter_mapbox(
                map_df, lat="lat", lon="lon", size="revenu_genere",
                color="niveau_urgence", hover_name="client",
                hover_data=["type_site", "type_service", "statut_service", "revenu_genere"],
                zoom=5.8, height=620, color_discrete_sequence=PALETTE, size_max=42,
            )
        else:
            ville_df = df.groupby("ville").agg(
                dossiers=("id_contrat", "count"),
                interventions=("nb_interventions", "sum"),
                revenu=("revenu_genere", "sum"),
            ).reset_index()
            ville_df["ville_clean"] = ville_df["ville"].str.strip().str.lower()
            coords["ville_clean"] = coords["ville"].str.strip().str.lower()
            map_df = ville_df.merge(coords[["ville_clean", "lat", "lon"]], on="ville_clean", how="left").dropna(subset=["lat", "lon"])

            if len(map_df) > 0:
                fig = px.scatter_mapbox(
                    map_df, lat="lat", lon="lon", size="dossiers", color="revenu",
                    hover_name="ville",
                    hover_data={"dossiers": True, "interventions": True, "revenu": ":,.0f", "lat": False, "lon": False},
                    zoom=5.7, height=620,
                    color_continuous_scale=[[0, LIGHT], [.5, ORANGE], [1, BLUE]],
                    size_max=46,
                )

        if fig is not None:
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox_center={"lat": 7.54, "lon": -5.55},
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune ville ou coordonnée reconnue pour afficher la carte.")
    else:
        st.info("La carte sera affichée dès qu’il y aura des données.")

    st.markdown("<div class='section-title'>Résumé géographique</div>", unsafe_allow_html=True)
    if len(df) > 0:
        geo_table = df.groupby("ville").agg(
            dossiers=("id_contrat", "count"),
            interventions=("nb_interventions", "sum"),
            revenu=("revenu_genere", "sum"),
        ).reset_index().sort_values("revenu", ascending=False)
        st.dataframe(geo_table, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun résumé géographique.")


with tabs[6]:
    st.markdown("<div class='section-title'>Base des données Facility Management</div>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Télécharger les données filtrées en CSV",
        data=csv,
        file_name="donnees_facility_management_inevoke.csv",
        mime="text/csv",
    )


st.markdown("---")
st.caption("INEVOKE SARL — Dashboard Facility Management ")
