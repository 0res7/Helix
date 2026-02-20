# Helix

Automated **Sarvam attempts** report: fetches analytics from the Sarvam API, writes a date-stamped Excel file, and optionally uploads it to a Box folder. Runs on a schedule via GitHub Actions (no need for your machine to be on).

## What it does

- Calls the [Sarvam Analytics API](https://apps.sarvam.ai) to fetch attempts data.
- Builds an Excel report named `sarvam_attempts_report_DDMonYYYY.xlsx` (e.g. `sarvam_attempts_report_19Feb2026.xlsx`).
- Saves the file locally and/or uploads it to a Box folder (via Box API, using JWT or a developer token).
- **GitHub Actions**: runs daily at 10:30 AM IST and can be triggered manually; uploads the report as an artifact and, when configured, to Box.

## Repository structure

```
.
├── .github/workflows/
│   └── sarvam-attempts-report.yml   # Scheduled + manual workflow
├── docs/
│   ├── AUTOMATION_SETUP.md          # Turn on automation (environment, secrets, schedule)
│   ├── BOX_SETUP.md                 # Box folder, Developer Token, JWT, OAuth options
│   └── BOX_OAUTH_AUTOMATION.md      # OAuth refresh token setup for scheduled Box uploads
├── sarvam_attempts_report.py        # Main script
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Setup

### 1. GitHub environment and secrets

Workflow uses the **report** environment. Create it and add secrets there:

**Settings → Environments → New environment** → name: `report` → configure.

Under **Environment secrets** for `report`, add:

**Sarvam (required)**  
- `SARVAM_ORG_ID`  
- `SARVAM_WORKSPACE_ID`  
- `SARVAM_APP_ID`  
- `SARVAM_API_KEY`  

**Box (optional; for upload)**  
- `BOX_FOLDER_ID` — folder ID from the Box folder URL (e.g. `.../folder/366969394973` → `366969394973`).  
- **Automated (personal Box):** OAuth refresh token — see **[docs/BOX_OAUTH_AUTOMATION.md](docs/BOX_OAUTH_AUTOMATION.md)** for detailed steps; needs `BOX_REFRESH_TOKEN`, `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET` in **report** env and **GH_PAT** (repo secret). When using OAuth refresh, do **not** set `BOX_ACCESS_TOKEN` in the report environment (remove it if present).  
- **Manual / quick test:** Developer Token — `BOX_ACCESS_TOKEN` (expires in 1 hour).  
- **Enterprise Box:** JWT — `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, `BOX_KEY_ID`, `BOX_PRIVATE_KEY`, `BOX_ENTERPRISE_ID`, etc. See [docs/BOX_SETUP.md](docs/BOX_SETUP.md).

### 2. Run the workflow

- **Manual run**: **Actions** tab → **Sarvam Attempts Report** → **Run workflow** → **Run workflow**.
- **Schedule**: workflow runs daily at 10:30 AM IST (`cron: "0 5 * * *"` UTC).

After a run, the Excel file is in the **Artifacts** of that run (and in your Box folder if Box secrets are set).

## Run locally

```bash
# Clone and enter repo
git clone https://github.com/0res7/Helix.git && cd Helix

# Optional: create venv and install deps
python3 -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set env vars (Sarvam required; Box optional)
export SARVAM_ORG_ID="..."
export SARVAM_WORKSPACE_ID="..."
export SARVAM_APP_ID="..."
export SARVAM_API_KEY="..."
# Optional: OUTPUT_DIR, BOX_* (see docs/BOX_SETUP.md)

# Generate report
python sarvam_attempts_report.py
```

Output goes to `OUTPUT_DIR` (default: `~/Library/CloudStorage/Box-Box` on macOS). If Box env vars are set, the script also uploads the file to the Box folder.

## Requirements

- Python 3.9+
- Dependencies: `pandas`, `requests`, `openpyxl`, `pyjwt[crypto]` (see `requirements.txt`)

## Docs

- **[Turn on automation (detailed)](docs/AUTOMATION_SETUP.md)** — Step-by-step: environment, secrets, first run, schedule.
- **[Box OAuth automation](docs/BOX_OAUTH_AUTOMATION.md)** — One-time OAuth setup so scheduled runs can upload to Box; includes troubleshooting (e.g. upload 401).
- [Box folder and JWT setup](docs/BOX_SETUP.md) — `BOX_FOLDER_ID`, Developer Token, OAuth refresh, and JWT app configuration.
