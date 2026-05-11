# UB Labor Market Intelligence Dashboard

Weekly auto-refreshing public webpage for UB Career & Internship Center.

## What this is

A single-file static website (`index.html`) that reads `data/labor_market.json`
and renders live labor market data for students and faculty. A Python script
fetches from the BLS API every Monday and updates the JSON automatically.

---

## Folder structure

```
ub-dashboard/
├── index.html                         # The public webpage
├── data/
│   └── labor_market.json              # Auto-generated weekly — do not edit manually
├── scripts/
│   └── weekly_refresh.py              # BLS data fetch + transform script
└── .github/
    └── workflows/
        └── weekly_refresh.yml         # GitHub Actions cron job (Monday 6 AM)
```

---

## Deployment (GitHub Pages — free)

1. Create a new GitHub repository (public)
2. Upload all files in this folder
3. Go to **Settings → Pages → Source → Deploy from branch → main / root**
4. Your site is live at `https://yourusername.github.io/ub-dashboard/`

Optional: add a custom domain like `careers.ubalt.edu/market` via Settings → Pages → Custom domain.

---

## Setting up the BLS API key

1. Register for a free API key at https://data.bls.gov/registrationEngine/
2. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Name: `BLS_API_KEY` · Value: your key

The GitHub Actions workflow automatically uses this secret every Monday.

---

## Manual refresh

To run the data refresh manually from your terminal:

```bash
BLS_API_KEY=your_key_here python scripts/weekly_refresh.py
```

Or trigger it from GitHub UI: **Actions → Weekly Labor Market Refresh → Run workflow**

---

## Updating occupations or programs

Edit the `OCCUPATION_META` and `PROGRAMS` dictionaries in `scripts/weekly_refresh.py`.
The changes take effect on the next weekly run, or immediately after a manual run.

To add a new occupation:
1. Find its SOC code at https://www.onetonline.org/
2. Look up its BLS OEWS series ID for Baltimore Metro at https://www.bls.gov/oes/
3. Add a new entry to `OCCUPATION_SERIES` and `OCCUPATION_META`

---

## Connecting to Lightcast (optional upgrade)

If your institution has a Lightcast license, replace the `bls_fetch()` call
with the Lightcast API to get real-time posting counts, talent gap scores,
and emerging skills data. Contact your Lightcast rep for API credentials.

---

## Data sources

| Source | What it provides | Frequency |
|--------|-----------------|-----------|
| BLS OEWS | Occupation wages & employment | Annual |
| BLS QCEW | Regional industry employment | Quarterly |
| BLS Projections | Future demand | Biennial |
| O*NET | Skills & education requirements | Quarterly |
| Handshake/UBworks | Job posting counts | Weekly export |
| Lightcast (optional) | Real-time postings & skills | Weekly |

---

*Built for UB Career & Internship Center · College of Public Affairs*
