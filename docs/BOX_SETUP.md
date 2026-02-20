# Box upload setup

Use these values so the report is uploaded to your Box folder.

## Personal Box (app.box.com) and JWT

If you use **personal/developer Box** (enterpriseID `"0"`), Box often returns **"The 'sub' specified is invalid"** when using JWT with your account user ID. For Application Access apps, Box expects the `sub` to be an **App User** created by the app, not your personal account ID, and personal Box does not support enterprise tokens needed to create App Users.

**Automated option for personal Box:** use **OAuth refresh token** (Option C below). You do a one-time OAuth in the browser to get a refresh token; the workflow then refreshes it each run and persists the new token so scheduled runs keep working.

**Quick manual option:** use a **Developer Token** (Option A). It expires in 1 hour; for scheduled runs use Option C or the artifact only.

## BOX_FOLDER_ID

From your folder URL:

- URL: `https://apple.ent.box.com/folder/366400499122?...`
- **BOX_FOLDER_ID** = **`366400499122`**

Add this as a secret (or env var) in your GitHub **report** environment.

---

## Troubleshooting: Box upload 401

If you see **"Box upload failed (401)"** in the workflow log, the script is likely using an expired **Developer Token** (`BOX_ACCESS_TOKEN`). Remove **BOX_ACCESS_TOKEN** from the **report** environment so the workflow uses the OAuth refresh token instead. See [BOX_OAUTH_AUTOMATION.md](BOX_OAUTH_AUTOMATION.md#troubleshooting) for details.

---

## BOX_ACCESS_TOKEN (two options)

### Option A: Developer Token (works for personal Box)

Access tokens from Box expire in **1 hour**. This is the option that works with **personal/developer Box** (app.box.com) when JWT returns "sub is invalid".

1. Go to [Box Developer Console](https://app.box.com/developers/console).
2. Open your app (the same JWT app is fine) → **Configuration**.
3. Under **Developer Token**, click **Generate** and copy the token.
4. In GitHub → **report** environment → add or update secret **BOX_ACCESS_TOKEN** with that token.
5. Run the workflow **within about an hour** (or run it manually whenever you need the file in Box and refresh the token first).

For **scheduled** daily runs on personal Box, use **Option C** (OAuth refresh) instead.

---

### Option C: OAuth refresh token (automated for personal Box)

Use this so the **scheduled** workflow can upload to Box without touching a Developer Token every hour.

**→ For full step-by-step instructions, see [BOX_OAUTH_AUTOMATION.md](BOX_OAUTH_AUTOMATION.md).**

Summary:

1. **Create an OAuth app in Box** (separate from any JWT app)
   - [Box Developer Console](https://app.box.com/developers/console) → **Create new app** → **Custom App**.
   - Choose **User Authentication (OAuth 2.0)** → **Create**.
   - In **Configuration** → **Application Scopes**, enable **Read and write all files and folders** (or at least write).
   - Under **Redirect URL**, add `https://app.box.com` (or use a URL you control; you’ll paste the redirect back into the browser or a script).
   - Note the **Client ID** and **Client Secret**.

2. **Get a refresh token (one-time)**
   - Open this URL in your browser (replace `YOUR_CLIENT_ID` and `YOUR_REDIRECT_URI`):
     ```
     https://account.box.com/api/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&state=helix
     ```
   - Sign in to Box and approve the app. You’ll be redirected to something like `https://app.box.com/?code=CODE&state=helix`. Copy the `code` from the URL.
   - Exchange the code for tokens (replace placeholders and run in Terminal, or use Postman):
     ```bash
     curl -X POST "https://api.box.com/oauth2/token" \
       -d "grant_type=authorization_code" \
       -d "code=PASTE_CODE_HERE" \
       -d "client_id=YOUR_CLIENT_ID" \
       -d "client_secret=YOUR_CLIENT_SECRET" \
       -d "redirect_uri=YOUR_REDIRECT_URI"
     ```
   - The response includes `refresh_token`. Copy it.

3. **Add GitHub secrets**
   - In the **report** environment: **BOX_REFRESH_TOKEN** (the refresh token), **BOX_CLIENT_ID**, **BOX_CLIENT_SECRET**, **BOX_FOLDER_ID** (your folder ID, e.g. `366969394973`). Do **not** set **BOX_ACCESS_TOKEN** when using refresh.
   - So the workflow can update the refresh token each run, add a **repository** secret (not environment): **GH_PAT**. Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with scope **repo** (or **admin:repo_hook** / fine-grained with **Secrets: Write**), and add it as **GH_PAT** under **Settings → Secrets and variables → Actions → Repository secrets**.

4. **Run the workflow**  
   The first run uses your refresh token to get an access token and upload. Box returns a new refresh token; the workflow saves it into **BOX_REFRESH_TOKEN** for the next run. Scheduled runs then keep working without you doing anything.

---

### Option B: JWT app (enterprise / non–personal Box)

A JWT app lets the script get a new access token on every run. No short-lived token to refresh.

1. **Create a JWT app**
   - [Box Developer Console](https://app.box.com/developers/console) → **Create new app** → **Custom App**.
   - Choose **Server Authentication (with JWT)** → **Create**.
   - Enable **2FA** on your Box account if required.

2. **Generate keypair and get config**
   - In the app → **Configuration** → scroll to **Add and Manage Public Keys**.
   - Click **Generate a Public/Private Keypair**.
   - A JSON config file is downloaded (Box does not store the private key; keep it safe).

3. **Authorize the app**
   - **Authorization** tab → **Review and Submit** so your Box admin can approve (or approve yourself if you are admin).

4. **Grant the app access to the folder**
   - The JWT app has a **Service Account** (or App User). In Box, open folder `366400499122` and add that service account (or the app user) as a **collaborator** with **Editor** (or upload) access so the script can upload files there.

5. **Personal Box (enterpriseID 0)**  
   If your config has `"enterpriseID": "0"` (personal/developer Box), you must set **BOX_USER_ID** so the script can request a user token. Find your Box user ID: sign in at [Box](https://app.box.com) → **Account Settings** (profile/gear) → **Account** tab → **Account ID**. Add it as the **BOX_USER_ID** secret. Without it, Box upload is skipped.  
   **Also enable "Generate user access tokens"** in the Box Developer Console: open your app → **Configuration** → **Application Scopes** → turn on **Generate user access tokens**. Save and re-authorize the app if prompted. Without this scope, the token API returns 400 when requesting a user token.

6. **Map config to GitHub secrets**

   From the downloaded JSON (or from the Configuration tab):

   | JSON path / Config        | GitHub secret      |
   |---------------------------|--------------------|
   | `boxAppSettings.clientID` | **BOX_CLIENT_ID**  |
   | `boxAppSettings.clientSecret` | **BOX_CLIENT_SECRET** |
   | `boxAppSettings.appAuth.publicKeyID` | **BOX_KEY_ID** |
   | `boxAppSettings.appAuth.privateKey` (full PEM) | **BOX_PRIVATE_KEY** |
   | `enterpriseID` (or from Configuration) | **BOX_ENTERPRISE_ID** |
   | `boxAppSettings.appAuth.passphrase` (if set) | **BOX_PASSPHRASE** |

   - **BOX_PRIVATE_KEY**: Paste the full private key PEM (including `-----BEGIN ... KEY-----` and `-----END ... KEY-----`). In GitHub secrets you can paste it as-is; in a shell env you may need to replace real newlines with `\n`.
   - Do **not** put **BOX_ACCESS_TOKEN** when using JWT; the script will get the token from these credentials.

7. **Add BOX_FOLDER_ID**
   - **BOX_FOLDER_ID** = **`366400499122`** (same as above).

After that, each run will use the JWT credentials to obtain an access token and upload to your Box folder.
