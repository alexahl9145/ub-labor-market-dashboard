"""
weekly_refresh.py
Fetches BLS OEWS wages weekly, merges with static enrichment data,
and writes data/labor_market.json for the UB dashboard to consume.

Setup:
  1. Get a free BLS API key at https://data.bls.gov/registrationEngine/
  2. Add it as a GitHub secret named BLS_API_KEY
  3. This script runs automatically via .github/workflows/weekly_refresh.yml
"""

import os, json, requests, logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

BLS_API_KEY = os.environ.get("BLS_API_KEY", "")
BLS_URL     = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "labor_market.json"

# BLS Series IDs for Baltimore Metro (CBSA 12580)
# Replace with real series from https://www.bls.gov/oes/
OCCUPATION_SERIES = {
    "11-1021": "OEUM212113111021003",  # General and Operations Managers
    "13-2011": "OEUM212113132011003",  # Accountants and Auditors
    "15-1212": "OEUM212113151212003",  # Information Security Analysts
    "15-1211": "OEUM212113151211003",  # Computer Systems Analysts
    "13-1111": "OEUM212113131111003",  # Management Analysts
    "13-2051": "OEUM212113132051003",  # Financial and Investment Analysts
    "11-3031": "OEUM212113113031003",  # Financial Managers
    "11-1011": "OEUM212113111011003",  # Chief Executives
    "25-1011": "OEUM212113251011003",  # Business Teachers, Postsecondary
    "33-1011": "OEUM212113331011003",  # First-Line Supervisors of Police
    "23-1011": "OEUM212113231011003",  # Lawyers
    "33-3021": "OEUM212113333021003",  # Detectives and Criminal Investigators
    "19-4092": "OEUM212113194092003",  # Forensic Science Technicians
    "11-1031": "OEUM212113111031003",  # Legislators
    "13-1041": "OEUM212113131041003",  # Compliance Officers
    "11-9111": "OEUM212113119111003",  # Medical and Health Services Managers
    "11-9151": "OEUM212113119151003",  # Social and Community Service Managers
    "21-1099": "OEUM212113211099003",  # Community and Social Service Specialists
    "11-9199": "OEUM212113119199003",  # Managers, All Other (Intl Affairs)
    "13-1071": "OEUM212113131071003",  # Human Resources Specialists
    "23-1022": "OEUM212113231022003",  # Arbitrators, Mediators, Conciliators
    "15-1244": "OEUM212113151244003",  # Network and Computer Systems Admins
    "15-2051": "OEUM212113152051003",  # Data Scientists
    "27-3031": "OEUM212113273031003",  # Public Relations Specialists
    "11-2011": "OEUM212113112011003",  # Advertising and Promotions Managers
    "27-3043": "OEUM212113273043003",  # Writers and Authors
    "27-3041": "OEUM212113273041003",  # Editors
    "19-2041": "OEUM212113192041003",  # Environmental Scientists and Specialists
    "25-4031": "OEUM212113254031003",  # Library Technicians / Archivists
    "27-1019": "OEUM212113271019003",  # Artists and Related Workers
    "23-2011": "OEUM212113232011003",  # Paralegals and Legal Assistants
    "19-3031": "OEUM212113193031003",  # Clinical and Counseling Psychologists
    "15-1251": "OEUM212113151251003",  # Computer Programmers
    "27-1014": "OEUM212113271014003",  # Special Effects Artists and Animators
    "21-1014": "OEUM212113211014003",  # Mental Health Counselors
    "19-3032": "OEUM212113193032003",  # Industrial-Organizational Psychologists
    "11-3121": "OEUM212113113121003",  # Human Resources Managers
    "15-1255": "OEUM212113151255003",  # Web and Digital Interface Designers
    "27-1024": "OEUM212113271024003",  # Graphic Designers
}

OCCUPATION_META = {
    "15-1212": {
        "title": "Information Security Analysts",
        "industry": "Computer Systems Design & Related Services",
        "education": "Bachelor's degree",
        "skills": "Cybersecurity, Risk management, Cloud security",
        "entry_wage": 85000, "future_wage": 132000,
        "proj_growth": 0.250, "post_intensity": 0.272, "talent_gap": 480,
        "demand": "High", "naics": "5415"
    },
    "13-1111": {
        "title": "Management Analysts",
        "industry": "Mgmt, Scientific & Technical Consulting",
        "education": "Bachelor's degree",
        "skills": "Data analysis, Process improvement, Project management",
        "entry_wage": 72000, "future_wage": 109000,
        "proj_growth": 0.115, "post_intensity": 0.230, "talent_gap": 500,
        "demand": "High", "naics": "5416"
    },
    "11-9111": {
        "title": "Medical & Health Services Managers",
        "industry": "General Medical & Surgical Hospitals",
        "education": "Bachelor's degree",
        "skills": "Healthcare operations, Budgeting, Compliance",
        "entry_wage": 79000, "future_wage": 124000,
        "proj_growth": 0.233, "post_intensity": 0.207, "talent_gap": 320,
        "demand": "High", "naics": "6221"
    },
    "13-1071": {
        "title": "Human Resources Specialists",
        "industry": "Administration of Human Resource Programs",
        "education": "Bachelor's degree",
        "skills": "Recruiting, Employee relations, HRIS",
        "entry_wage": 52000, "future_wage": 79000,
        "proj_growth": 0.058, "post_intensity": 0.163, "talent_gap": 100,
        "demand": "High", "naics": "9231"
    },
    "25-9031": {
        "title": "Instructional Coordinators",
        "industry": "Colleges, Universities & Professional Schools",
        "education": "Master's degree",
        "skills": "Curriculum design, Assessment, Training",
        "entry_wage": 58000, "future_wage": 85000,
        "proj_growth": 0.060, "post_intensity": 0.144, "talent_gap": 40,
        "demand": "High", "naics": "6113"
    },
}

INDUSTRY_META = {
    "5415": {"name": "Computer Systems Design", "lq": 0.81, "reg_growth": 23.3, "nat_growth": 20.0, "emp_end": 18500},
    "6221": {"name": "General Medical Hospitals", "lq": 0.96, "reg_growth": 8.3,  "nat_growth": 5.6,  "emp_end": 45500},
    "9231": {"name": "Admin of HR Programs",      "lq": 1.21, "reg_growth": 9.8,  "nat_growth": 5.9,  "emp_end": 9000},
    "5416": {"name": "Mgmt & Tech Consulting",    "lq": 1.59, "reg_growth": 19.0, "nat_growth": 18.8, "emp_end": 25000},
    "6113": {"name": "Colleges & Universities",   "lq": 1.23, "reg_growth": -2.2, "nat_growth": 1.2,  "emp_end": 17600},
}

PROGRAMS = [
    {"name": "B.S. Business Administration",          "cred": "Bachelor's", "college": "Merrick School of Business",
     "industry": "Mgmt & Tech Consulting",             "occ": "Management Analysts",       "naics": "5416", "soc": "13-1111", "fit": "High"},
    {"name": "B.S. Information Systems & Technology", "cred": "Bachelor's", "college": "College of Arts & Sciences",
     "industry": "Computer Systems Design",            "occ": "Information Security Analysts", "naics": "5415", "soc": "15-1212", "fit": "Strategic"},
    {"name": "M.P.A.",                                "cred": "Master's",   "college": "College of Public Affairs",
     "industry": "Admin of HR Programs",              "occ": "Human Resources Specialists", "naics": "9231", "soc": "13-1071", "fit": "Moderate"},
    {"name": "M.S. Health Systems Management",        "cred": "Master's",   "college": "College of Public Affairs",
     "industry": "General Medical Hospitals",         "occ": "Medical & Health Services Managers", "naics": "6221", "soc": "11-9111", "fit": "High"},
]


def bls_fetch(series_ids):
    if not BLS_API_KEY:
        log.warning("No BLS_API_KEY set — using static data")
        return {}
    try:
        payload = {"seriesid": series_ids, "registrationkey": BLS_API_KEY,
                   "startyear": "2023", "endyear": str(datetime.now().year), "calculations": True}
        r = requests.post(BLS_URL, json=payload, timeout=30)
        r.raise_for_status()
        result = r.json()
        if result.get("status") != "REQUEST_SUCCEEDED":
            log.warning("BLS status: %s", result.get("status"))
            return {}
        return {s["seriesID"]: s["data"] for s in result["Results"]["series"]}
    except Exception as e:
        log.error("BLS fetch error: %s", e)
        return {}


def latest_value(data):
    for entry in sorted(data, key=lambda x: (x["year"], x.get("period", "")), reverse=True):
        try:
            return float(entry["value"])
        except (KeyError, ValueError):
            continue
    return None


def build_occupations(bls_data):
    out = []
    for soc, meta in OCCUPATION_META.items():
        sid = OCCUPATION_SERIES.get(soc)
        median = meta["entry_wage"] * 1.45
        if sid and sid in bls_data:
            v = latest_value(bls_data[sid])
            if v:
                median = v * 1000
                log.info("Live BLS wage %s: $%,.0f", soc, median)
        out.append({
            "title": meta["title"], "industry": meta["industry"],
            "entry": meta["entry_wage"], "median": round(median), "future": meta["future_wage"],
            "projGrowth": meta["proj_growth"], "postIntensity": meta["post_intensity"],
            "talentGap": meta["talent_gap"], "demand": meta["demand"],
            "education": meta["education"], "skills": meta["skills"],
            "naics": meta["naics"], "soc": soc,
        })
    return out


def build_industries():
    return [{"name": m["name"], "naics": n, "lq": m["lq"],
             "regGrowth": m["reg_growth"], "natGrowth": m["nat_growth"], "empEnd": m["emp_end"]}
            for n, m in INDUSTRY_META.items()]


def build_programs(occupations, industries):
    occ_map = {o["soc"]: o for o in occupations}
    ind_map = {i["naics"]: i for i in industries}
    out = []
    for p in PROGRAMS:
        occ = occ_map.get(p["soc"], {})
        ind = ind_map.get(p["naics"], {})
        out.append({**p, "lq": ind.get("lq", 0),
                    "indGrowth": ind.get("regGrowth", 0),
                    "occGrowth": round(occ.get("projGrowth", 0) * 100, 1)})
    return out


def main():
    log.info("Weekly refresh started — %s", datetime.now(timezone.utc).isoformat())
    bls_data = bls_fetch(list(OCCUPATION_SERIES.values()))
    occupations = build_occupations(bls_data)
    industries  = build_industries()
    programs    = build_programs(occupations, industries)
    output = {
        "refreshed": datetime.now(timezone.utc).isoformat(),
        "region": "Baltimore Metro",
        "dataWindow": "2021–2026",
        "occupations": occupations,
        "industries": industries,
        "programs": programs,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    log.info("Wrote %s — %d occupations, %d industries, %d programs",
             OUTPUT_FILE, len(occupations), len(industries), len(programs))


if __name__ == "__main__":
    main()
