[README.md](https://github.com/user-attachments/files/27713614/README.md)
# UB Labor Market Intelligence Dashboard

Weekly auto-refreshing public dashboard for the University of Baltimore Career & Internship Center.
**Law School and all law-affiliated programs are excluded per policy.**

---

## Package contents

```
ub-dashboard/
├── index.html                          # Complete dashboard (students + faculty)
├── data/
│   └── labor_market.json               # Live data — auto-updated weekly
├── scripts/
│   └── weekly_refresh.py               # BLS + O*NET data pipeline
├── .github/
│   └── workflows/
│       └── weekly_refresh.yml          # GitHub Actions cron automation
└── README.md
```

---

## Features

### Student view
- Occupation cards with **degree required**, Bright Outlook badge, top skills, wages
- Clickable **O*NET job postings by region** link on every card
- Direct job search links: CareerOneStop, USAJobs, LinkedIn, Indeed, Idealist, MD State Jobs
- **Region selector** (Baltimore Metro / Maryland / DC Metro / Virginia Metro) switches the program alignment table
- Program alignment table shows LQ, alignment strength, outlook, median wage, and job posting links for all 44 programs
- CSV export: occupations, programs
- JSON export: full dataset

### Faculty view
- **No cards** — table-only layout for dense data comparison
- **Region selector** switches Location Quotient bars, growth chart, and employment share donut
- Multi-region program alignment table: all 44 programs × 4 regions with color-coded LQ chips
- Regional strength, curriculum alignment, and recommendations columns
- CSV export: alignment data, industry data
- WCAG 2 AA compliant throughout

---

## Deployment (GitHub Pages — free)

1. Create a public GitHub repository
2. Upload all files (index.html must be at root level)
3. Go to **Settings → Pages → Source → Deploy from branch → main / root**
4. Site is live at `https://yourusername.github.io/ub-labor-market-dashboard/`

---

## GitHub Secrets (Settings → Secrets and variables → Actions)

| Secret name  | Where to get it                                | Required? |
|---|---|---|
| `BLS_API_KEY`  | Register free: data.bls.gov/registrationEngine/ | Yes |
| `ONET_API_KEY` | Register free: services.onetcenter.org/developer/ | Yes |

---

## Manual refresh

```bash
BLS_API_KEY=your_key ONET_API_KEY=your_key python scripts/weekly_refresh.py
```

Or trigger from GitHub: **Actions → Weekly Labor Market Refresh → Run workflow**

---

## Data sources

| Source | Provides | Frequency |
|---|---|---|
| BLS OEWS | Occupation wages | Annual (May) |
| BLS QCEW | Regional industry employment | Quarterly |
| BLS Projections | Future occupational demand | Biennial |
| O*NET Web Services | Skills, education, Bright Outlook | Quarterly |

---

## Schools included
- Merrick School of Business
- College of Public Affairs
- Yale Gordon College of Arts & Sciences

**School of Law excluded per dashboard policy.**

---

*University of Baltimore Career & Internship Center · careerservices@ubalt.edu*
