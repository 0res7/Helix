# Box upload setup

Use these values so the report is uploaded to your Box folder.

## BOX_FOLDER_ID

From your folder URL:

- URL: `https://apple.ent.box.com/folder/366400499122?...`
- **BOX_FOLDER_ID** = **`366400499122`**

Add this as a secret (or env var) in your GitHub **report** environment.

---

## BOX_ACCESS_TOKEN (two options)

### Option A: Developer Token (quick test only)

Access tokens from Box expire in **1 hour**. Fine for a one-off run; for daily scheduled runs use Option B.

1. Go to [Box Developer Console](https://app.box.com/developers/console).
2. Create an app or open an existing one:
   - **Create new app** → **Custom App** → **User Authentication (OAuth 2.0)** or use an existing app.
3. Open the app → **Configuration**.
4. Under **Developer Token**, click **Generate**.
5. Copy the token and add it as the **BOX_ACCESS_TOKEN** secret in GitHub (report environment).
6. Ensure your Box user has access to folder `366400499122` (you do if you opened that link).

For scheduled runs you would have to regenerate and update the secret often, so prefer Option B.

---

### Option B: JWT app (recommended for scheduled runs)

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
   If your config has `"enterpriseID": "0"` (personal/developer Box), you must set **BOX_USER_ID** so the script can request a user token. Find your Box user ID: sign in at [Box](https://app.box.com) → **Account Settings** (profile/gear) → the numeric **User ID** is in the URL or on the page. Add it as the **BOX_USER_ID** secret. Without it, Box upload is skipped (the report still generates and the workflow artifact is produced).

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
