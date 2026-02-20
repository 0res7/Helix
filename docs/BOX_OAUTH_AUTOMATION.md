# Box OAuth automation – detailed steps

Complete step-by-step instructions so the **scheduled** workflow can upload the report to Box every day without you renewing a Developer Token.

---

## Part 1: Create a Box OAuth app

1. **Open the Box Developer Console**  
   Go to: **https://app.box.com/developers/console**

2. **Create a new app**  
   - Click **Create New App**.  
   - Choose **Custom App** → **Next**.  
   - Select **User Authentication (OAuth 2.0)** (do **not** choose JWT).  
   - Click **Next**, then **Create App**.

3. **Configure the app**  
   - Open the **Configuration** tab.
   - **Application Scopes**
     - Enable **Read and write all files and folders stored in Box** (or at least **Write**).
     - Leave other scopes as needed for your use.
   - **Redirect URL**
     - Under **Redirect URL**, click **Add a Redirect URL**.
     - Enter exactly: `https://app.box.com`  
     - Click **Save**.

4. **Get Client ID and Client Secret**  
   - In the same **Configuration** tab, at the top you’ll see:
     - **Client ID** (e.g. `abc123...`)
     - **Client Secret** — click **Show** or **Reveal** to see it.
   - Keep this page open or copy both values to a safe place. You’ll add them to GitHub later.

---

## Part 2: One-time OAuth – get a refresh token

You do this once in a browser and in Terminal (or Postman). After that, the workflow will refresh the token for you.

### 2.1 Build the authorize URL and open it

1. **Build the URL**  
   Replace `YOUR_CLIENT_ID` with your Box **Client ID** from Part 1.  
   Use the **exact** redirect URL you added (here: `https://app.box.com`).  
   Encode it for the URL: spaces become `%20`; here it stays `https://app.box.com`.

   ```
   https://account.box.com/api/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https%3A%2F%2Fapp.box.com&state=helix
   ```

   Example (fake ID):
   ```
   https://account.box.com/api/oauth2/authorize?response_type=code&client_id=xyz789abc&redirect_uri=https%3A%2F%2Fapp.box.com&state=helix
   ```

2. **Open the URL**  
   Paste the full URL into your browser and press Enter.

3. **Sign in and approve**  
   - Sign in to Box if asked.  
   - Approve the app (e.g. “Allow” / “Grant access”).

4. **Copy the `code`**  
   - You’ll be redirected to a URL like:
     `https://app.box.com/?code=long_string_here&state=helix`
   - Or:
     `https://app.box.com/?state=helix&code=long_string_here`
   - Copy **only** the value of `code` (the long string between `code=` and `&`).  
   - Do **not** include `code=` or `&state=...`.  
   - The code is single-use and usually expires in a few minutes, so do the next step right away.

**If you don’t see a redirect or the code (e.g. with `https://app.box.com` the page loads and the URL changes):**

Use **`http://localhost`** as the redirect URL so the code stays in the address bar:

1. **In Box Developer Console**  
   - Open your OAuth app → **Configuration** → **Redirect URL**.  
   - Add: **`http://localhost`** (no trailing slash). Save.

2. **Use this authorize URL** (same as before but with `redirect_uri=http://localhost` encoded):
   ```
   https://account.box.com/api/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost&state=helix
   ```
   Replace `YOUR_CLIENT_ID` with your Client ID.

3. **Open that URL** in your browser → sign in → approve the app.

4. **After approval**, the browser will redirect to something like:
   `http://localhost/?code=abc123...&state=helix`  
   The page may show “This site can’t be reached” or “Connection refused” because nothing is running on localhost. **That’s fine.** The **address bar** will still show the full URL with `code=...`. Copy the **code** value from the address bar (the part between `code=` and `&state=`).

5. When you run the **curl** in 2.2, use **`redirect_uri=http://localhost`** (not `https://app.box.com`).

### 2.2 Exchange the code for tokens

1. **Open Terminal** (macOS Terminal, or any shell).

2. **Run this command** (all one block), replacing the placeholders:
   - `PASTE_CODE_HERE` → the `code` you just copied.
   - `YOUR_CLIENT_ID` → your Box Client ID.
   - `YOUR_CLIENT_SECRET` → your Box Client Secret.
   - `redirect_uri` → must match what you used in the authorize URL: either `https://app.box.com` or `http://localhost`.

   If you used **https://app.box.com**:
   ```bash
   curl -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code" \
     -d "code=PASTE_CODE_HERE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=https://app.box.com"
   ```

   If you used **http://localhost** (to capture the code from the address bar):
   ```bash
   curl -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code" \
     -d "code=PASTE_CODE_HERE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=http://localhost"
   ```

3. **Read the response**  
   You’ll get JSON like:
   ```json
   {
     "access_token": "...",
     "refresh_token": "...",
     "expires_in": 3600,
     "token_type": "bearer"
   }
   ```
   Copy the **`refresh_token`** value (the long string). You’ll add it to GitHub as **BOX_REFRESH_TOKEN**.

---

## Part 3: GitHub – report environment secrets

Add these **in the report environment** (not repository secrets). If **BOX_ACCESS_TOKEN** is set there, remove it or leave it empty so the workflow uses the refresh token instead.

1. **Open the repo**  
   Go to **https://github.com/0res7/Helix** (or your repo).

2. **Go to environment secrets**  
   - **Settings** → **Environments** (left sidebar).  
   - Click the **report** environment (create it first if needed; see [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)).

3. **Add or update these environment secrets** (under **Environment secrets**):

   | Secret name           | Value to use |
   |-----------------------|--------------|
   | **BOX_REFRESH_TOKEN** | The `refresh_token` you copied from the curl response in Part 2. |
   | **BOX_CLIENT_ID**     | Your Box app **Client ID** from Part 1. |
   | **BOX_CLIENT_SECRET** | Your Box app **Client Secret** from Part 1. |
   | **BOX_FOLDER_ID**     | Your Box folder ID (e.g. `366969394973`). From the folder URL: `https://app.box.com/folder/366969394973` → ID is `366969394973`. |

   For each:
   - Click **Add secret** (or the pencil to edit).
   - **Name:** type the exact name (e.g. `BOX_REFRESH_TOKEN`).
   - **Value:** paste the value.
   - Save.

4. **Do not set BOX_ACCESS_TOKEN**  
   When using OAuth refresh, leave **BOX_ACCESS_TOKEN** unset in the **report** environment (or delete it if it was there for the Developer Token).

---

## Part 4: GitHub – repository secret GH_PAT

The workflow needs a GitHub token so it can **update** the **BOX_REFRESH_TOKEN** secret after each run (Box gives a new refresh token each time). Add that token as a **repository** secret named **GH_PAT**.

### 4.1 Create a Personal Access Token (PAT)

1. **Open GitHub token settings**  
   **https://github.com/settings/tokens**  
   (Or: GitHub profile picture → **Settings** → **Developer settings** → **Personal access tokens**.)

2. **Create a token**  
   - **Tokens (classic)** → **Generate new token** → **Generate new token (classic)**.  
   - **Note:** e.g. `Helix Box secret update`.  
   - **Expiration:** pick a duration (e.g. 90 days or No expiration).  
   - **Scopes:** enable **repo** (full control of private repositories).  
     - That allows the token to update repo/environment secrets.  
   - Click **Generate token**.

3. **Copy the token**  
   You’ll see it only once. Copy it (e.g. `ghp_...`).

### 4.2 Add GH_PAT as a repository secret

1. **Open the repo**  
   **https://github.com/0res7/Helix**.

2. **Repository secrets**  
   - **Settings** → **Secrets and variables** → **Actions** (left sidebar).  
   - Under **Repository secrets** (not **Environment secrets**), click **New repository secret**.

3. **Create the secret**  
   - **Name:** `GH_PAT`  
   - **Value:** paste the Personal Access Token you generated.  
   - Click **Add secret**.

---

## Part 5: Push and run the workflow

1. **Push your code**  
   Make sure the latest code (with OAuth refresh and the “Persist new Box refresh token” step) is pushed to the default branch (e.g. `main`).

2. **Run the workflow once**  
   - **Actions** → **Sarvam Attempts Report** → **Run workflow** → **Run workflow**.  
   - Wait for the run to finish.  
   - Open the run → **generate-report** job.  
   - You should see the report generated and “Uploaded report to Box via API successfully…” (and optionally “Updated BOX_REFRESH_TOKEN for next run.”).

3. **Check Box**  
   Open your Box folder (e.g. `https://app.box.com/folder/366969394973`) and confirm the new Excel file is there.

4. **Scheduled runs**  
   After that, the **scheduled** run (e.g. daily at 10:30 AM IST) will:
   - Use the current **BOX_REFRESH_TOKEN** to get an access token.
   - Upload the report to Box.
   - Save the new refresh token back into **BOX_REFRESH_TOKEN** so the next run keeps working.

You don’t need to touch Box or tokens again unless you revoke the app or the refresh token expires (e.g. after long inactivity; then repeat Part 2 and update **BOX_REFRESH_TOKEN**).

---

## Troubleshooting

### Box upload returns 401

**Cause:** The workflow is using an expired **Developer Token** (`BOX_ACCESS_TOKEN`) instead of the OAuth refresh token. The script uses `BOX_ACCESS_TOKEN` first when it is set; that token expires in about an hour and then Box returns 401.

**Fix:**

1. In GitHub → **Settings** → **Environments** → **report** → **Environment secrets**, find **BOX_ACCESS_TOKEN**.
2. **Delete** it (or leave it unset) so the workflow uses **BOX_REFRESH_TOKEN**, **BOX_CLIENT_ID**, and **BOX_CLIENT_SECRET** to get a fresh access token each run.
3. Re-run the workflow. In the **Generate report** step log you should see **"Box: using access token from OAuth refresh."** and the upload should succeed.

If you still get 401 after removing `BOX_ACCESS_TOKEN`:

- Confirm the OAuth app has **Read and write all files and folders** (or at least write) scope.
- Confirm **BOX_FOLDER_ID** is a folder where your Box user has upload permission (e.g. you are a collaborator with Editor access).

### OAuth refresh fails (invalid_grant or 400)

- **BOX_CLIENT_ID and BOX_CLIENT_SECRET must be from the same OAuth app** (User Authentication) that you used in the browser to get the refresh token. If you have both a JWT app and an OAuth app in Box, use the **OAuth app’s** Client ID and Secret with **BOX_REFRESH_TOKEN**, not the JWT app’s.
- **Refresh token expired or revoked** — Do the one-time OAuth flow again (Part 2), get a new `refresh_token`, and set it as **BOX_REFRESH_TOKEN** in the **report** environment. Then ensure **GH_PAT** is set as a **repository** secret so the “Persist new Box refresh token” step can save the new token after each run.

### Redirect URL options

You can use any redirect URL that Box allows and that lets you capture the `code`:

- **`https://app.box.com`** — Box redirects here; copy the `code` from the URL after approval (see Part 2.1).
- **`http://localhost`** — Useful if the code does not appear in the URL with `https://app.box.com`; see the "If you don't see a redirect or the code" section in Part 2.1.
- **`http://localhost:3000/callback`** — Same idea; add this exact URL in the Box app **Redirect URL** list and **Save**, then use it in the authorize URL and in the `curl` `redirect_uri` when exchanging the code.

---

## Quick checklist

- [ ] Box: OAuth app created (User Authentication), redirect URL `https://app.box.com`, write scope enabled.
- [ ] Box: Client ID and Client Secret copied.
- [ ] Browser: Authorize URL opened, app approved, `code` copied from redirect URL.
- [ ] Terminal: `curl` run with `code`, client id, client secret, `redirect_uri=https://app.box.com`; `refresh_token` copied.
- [ ] GitHub **report** environment: **BOX_REFRESH_TOKEN**, **BOX_CLIENT_ID**, **BOX_CLIENT_SECRET**, **BOX_FOLDER_ID** set; **BOX_ACCESS_TOKEN** not set.
- [ ] GitHub **repository** secret: **GH_PAT** set (PAT with **repo** scope).
- [ ] Workflow run once manually; run succeeds and file appears in Box.
- [ ] Schedule is enabled (see [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)); next automatic run will be at 10:30 AM IST.
