import os
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests
import pandas as pd

# ==========================================
# 1. CONFIGURATION - Update these values
# ==========================================
ORG_ID = os.getenv("SARVAM_ORG_ID", "")
WORKSPACE_ID = os.getenv("SARVAM_WORKSPACE_ID", "")
APP_ID = os.getenv("SARVAM_APP_ID", "")
API_KEY = os.getenv("SARVAM_API_KEY", "")

# Local output path. For GitHub Actions, set OUTPUT_DIR to "./reports".
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "~/Library/CloudStorage/Box-Box")
REQUEST_TIMEOUT_SECONDS = 60

# Optional Box API upload support (for cloud runs).
# BOX_FOLDER_ID: from the folder URL, e.g. .../folder/366400499122 → 366400499122
# BOX_ACCESS_TOKEN: use a Developer Token (short-lived) OR leave unset and use JWT vars below.
BOX_ACCESS_TOKEN = os.getenv("BOX_ACCESS_TOKEN", "")
BOX_FOLDER_ID = os.getenv("BOX_FOLDER_ID", "")

# Optional: JWT app credentials (from Box Developer Console config). Used to get access token each run.
BOX_CLIENT_ID = os.getenv("BOX_CLIENT_ID", "")
BOX_CLIENT_SECRET = os.getenv("BOX_CLIENT_SECRET", "")
BOX_KEY_ID = os.getenv("BOX_KEY_ID", "")
BOX_PRIVATE_KEY = os.getenv("BOX_PRIVATE_KEY", "")  # PEM string; use \n for newlines in env
BOX_ENTERPRISE_ID = os.getenv("BOX_ENTERPRISE_ID", "")
BOX_USER_ID = os.getenv("BOX_USER_ID", "")  # For personal Box (enterpriseID 0): your Box user ID
BOX_PASSPHRASE = os.getenv("BOX_PASSPHRASE", "")

# The endpoint as per Sarvam documentation
URL = f"https://apps.sarvam.ai/api/analytics/v1/{ORG_ID}/{WORKSPACE_ID}/{APP_ID}/attempts"


def validate_config():
    required = {
        "SARVAM_ORG_ID": ORG_ID,
        "SARVAM_WORKSPACE_ID": WORKSPACE_ID,
        "SARVAM_APP_ID": APP_ID,
        "SARVAM_API_KEY": API_KEY,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
        )


def _get_box_token_jwt() -> str:
    """Exchange JWT assertion for Box access token. For personal Box (enterpriseID 0), set BOX_USER_ID and use box_sub_type user."""
    import jwt as pyjwt
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    key_pem = BOX_PRIVATE_KEY.encode().replace(br"\n", b"\n")
    password = BOX_PASSPHRASE.encode() if BOX_PASSPHRASE else None
    private_key = load_pem_private_key(key_pem, password=password)
    now = int(time.time())
    # Personal Box (enterpriseID 0): use user token. Otherwise enterprise token.
    if BOX_USER_ID and (not BOX_ENTERPRISE_ID or BOX_ENTERPRISE_ID == "0"):
        sub, box_sub_type = BOX_USER_ID, "user"
    else:
        sub, box_sub_type = BOX_ENTERPRISE_ID, "enterprise"
    payload = {
        "iss": BOX_CLIENT_ID,
        "sub": sub,
        "box_sub_type": box_sub_type,
        "aud": "https://api.box.com/oauth2/token",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + 60,
    }
    assertion = pyjwt.encode(
        payload, private_key, algorithm="RS256", headers={"kid": BOX_KEY_ID}
    )
    if hasattr(assertion, "decode"):
        assertion = assertion.decode("utf-8")
    resp = requests.post(
        "https://api.box.com/oauth2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
            "client_id": BOX_CLIENT_ID,
            "client_secret": BOX_CLIENT_SECRET,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_box_access_token() -> str:
    """Return Box access token: from BOX_ACCESS_TOKEN or by exchanging JWT."""
    if BOX_ACCESS_TOKEN:
        return BOX_ACCESS_TOKEN
    # Personal Box (enterpriseID 0) requires BOX_USER_ID for JWT; enterprise 0 token is not valid
    if BOX_ENTERPRISE_ID == "0" and not BOX_USER_ID:
        return ""
    has_jwt = all((BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_KEY_ID, BOX_PRIVATE_KEY))
    if has_jwt and (BOX_ENTERPRISE_ID or BOX_USER_ID):
        return _get_box_token_jwt()
    return ""


def upload_to_box(file_path: Path):
    token = _get_box_access_token() if BOX_FOLDER_ID else ""
    if not token or not BOX_FOLDER_ID:
        if BOX_FOLDER_ID and BOX_ENTERPRISE_ID == "0" and not BOX_USER_ID:
            print("Box API upload skipped (personal Box requires BOX_USER_ID for JWT).")
        else:
            print("Box API upload skipped (no Box token and/or BOX_FOLDER_ID not set).")
        return

    headers = {"Authorization": f"Bearer {token}"}
    upload_url = "https://upload.box.com/api/2.0/files/content"

    with file_path.open("rb") as file_data:
        files = {"file": (file_path.name, file_data)}
        data = {"attributes": f'{{"name":"{file_path.name}","parent":{{"id":"{BOX_FOLDER_ID}"}}}}'}
        response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=REQUEST_TIMEOUT_SECONDS)

    # File name exists: upload a new version instead.
    if response.status_code == 409:
        conflict_id = (
            response.json()
            .get("context_info", {})
            .get("conflicts", {})
            .get("id")
        )
        if not conflict_id:
            raise RuntimeError(f"Box upload conflict without file id: {response.text}")

        version_url = f"https://upload.box.com/api/2.0/files/{conflict_id}/content"
        with file_path.open("rb") as file_data:
            files = {"file": (file_path.name, file_data)}
            response = requests.post(version_url, headers=headers, files=files, timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Box upload failed ({response.status_code}): {response.text}")

    print("Uploaded report to Box via API successfully.")


def fetch_sarvam_data():
    validate_config()

    all_items = []
    limit = 1000  # Maximum records allowed per request
    offset = 0

    # Generate mandatory UTC timestamps in ISO8601 format
    # This fetches data from the last 1000 days
    now = datetime.now(timezone.utc)
    end_dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_dt = (now - timedelta(days=1000)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Documentation requires X-API-Key
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    print(f"Starting fetch for range: {start_dt} to {end_dt}")

    while True:
        # Mandatory query parameters
        params = {
            "start_datetime": start_dt,
            "end_datetime": end_dt,
            "limit": limit,
            "offset": offset
        }

        try:
            response = requests.get(
                URL,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            # Check for errors (like 422 or 401)
            if response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                break

            data = response.json()

            # The API returns an object with an 'items' list
            batch = data.get("items", [])

            if not batch:
                print("No more records found.")
                break

            all_items.extend(batch)
            print(f"Downloaded {len(all_items)} records so far (Offset: {offset})...")

            # If we received fewer items than the limit, we've reached the end
            if len(batch) < limit:
                break

            # Move the offset forward for the next loop
            offset += limit

        except Exception as e:
            print(f"A connection error occurred: {e}")
            break

    # ==========================================
    # 2. STORAGE - Save to Excel
    # ==========================================
    if all_items:
        df = pd.DataFrame(all_items)

        # Clean up column names if needed or just save directly
        date_suffix = datetime.now().strftime("%d%b%Y")
        filename = f"sarvam_attempts_report_{date_suffix}.xlsx"
        output_dir = Path(OUTPUT_DIR).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / filename
        df.to_excel(output_file, index=False)
        print("\nSUCCESS")
        print(f"Total records retrieved: {len(all_items)}")
        print(f"File saved as: {output_file}")
        try:
            upload_to_box(output_file)
        except Exception as e:
            print(f"Box upload failed (report still saved): {e}")
    else:
        print("\nNo data found for the selected time period.")


if __name__ == "__main__":
    fetch_sarvam_data()
