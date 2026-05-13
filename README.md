[README.md](https://github.com/user-attachments/files/27718039/README.md)
# 🎓 UB Labor Market Intelligence Dashboard

**University of Baltimore · Career & Internship Center**

A fully automated, WCAG 2.1 AA compliant labor market intelligence dashboard providing real-time career insights for students, faculty, and advisors across four regional markets: Baltimore Metro, Maryland, DC Metro, and Virginia Metro.

[![Live Dashboard](https://img.shields.io/badge/Live-Dashboard-gold?style=for-the-badge)](https://yourusername.github.io/ub-labor-market/)
[![WCAG 2.1 AA](https://img.shields.io/badge/WCAG%202.1-AA%20Compliant-green?style=for-the-badge)](https://www.w3.org/WAI/WCAG21/quickref/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## 📊 **What's Inside**

### **4 Interactive Views**

| View | Audience | Features |
|------|----------|----------|
| **👨‍🎓 Student View** | Students & Career Changers | Program cards with degree badges, regional alignment insights, salary data, career outlook |
| **👩‍🏫 Faculty View** | Faculty & Administrators | Program-to-market alignment analysis, Location Quotient metrics, curriculum recommendations |
| **💼 Occupations** | Career Advisors | 39 tracked occupations with O*NET links, salary data, demand indicators, education requirements |
| **📊 Charts** | All Users | 4 interactive Chart.js visualizations comparing regions and industries |

### **Data Coverage**

✅ **43 UB Programs** across 3 schools:
- Merrick School of Business (6 programs)
- College of Public Affairs (17 programs)
- Yale Gordon College of Arts & Sciences (20 programs)

✅ **4 Regional Markets:**
- Baltimore Metro (CBSA 12580)
- Maryland Statewide (State 24)
- DC Metro (CBSA 47900)
- Virginia Metro - Richmond (CBSA 40060)

✅ **20 NAICS Industries** per region with:
- Employment data (2022-2024)
- Location Quotients (LQ)
- Growth rates
- National benchmarks

✅ **39 SOC Occupations** with:
- Median wages
- Demand levels
- Education requirements
- Clickable O*NET links
- Job posting links (CareerOneStop, USAJobs, LinkedIn, Indeed)

---

## 🚀 **Quick Start**

### **Option 1: View Live Demo (Immediate)**

1. Download `ub_labor_market_dashboard_v3.html`
2. Download `labor_market_data_v3.json`
3. Place both files in the same folder
4. Double-click the HTML file
5. **Done!** Dashboard opens in your browser

### **Option 2: Deploy to GitHub Pages (Recommended)**

```bash
# 1. Create a new GitHub repository
# Go to github.com → New repository → Name it "ub-labor-market"

# 2. Clone and setup locally
git clone https://github.com/yourusername/ub-labor-market.git
cd ub-labor-market

# 3. Add your files
# - Rename ub_labor_market_dashboard_v3.html → index.html
# - Place labor_market_data_v3.json in same directory
# - Add weekly_refresh.py to root
# - Create .github/workflows/ folder and add weekly_refresh.yml

# 4. Push to GitHub
git add .
git commit -m "Initial dashboard deployment"
git push origin main

# 5. Enable GitHub Pages
# Go to: Settings → Pages → Source: main branch → Save
```

**Your dashboard will be live at:**
```
https://yourusername.github.io/ub-labor-market/
```

---

## 🔧 **Setup Automated Weekly Refresh**

### **Step 1: Get BLS API Key (Free)**

1. Visit: https://api.bls.gov/registrationEngine/
2. Register with your email
3. Copy your API key (arrives via email)

### **Step 2: Add API Key to GitHub**

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `BLS_API_KEY`
4. Value: *(paste your key)*
5. Click **Add secret**

### **Step 3: Verify Workflow**

1. Go to **Actions** tab in your repo
2. You should see "Weekly Labor Market Refresh" workflow
3. Click **Run workflow** to test manually
4. Check the logs to confirm success

**Automated schedule:** Every Monday at 6 AM UTC

---

## 📁 **File Structure**

```
ub-labor-market/
├── index.html                          # Main dashboard (rename from ub_labor_market_dashboard_v3.html)
├── labor_market_data_v3.json           # Data file (auto-updated weekly)
├── weekly_refresh.py                   # BLS data fetcher script
├── README.md                           # This file
├── LICENSE                             # MIT License
├── .github/
│   └── workflows/
│       └── weekly_refresh.yml          # GitHub Actions automation
└── backups/                            # Auto-created by refresh script
    └── labor_market_data_v3_*.json     # Timestamped backups
```

---

## 🎨 **Accessibility Features (WCAG 2.1 AA)**

### **Keyboard Navigation**
- ✅ Skip to main content link (Tab to reveal)
- ✅ All interactive elements keyboard accessible
- ✅ Visible focus indicators (3px blue outline)
- ✅ Logical tab order

### **Screen Reader Support**
- ✅ ARIA labels on all buttons and controls
- ✅ Semantic HTML5 (header, nav, main, footer)
- ✅ Role attributes (tablist, tab, tabpanel, listitem)
- ✅ State management (aria-selected, aria-pressed, aria-hidden)

### **Visual Accessibility**
- ✅ Color contrast ratios ≥4.5:1 for text
- ✅ Color contrast ratios ≥3:1 for UI components
- ✅ Text resizable up to 200%
- ✅ No information conveyed by color alone

### **Motion & Animation**
- ✅ Respects `prefers-reduced-motion` setting
- ✅ Animations disabled for users who prefer reduced motion

---

## 🔄 **How the Automation Works**

```
┌─────────────────────────────────────────────────────────────┐
│  Every Monday at 6 AM UTC                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions triggers weekly_refresh.py                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Python script fetches latest BLS QCEW data via API         │
│  • Employment by industry (20 NAICS codes)                  │
│  • 4 regions (Baltimore, Maryland, DC, Virginia)            │
│  • 3-year rolling window (2022-2024)                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Script calculates metrics                                  │
│  • Location Quotients (LQ)                                  │
│  • Employment growth rates                                  │
│  • Regional comparisons                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Updates labor_market_data_v3.json                          │
│  • Creates timestamped backup                               │
│  • Commits to GitHub                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Pages auto-deploys updated dashboard                │
│  • Live site refreshes within 2 minutes                     │
│  • No manual intervention required                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 **Manual Refresh (Local Testing)**

```bash
# Install dependencies
pip install requests pandas

# Set your BLS API key
export BLS_API_KEY=your_key_here

# Full refresh (all 4 regions)
python weekly_refresh.py

# Single region
python weekly_refresh.py --region baltimore

# Multiple regions
python weekly_refresh.py --region baltimore dc

# Test without writing files
python weekly_refresh.py --dry-run

# Create backup before refresh
python weekly_refresh.py --backup

# Debug mode
LOG_LEVEL=DEBUG python weekly_refresh.py
```

---

## 📊 **Data Sources**

| Source | What It Provides | Update Frequency | Link |
|--------|------------------|------------------|------|
| **BLS QCEW** | Employment by industry & region | Quarterly (with lag) | [data.bls.gov/cew](https://data.bls.gov/cew/home.htm) |
| **BLS OEWS** | Occupation wages | Annual (May) | [bls.gov/oes](https://www.bls.gov/oes/) |
| **O*NET** | Occupation details, skills, tasks | Continuous | [onetonline.org](https://www.onetonline.org/) |
| **BLS Projections** | 10-year employment outlook | Biennial | [bls.gov/emp](https://www.bls.gov/emp/) |

---

## 📈 **Key Metrics Explained**

### **Location Quotient (LQ)**

**Formula:**
```
LQ = (Local Industry Employment / Local Total Employment) 
     ÷ 
     (National Industry Employment / National Total Employment)
```

**Interpretation:**
- **LQ ≥ 1.25** 🟢 **Strong** — High regional concentration (25%+ above national average)
- **LQ 1.0-1.25** 🟡 **Moderate** — Average concentration
- **LQ < 1.0** 🔴 **Below Average** — Lower than national concentration

**Example:** If Baltimore's IT industry has LQ = 1.5, it means IT represents 50% more of Baltimore's economy than it does nationally.

### **Employment Growth Rate**

**Formula:**
```
Growth Rate = ((Employment_2024 - Employment_2022) / Employment_2022) × 100
```

**Interpretation:**
- **Positive %** — Industry is growing
- **Negative %** — Industry is declining
- **>10%** — Rapid growth (strong job market)

---

## 🎯 **Use Cases**

### **For Students**
- ✅ Compare career prospects across 4 regional markets
- ✅ See median salaries for target occupations
- ✅ Identify strongest markets for your program
- ✅ Explore career paths with "Bright Outlook" designation
- ✅ Export filtered data for career planning

### **For Faculty**
- ✅ Assess program alignment with regional labor markets
- ✅ Identify curriculum enhancement opportunities
- ✅ Compare Location Quotients across all 4 regions
- ✅ Support accreditation reports with labor market data
- ✅ Make data-driven program development decisions

### **For Career Advisors**
- ✅ Real-time labor market intelligence for student advising
- ✅ Industry-specific employment trends
- ✅ Occupation demand indicators
- ✅ Regional comparison for relocation planning
- ✅ Salary negotiation data

### **For Administrators**
- ✅ Program performance metrics
- ✅ Regional market analysis for strategic planning
- ✅ Enrollment strategy insights
- ✅ Workforce development alignment

---

## 🛠️ **Customization Guide**

### **Add More Programs**

Edit `labor_market_data_v3.json`:

```json
{
  "programs": [
    {
      "program": "Your New Program",
      "school": "Your School Name",
      "degree": "BS",
      "naics": ["5415", "5416"],
      "soc": ["15-1252", "15-1256"],
      "salary": 75000,
      "outlook": "Bright Outlook",
      "alignment": {
        "baltimore": "Alignment text for Baltimore...",
        "maryland": "Alignment text for Maryland...",
        "dc": "Alignment text for DC...",
        "virginia": "Alignment text for Virginia..."
      }
    }
  ]
}
```

### **Add More Regions**

1. Edit `weekly_refresh.py` — add region to `REGIONS` dict:
```python
REGIONS = {
    "newregion": {
        "name": "New Region Name",
        "code": "CBSA XXXXX",
        "area_code": "CXXXXXXXXXXX",
        "label": "Full Region Label"
    }
}
```

2. Update `labor_market_data_v3.json` — add region data
3. Update `index.html` — add region button to all views

### **Add More Industries**

Edit `weekly_refresh.py` — add NAICS codes to `NAICS_CODES` list:
```python
NAICS_CODES = [
    "5111", "5112", "5221",  # existing
    "6214", "6215"           # new codes
]
```

### **Change Refresh Schedule**

Edit `.github/workflows/weekly_refresh.yml`:
```yaml
on:
  schedule:
    - cron: '0 6 * * 1'   # Every Monday at 6 AM UTC
    # Change to:
    - cron: '0 0 * * 0'   # Every Sunday at midnight UTC
    # Or:
    - cron: '0 12 * * 3'  # Every Wednesday at noon UTC
```

**Cron syntax:** `minute hour day-of-month month day-of-week`

---

## 🐛 **Troubleshooting**

### **Dashboard shows "Data file not found"**

**Cause:** `labor_market_data_v3.json` not in same directory as HTML file

**Fix:**
```bash
# Ensure both files are in same folder
ls -la
# Should show:
# index.html
# labor_market_data_v3.json
```

### **GitHub Actions workflow fails**

**Cause:** Missing BLS_API_KEY secret

**Fix:**
1. Go to repo → Settings → Secrets → Actions
2. Add `BLS_API_KEY` secret
3. Re-run workflow

### **Charts not rendering**

**Cause:** Chart.js CDN blocked or slow connection

**Fix:** Open browser console (F12) and check for errors. If Chart.js fails to load, download it locally:
```bash
# Download Chart.js
curl -o chart.min.js https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js

# Update index.html script tag:
<script src="chart.min.js"></script>
```

### **O*NET links not working**

**Cause:** SOC codes in JSON don't match O*NET format

**Fix:** Ensure SOC codes are 7-digit format (e.g., `15-1252`, not `15-1252.00`)

### **Region buttons don't switch data**

**Cause:** JavaScript filtering logic issue

**Fix:** Open browser console (F12) and check for errors. Ensure `labor_market_data_v3.json` has all 4 regions:
```json
{
  "regions": {
    "baltimore": { ... },
    "maryland": { ... },
    "dc": { ... },
    "virginia": { ... }
  }
}
```

---

## 📚 **Technical Specifications**

### **Frontend**
- **HTML5** with semantic markup
- **CSS3** with CSS Grid and Flexbox
- **Vanilla JavaScript** (no frameworks)
- **Chart.js 4.4.0** for visualizations
- **Zero build process** — works out of the box

### **Data Format**
- **JSON** with embedded metadata
- **BLS QCEW & OEWS** structure
- **O*NET** occupation taxonomy
- **Fully documented schema**

### **Backend Automation**
- **Python 3.12+**
- **requests** library for BLS API
- **pandas** for data processing (optional)
- **GitHub Actions** for scheduling

### **Browser Support**
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile responsive (iOS/Android)

### **Performance**
- **HTML file:** 79 KB (gzips to ~20 KB)
- **JSON file:** 52 KB (gzips to ~12 KB)
- **Load time:** <1 second on 3G
- **No backend required** — fully static

---

## 🤝 **Contributing**

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Test thoroughly** (accessibility, mobile, all browsers)
5. **Commit:** `git commit -m "Add your feature"`
6. **Push:** `git push origin feature/your-feature`
7. **Open a Pull Request**

### **Contribution Guidelines**

- ✅ Maintain WCAG 2.1 AA compliance
- ✅ Test on multiple browsers
- ✅ Update README if adding features
- ✅ Follow existing code style
- ✅ Add comments for complex logic

---

## 📄 **License**

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

**TL;DR:** You can use, modify, and distribute this dashboard freely, even commercially. Just include the original license.

---

## 🙏 **Acknowledgments**

- **Bureau of Labor Statistics** — Employment and wage data
- **O*NET Program** — Occupation details and skills data
- **University of Baltimore** — Career & Internship Center
- **Chart.js** — Data visualization library
- **GitHub** — Hosting and automation platform

---

## 📞 **Support & Contact**

### **For UB Students & Faculty**
- **Career & Internship Center:** [ubalt.edu/career](https://www.ubalt.edu/career)
- **Email:** career@ubalt.edu
- **Phone:** (410) 837-4900

### **Technical Issues**
- **GitHub Issues:** [github.com/yourusername/ub-labor-market/issues](https://github.com/yourusername/ub-labor-market/issues)
- **Documentation:** This README + inline code comments

### **Feature Requests**
Open an issue on GitHub with:
- Clear description of the feature
- Use case / benefit
- Example mockup (if applicable)

---

## 🗺️ **Roadmap**

### **v3.1 (Next Release)**
- [ ] Add more occupations (expand to 50+)
- [ ] Include all 46 UB programs
- [ ] Add salary range (25th-75th percentile)
- [ ] Export to PDF functionality

### **v3.2 (Future)**
- [ ] Interactive map visualization
- [ ] Trend analysis (5-year historical)
- [ ] Program recommendation engine
- [ ] Student portfolio integration

### **v4.0 (Long-term)**
- [ ] Real-time job posting scraper
- [ ] AI-powered career matching
- [ ] Alumni outcome tracking
- [ ] Employer partnership portal

---

## 📊 **Dashboard Statistics**

| Metric | Value |
|--------|-------|
| **Programs Tracked** | 43 |
| **Occupations Tracked** | 39 |
| **Industries Tracked** | 20 per region (80 total) |
| **Regional Markets** | 4 |
| **Data Points** | 1,200+ |
| **Update Frequency** | Weekly (automated) |
| **Accessibility Score** | WCAG 2.1 AA |
| **Load Time** | <1 second |
| **Mobile Responsive** | ✅ Yes |
| **Cost to Run** | $0/month |

---

## 🎓 **About University of Baltimore**

The University of Baltimore is a public university located in Baltimore, Maryland. UB specializes in professional programs in business, law, public affairs, and applied arts and sciences. The Career & Internship Center supports students and alumni with career planning, experiential learning, and employer engagement.

**Learn more:** [ubalt.edu](https://www.ubalt.edu)

---

## 🌟 **Star This Repo**

If you find this dashboard useful, please ⭐ star this repository on GitHub!

It helps others discover the project and motivates continued development.

---

**Built with ❤️ by the UB Career & Internship Center**

*Last updated: May 13, 2026*
