# Dashboard Facility Management — INEVOKE SARL

Dashboard Streamlit pour le formulaire Kobo :

https://ee.kobotoolbox.org/x/pScq0zr4

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration Kobo

Ouvre :

```text
.streamlit/secrets.toml
```

Puis renseigne :

```toml
KOBO_API_URL = "https://kf.kobotoolbox.org"
KOBO_ASSET_UID = "pScq0zr4"
KOBO_API_TOKEN = "COLLE_TON_TOKEN_ICI"
```

## Récupérer ton token Kobo

Va ici :

https://kf.kobotoolbox.org/token

## Sur Streamlit Cloud

Dans Manage app > Settings > Secrets, colle :

```toml
KOBO_API_URL = "https://kf.kobotoolbox.org"
KOBO_ASSET_UID = "pScq0zr4"
KOBO_API_TOKEN = "TON_TOKEN"
```

Puis clique sur Reboot.
