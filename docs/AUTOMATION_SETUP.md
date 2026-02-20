# Turn on automation – detailed instructions

Follow these steps so the Sarvam report runs **automatically every day at 10:30 AM IST** and you can download the Excel file from GitHub Actions.

---

## Step 1: Open your repository

1. Go to **https://github.com/0res7/Helix** (or your fork).
2. Make sure you’re signed in and you have **admin** or **write** access to the repo.

---

## Step 2: Confirm the workflow is on the default branch

Scheduled runs **only** use the workflow file on the **default branch** (usually `main`).

1. Click the branch dropdown (it usually says **main**).
2. If you don’t see **main**, go to **Settings** → **General** → **Default branch** and note the branch name (e.g. `main`).
3. Open **Code** → **.github/workflows/sarvam-attempts-report.yml**.
4. Check the branch shown (e.g. “Branch: main”). If the workflow is on another branch, merge or move it to the default branch and push.

---

## Step 3: Enable GitHub Actions (if needed)

1. Go to **Actions**.
2. If you see a message like “I understand my workflows go to GitHub”, click **Enable** or approve.
3. If Actions are disabled: **Settings** → **Actions** → **General** → under “Actions permissions” choose **Allow all actions and reusable workflows** (or your preferred option) and save.

---

## Step 4: Create the “report” environment

The workflow expects an environment named **report** and reads secrets from it.

1. Go to **Settings** (repo settings, not your profile).
2. In the left sidebar, under **Environments**, click **Environments**.
3. Click **New environment**.
4. Name it exactly: **report**.
5. Click **Configure environment**. You can leave “Required reviewers” and “Wait timer” empty.
6. Click **Save protection rules** (or **Save**).

---

## Step 5: Add secrets to the “report” environment

1. Still under **Settings** → **Environments**, click the **report** environment.
2. Under **Environment secrets**, click **Add secret** (or **Add environment secret**).

Add these **four** secrets (get the values from your Sarvam setup or team):

| Secret name         | Where to get it / what to put |
|---------------------|-------------------------------|
| **SARVAM_ORG_ID**   | Your Sarvam org ID (e.g. `applemaps.com`). |
| **SARVAM_WORKSPACE_ID** | Sarvam workspace ID (e.g. `applemaps-com-defa-4568bf`). |
| **SARVAM_APP_ID**   | Sarvam app ID (e.g. `apple-maps--fd4db570-6e85`). |
| **SARVAM_API_KEY**  | Sarvam API key (starts with `sk_...`). Keep this private. |

For each one:

- Click **Add secret**.
- **Name:** type the exact name (e.g. `SARVAM_ORG_ID`).
- **Value:** paste the value.
- Click **Add secret** (or **Save**).

Repeat until all four Sarvam secrets exist under the **report** environment.

**Box (optional, can skip for now):**  
If you want the report uploaded to Box later, see [BOX_SETUP.md](BOX_SETUP.md) and, for scheduled uploads without renewing tokens, [BOX_OAUTH_AUTOMATION.md](BOX_OAUTH_AUTOMATION.md). Add **BOX_FOLDER_ID** and either **BOX_ACCESS_TOKEN** (Developer Token, short-lived) or OAuth refresh secrets (**BOX_REFRESH_TOKEN**, **BOX_CLIENT_ID**, **BOX_CLIENT_SECRET**). When using OAuth refresh, do **not** set **BOX_ACCESS_TOKEN** in the report environment. If Box upload fails with 401, remove **BOX_ACCESS_TOKEN** so the workflow uses the refresh token; see [BOX_OAUTH_AUTOMATION.md](BOX_OAUTH_AUTOMATION.md#troubleshooting).

---

## Step 6: Run the workflow once manually (important)

Running it once manually:

- Verifies that secrets and the workflow are correct.
- Counts as “activity” so GitHub does not disable scheduled workflows for inactivity.

1. Go to the **Actions** tab.
2. In the left sidebar, click **Sarvam Attempts Report**.
3. On the right, click **Run workflow**.
4. Leave **Branch** as your default branch (e.g. **main**).
5. Click the green **Run workflow** button.
6. Wait 1–2 minutes. Click the run that appears (e.g. “Run workflow” with a yellow dot, then green when done).
7. Open the **generate-report** job and confirm:
   - “Generate report” step shows “SUCCESS” and “Total records retrieved: …”.
   - “Upload report artifact” step succeeded.
8. At the bottom of the run page, under **Artifacts**, download **sarvam-attempts-report** and confirm the Excel file is inside.

If anything fails, fix the error (usually a missing or wrong secret) and run again.

---

## Step 7: Confirm the schedule is active

1. After at least one successful manual run, stay on **Actions** → **Sarvam Attempts Report**.
2. If you ever see a yellow banner like **“Scheduled workflows have been disabled…”**, click the link in the message and **enable** scheduled workflows.
3. The workflow is scheduled with **cron: "0 5 * * *"** (UTC), which is **10:30 AM IST** every day. GitHub does not show “10:30 AM IST” in the UI; you only see runs after they start.
4. Scheduled runs can be **up to ~15 minutes late**. So the run may show up between about 10:30 and 10:45 AM IST.

---

## Step 8: When the scheduled run will happen

- **First time:** Often the **next** calendar day at 10:30 AM IST (e.g. if you set up today, the first automatic run may be tomorrow morning).
- **After that:** Every day at about 10:30 AM IST (05:00 UTC), as long as:
  - The workflow file is on the default branch.
  - There has been some repo activity in the last 60 days (e.g. a manual run or a commit).
  - Scheduled workflows are not disabled.

---

## Troubleshooting: Why automation doesn’t run or fails

### Scheduled runs never appear

- **Workflow not on default branch**  
  Scheduled workflows run only from the **default branch** (e.g. `main`). Open **Code** → `.github/workflows/sarvam-attempts-report.yml` and confirm the file is on the default branch (branch dropdown at the top).

- **Scheduled workflows disabled**  
  GitHub can disable scheduled workflows after ~60 days of no repo activity, or if disabled in settings. In **Actions** → **Sarvam Attempts Report**, look for a yellow banner like “Scheduled workflows have been disabled…”; click the link and **enable** them. Trigger a manual run or push a commit so the repo is active.

- **Schedule time**  
  The workflow uses **cron: "0 5 * * *"** (05:00 UTC = **10:30 AM IST**). The first scheduled run is often the **next calendar day**; runs can be up to ~15 minutes late.

### Workflow runs but the job fails or is stuck

- **Environment “report” missing**  
  The job uses `environment: report`. If that environment doesn’t exist (**Settings** → **Environments**), the job can fail at start. Create an environment named exactly **report**.

- **Required reviewers on “report”**  
  If the **report** environment has “Required reviewers” or a “Wait timer”, the run will sit **waiting for approval** until someone approves it. Remove required reviewers (or approve the run) so the job can proceed.

- **Missing or wrong secrets**  
  The “Generate report” step needs the **report** environment secrets: **SARVAM_ORG_ID**, **SARVAM_WORKSPACE_ID**, **SARVAM_APP_ID**, **SARVAM_API_KEY**. If any are missing or wrong, the script will fail. Check **Settings** → **Environments** → **report** → **Environment secrets**.

- **Box upload 401**  
  If the log shows “Box upload failed (401)”, remove **BOX_ACCESS_TOKEN** from the **report** environment so the workflow uses the OAuth refresh token. See [BOX_OAUTH_AUTOMATION.md](BOX_OAUTH_AUTOMATION.md#troubleshooting).

### Report succeeds but Box upload fails every time

- **OAuth refresh not used**  
  In the “Generate report” step log, you should see **“Box: using access token from OAuth refresh.”** If you don’t, the script is using **BOX_ACCESS_TOKEN** (expired) or JWT. Remove **BOX_ACCESS_TOKEN** and ensure **BOX_REFRESH_TOKEN**, **BOX_CLIENT_ID**, **BOX_CLIENT_SECRET**, and **BOX_FOLDER_ID** are set in the **report** environment.

- **Refresh token never updated**  
  Each run, Box may return a new refresh token. The workflow has a “Persist new Box refresh token” step that writes it back to **BOX_REFRESH_TOKEN**. That step needs **GH_PAT** as a **repository** secret (**Settings** → **Secrets and variables** → **Actions** → **Repository secrets**), with **repo** scope. If **GH_PAT** is missing, the new token is never saved and uploads can start failing after Box rotates the token.

### Quick checks

| Check | Where |
|-------|--------|
| Workflow on default branch? | **Code** → `.github/workflows/sarvam-attempts-report.yml` → branch dropdown |
| Scheduled workflows enabled? | **Actions** → banner / **Settings** → **Actions** → **General** |
| Environment **report** exists? | **Settings** → **Environments** |
| **report** has SARVAM_* and (for Box) BOX_*? | **Settings** → **Environments** → **report** |
| **GH_PAT** set (for Box token refresh)? | **Settings** → **Secrets and variables** → **Actions** → **Repository secrets** |
| **BOX_ACCESS_TOKEN** removed when using OAuth? | **Settings** → **Environments** → **report** → Environment secrets |

---

## Checklist summary

- [ ] Repo default branch (e.g. `main`) contains `.github/workflows/sarvam-attempts-report.yml`.
- [ ] **Settings** → **Actions**: Actions are enabled.
- [ ] **Settings** → **Environments**: Environment **report** exists.
- [ ] **report** environment has secrets: **SARVAM_ORG_ID**, **SARVAM_WORKSPACE_ID**, **SARVAM_APP_ID**, **SARVAM_API_KEY**.
- [ ] **Actions** → **Sarvam Attempts Report** → **Run workflow** ran successfully at least once.
- [ ] You downloaded the artifact and confirmed the Excel file is correct.
- [ ] No “Scheduled workflows have been disabled” banner; if there was one, you enabled schedules.

After this, automation is on: the report will run daily at 10:30 AM IST and the Excel file will be in **Actions** → latest run → **Artifacts** → **sarvam-attempts-report**.
