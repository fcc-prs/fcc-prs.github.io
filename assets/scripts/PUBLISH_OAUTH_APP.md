# Publishing the FCCPrsApp OAuth App to Production

The Google OAuth app used by `draft_email_doc.py` and `doc_to_mail.py` is currently
in **Testing mode**, which means refresh tokens expire after 7 days. Publishing it to
Production removes this limit (tokens last until 6 months of non-use).

## Steps

### 1. Publish the app in Google Cloud Console

1. Go to [https://console.cloud.google.com/auth/branding](https://console.cloud.google.com/auth/branding)
   and make sure the correct project (FCCPrsApp) is selected.
2. Find the "Publish app" button and confirm. Because the app uses only `drive.file`
   (a sensitive scope, not a restricted one), Google should allow publishing without
   a formal security review.
3. You may see a warning that the app is unverified — that is fine for personal use.

### 2. Re-authenticate locally to get a Production-mode token

```bash
cd /path/to/fcc-prs.github.io
rm token.json
conda activate hsfindia
python3 assets/scripts/draft_email_doc.py
```

A browser window will open. You may see an "unverified app" warning — click
**Advanced → Go to FCCPrsApp (unsafe)** and complete the OAuth flow.
A fresh `token.json` will be written.

### 3. Update GitHub Secrets

Go to the repo's **Settings → Secrets and variables → Actions** and update:

- `GOOGLE_TOKEN_JSON` — paste the full contents of the new `token.json`

`GOOGLE_APPS_JSON` does not need updating unless you recreated the OAuth client.

### 4. Manually trigger the workflow to verify

Go to **Actions → create weekly email doc → Run workflow**.
Confirm it completes without errors and that a new Google Doc is shared with you.

## Notes

- `token.json` and `google_apps.json` are gitignored — never commit them.
- The scripts use `drive.file` scope (not the broader `drive` scope) so the app
  only has access to files it creates — this is intentional and what allows
  publishing without Google verification.
- After publishing, the Monday 07:30 UTC schedule will keep the token perpetually
  fresh as long as the workflow runs successfully each week.
