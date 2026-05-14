"""
weekly_refresh.py  —  UB Career & Internship Center
════════════════════════════════════════════════════
Pulls live data from two FREE federal APIs every Monday:
  1. BLS OEWS API  → median wages, employment counts (Baltimore Metro)
  2. O*NET Web Services API → skills, tasks, technology, education, outlook

Both APIs are free. Registration required:
  BLS:   https://data.bls.gov/registrationEngine/
  O*NET: https://services.onetcenter.org/developer/signup

GitHub Secrets needed (Settings → Secrets → Actions → New repository secret):
  BLS_API_KEY   → from BLS registration email
  ONET_API_KEY → from O*NET developer dashboard at services.onetcenter.org/developer/

Output: data/labor_market.json  (read by index.html on every page load)
"""

import os, json, requests, logging, time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Credentials (set as GitHub Secrets) ──────────────────────────────────────
BLS_API_KEY         = os.environ.get("BLS_API_KEY", "")
ONET_API_KEY        = os.environ.get("ONET_API_KEY", "")
SYMPLICITY_KEY      = os.environ.get("SYMPLICITY_API_KEY", "")
SYMPLICITY_BASE     = os.environ.get("SYMPLICITY_BASE_URL", "").rstrip("/")

# ── API endpoints ─────────────────────────────────────────────────────────────
BLS_URL        = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
ONET_BASE      = "https://services.onetcenter.org/ws"
ONET_CAREER    = f"{ONET_BASE}/mnm/careers"          # My Next Move career report
ONET_ONLINE    = f"{ONET_BASE}/online/occupations"   # O*NET OnLine full report

OUTPUT_FILE    = Path(__file__).parent.parent / "data" / "labor_market.json"

# ══════════════════════════════════════════════════════════════════════════════
# BLS SERIES IDs — Baltimore-Columbia-Towson MSA (CBSA 12580)
# Format: OEUM + 212113 + SOC(6 digits, no dashes) + 003 (annual median wage)
# All 39 unique occupations across all UB programs
# ══════════════════════════════════════════════════════════════════════════════
OCCUPATION_SERIES = {
    "11-1011": "OEUS000000000000111011",  # Chief Executives
    "11-1021": "OEUS000000000000111021",  # General and Operations Managers
    "11-3031": "OEUS000000000000113031",  # Financial Managers
    "11-3121": "OEUS000000000000113121",  # Human Resources Managers
    "11-9199": "OEUS000000000000119199",  # Managers, All Other
    "13-1111": "OEUS000000000000131111",  # Management Analysts
    "13-1161": "OEUS000000000000131161",  # Market Research Analysts
    "13-2011": "OEUS000000000000132011",  # Accountants and Auditors
    "13-2051": "OEUS000000000000132051",  # Financial Analysts
    "13-2052": "OEUS000000000000132052",  # Personal Financial Advisors
    "15-1211": "OEUS000000000000151211",  # Computer Systems Analysts
    "15-1212": "OEUS000000000000151212",  # Information Security Analysts
    "15-1251": "OEUS000000000000151251",  # Computer Programmers
    "15-1252": "OEUS000000000000151252",  # Software Developers
    "15-1299": "OEUS000000000000151299",  # Computer Occupations, All Other
    "19-3051": "OEUS000000000000193051",  # Urban and Regional Planners
    "21-1021": "OEUS000000000000211021",  # Child, Family, School Social Workers
    "21-1091": "OEUS000000000000211091",  # Health Education Specialists
    "23-1011": "OEUS000000000000231011",  # Lawyers
    "23-2011": "OEUS000000000000232011",  # Paralegals and Legal Assistants
    "25-1011": "OEUS000000000000251011",  # Business Teachers, Postsecondary
    "25-1066": "OEUS000000000000251066",  # Psychology Teachers, Postsecondary
    "25-1082": "OEUS000000000000251082",  # Library Science Teachers, Postsecondary
    "25-1199": "OEUS000000000000251199",  # Postsecondary Teachers, All Other
    "25-4021": "OEUS000000000000254021",  # Librarians and Media Collections Specialists
    "27-1024": "OEUS000000000000271024",  # Graphic Designers
    "27-3031": "OEUS000000000000273031",  # Public Relations Specialists
    "27-3043": "OEUS000000000000273043",  # Writers and Authors
    "29-1141": "OEUS000000000000291141",  # Registered Nurses
    "29-1171": "OEUS000000000000291171",  # Nurse Practitioners
    "29-2061": "OEUS000000000000292061",  # Licensed Practical Nurses
    "33-1012": "OEUS000000000000331012",  # First-Line Supervisors of Police
    "33-3051": "OEUS000000000000333051",  # Police and Sheriff Patrol Officers
    "41-3099": "OEUS000000000000413099",  # Sales Representatives, Services, All Other
    "43-1011": "OEUS000000000000431011",  # First-Line Supervisors of Office Workers
    "43-6011": "OEUS000000000000436011",  # Executive Secretaries
    "43-6014": "OEUS000000000000436014",  # Secretaries and Admin Assistants
    "51-9199": "OEUS000000000000519199",  # Production Workers, All Other
    "53-3032": "OEUS000000000000533032",  # Heavy and Tractor-Trailer Truck Drivers
}

# ══════════════════════════════════════════════════════════════════════════════
# OCCUPATION METADATA — static enrichment (update annually from BLS projections)
# proj_growth and talent_gap come from BLS Employment Projections (biennial)
# entry_wage and future_wage are fallbacks when BLS API returns no data
# ══════════════════════════════════════════════════════════════════════════════
OCCUPATION_META = {
    "11-1011": { "title": "Chief Executives", "entry": 129499, "future": 212749, "proj_growth": 0.19, "talent_gap": 150, "demand": "Moderate", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "11-1021": { "title": "General and Operations Managers", "entry": 73500, "future": 120749, "proj_growth": 0.05, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "11-3031": { "title": "Financial Managers", "entry": 94500, "future": 155250, "proj_growth": 0.07, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "11-3121": { "title": "Human Resources Managers", "entry": 87500, "future": 143750, "proj_growth": 0.2, "talent_gap": 150, "demand": "Moderate", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "11-9199": { "title": "Managers, All Other", "entry": 77000, "future": 126499, "proj_growth": 0.33, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "13-1111": { "title": "Management Analysts", "entry": 66500, "future": 109249, "proj_growth": 0.31, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "13-1161": { "title": "Market Research Analysts", "entry": 47600, "future": 78200, "proj_growth": 0.14, "talent_gap": 50, "demand": "Low", "naics": "5418", "industry": "Advertising, PR, and Related" },
    "13-2011": { "title": "Accountants and Auditors", "entry": 53900, "future": 88550, "proj_growth": 0.3, "talent_gap": 350, "demand": "High", "naics": "5412", "industry": "Accounting, Tax Prep, Bookkeeping" },
    "13-2051": { "title": "Financial Analysts", "entry": 66500, "future": 109249, "proj_growth": 0.23, "talent_gap": 150, "demand": "Moderate", "naics": "5412", "industry": "Accounting, Tax Prep, Bookkeeping" },
    "13-2052": { "title": "Personal Financial Advisors", "entry": 65800, "future": 108099, "proj_growth": 0.25, "talent_gap": 350, "demand": "High", "naics": "5221", "industry": "Depository Credit Intermediation" },
    "15-1211": { "title": "Computer Systems Analysts", "entry": 69300, "future": 113849, "proj_growth": 0.33, "talent_gap": 350, "demand": "High", "naics": "5415", "industry": "Computer Systems Design" },
    "15-1212": { "title": "Information Security Analysts", "entry": 78400, "future": 128799, "proj_growth": 0.33, "talent_gap": 350, "demand": "High", "naics": "5415", "industry": "Computer Systems Design" },
    "15-1251": { "title": "Computer Programmers", "entry": 65099, "future": 106949, "proj_growth": 0.13, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "15-1252": { "title": "Software Developers", "entry": 84000, "future": 138000, "proj_growth": 0.27, "talent_gap": 350, "demand": "High", "naics": "5112", "industry": "Software Publishers" },
    "15-1299": { "title": "Computer Occupations, All Other", "entry": 70000, "future": 114999, "proj_growth": 0.13, "talent_gap": 50, "demand": "Low", "naics": "5415", "industry": "Computer Systems Design" },
    "19-3051": { "title": "Urban and Regional Planners", "entry": 54600, "future": 89700, "proj_growth": 0.27, "talent_gap": 350, "demand": "High", "naics": "6242", "industry": "Community Food and Housing Services" },
    "21-1021": { "title": "Child, Family, School Social Workers", "entry": 35000, "future": 57499, "proj_growth": 0.26, "talent_gap": 350, "demand": "High", "naics": "6242", "industry": "Community Food and Housing Services" },
    "21-1091": { "title": "Health Education Specialists", "entry": 42000, "future": 69000, "proj_growth": 0.2, "talent_gap": 150, "demand": "Moderate", "naics": "6242", "industry": "Community Food and Housing Services" },
    "23-1011": { "title": "Lawyers", "entry": 94500, "future": 155250, "proj_growth": 0.32, "talent_gap": 350, "demand": "High", "naics": "6113", "industry": "Colleges, Universities, Professional Schools" },
    "23-2011": { "title": "Paralegals and Legal Assistants", "entry": 39200, "future": 64399, "proj_growth": 0.08, "talent_gap": 50, "demand": "Low", "naics": "5411", "industry": "Legal Services" },
    "25-1011": { "title": "Business Teachers, Postsecondary", "entry": 59499, "future": 97749, "proj_growth": 0.3, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "25-1066": { "title": "Psychology Teachers, Postsecondary", "entry": 57399, "future": 94299, "proj_growth": 0.05, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "25-1082": { "title": "Library Science Teachers, Postsecondary", "entry": 52500, "future": 86250, "proj_growth": 0.24, "talent_gap": 150, "demand": "Moderate", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "25-1199": { "title": "Postsecondary Teachers, All Other", "entry": 54600, "future": 89700, "proj_growth": 0.1, "talent_gap": 50, "demand": "Low", "naics": "5111", "industry": "Book and Directory Publishers" },
    "25-4021": { "title": "Librarians and Media Collections Specialists", "entry": 43400, "future": 71300, "proj_growth": 0.22, "talent_gap": 150, "demand": "Moderate", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "27-1024": { "title": "Graphic Designers", "entry": 37100, "future": 60949, "proj_growth": 0.22, "talent_gap": 150, "demand": "Moderate", "naics": "5112", "industry": "Software Publishers" },
    "27-3031": { "title": "Public Relations Specialists", "entry": 43400, "future": 71300, "proj_growth": 0.07, "talent_gap": 50, "demand": "Low", "naics": "5418", "industry": "Advertising, PR, and Related" },
    "27-3043": { "title": "Writers and Authors", "entry": 48300, "future": 79350, "proj_growth": 0.21, "talent_gap": 150, "demand": "Moderate", "naics": "5418", "industry": "Advertising, PR, and Related" },
    "29-1141": { "title": "Registered Nurses", "entry": 53900, "future": 88550, "proj_growth": 0.22, "talent_gap": 150, "demand": "Moderate", "naics": "6221", "industry": "General Medical and Surgical Hospitals" },
    "29-1171": { "title": "Nurse Practitioners", "entry": 84000, "future": 138000, "proj_growth": 0.18, "talent_gap": 150, "demand": "Moderate", "naics": "6221", "industry": "General Medical and Surgical Hospitals" },
    "29-2061": { "title": "Licensed Practical Nurses", "entry": 35000, "future": 57499, "proj_growth": 0.14, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "33-1012": { "title": "First-Line Supervisors of Police", "entry": 64399, "future": 105799, "proj_growth": 0.32, "talent_gap": 350, "demand": "High", "naics": "9221", "industry": "Justice, Public Order, Safety Activities" },
    "33-3051": { "title": "Police and Sheriff Patrol Officers", "entry": 46900, "future": 77050, "proj_growth": 0.25, "talent_gap": 350, "demand": "High", "naics": "9221", "industry": "Justice, Public Order, Safety Activities" },
    "41-3099": { "title": "Sales Representatives, Services, All Other", "entry": 43400, "future": 71300, "proj_growth": 0.16, "talent_gap": 150, "demand": "Moderate", "naics": "5418", "industry": "Advertising, PR, and Related" },
    "43-1011": { "title": "First-Line Supervisors of Office Workers", "entry": 42000, "future": 69000, "proj_growth": 0.34, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "43-6011": { "title": "Executive Secretaries", "entry": 44100, "future": 72450, "proj_growth": 0.33, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "43-6014": { "title": "Secretaries and Admin Assistants", "entry": 28000, "future": 46000, "proj_growth": 0.31, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "51-9199": { "title": "Production Workers, All Other", "entry": 26600, "future": 43700, "proj_growth": 0.31, "talent_gap": 350, "demand": "High", "naics": "5416", "industry": "Management, Scientific Consulting" },
    "53-3032": { "title": "Heavy and Tractor-Trailer Truck Drivers", "entry": 34300, "future": 56349, "proj_growth": 0.1, "talent_gap": 50, "demand": "Low", "naics": "5416", "industry": "Management, Scientific Consulting" },
}

# ══════════════════════════════════════════════════════════════════════════════
# ALL UB PROGRAMS — mapped to primary + secondary SOC codes
# ══════════════════════════════════════════════════════════════════════════════
UB_PROGRAMS = [
  # Merrick School of Business
  { "school": "Merrick School of Business",                "level": "Undergraduate", "program": "B.S. in Business Administration",                          "specializations": "Accounting, Finance, Management, Marketing, Entrepreneurship", "primary_soc": "11-1021", "secondary_soc": "13-2011", "url": "https://www.ubalt.edu/msb" },
  { "school": "Merrick School of Business",                "level": "Undergraduate", "program": "B.S. in Information Systems and Technology Management",    "specializations": "Cybersecurity, Data Analytics, IT Management",                "primary_soc": "15-1212", "secondary_soc": "15-1211", "url": "https://www.ubalt.edu/msb" },
  { "school": "Merrick School of Business",                "level": "Graduate",      "program": "M.B.A.",                                                    "specializations": "Finance, Marketing, Management, Healthcare Management",       "primary_soc": "11-1021", "secondary_soc": "13-1111", "url": "https://www.ubalt.edu/msb" },
  { "school": "Merrick School of Business",                "level": "Graduate",      "program": "M.S. in Accounting and Business Advisory Services",          "specializations": "CPA Track, Advisory Services, Forensic Accounting",          "primary_soc": "13-2011", "secondary_soc": "13-2051", "url": "https://www.ubalt.edu/msb" },
  { "school": "Merrick School of Business",                "level": "Graduate",      "program": "M.S. in Finance",                                           "specializations": "Corporate Finance, Investment Analysis",                     "primary_soc": "13-2051", "secondary_soc": "11-3031", "url": "https://www.ubalt.edu/msb" },
  { "school": "Merrick School of Business",                "level": "Graduate",      "program": "D.B.A.",                                                    "specializations": "Applied Research, Leadership, Strategy",                     "primary_soc": "11-1011", "secondary_soc": "25-1011", "url": "https://www.ubalt.edu/msb" },
  # College of Public Affairs
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.S. in Criminal Justice",                                  "specializations": "Law Enforcement, Corrections, Homeland Security",            "primary_soc": "33-1011", "secondary_soc": "23-1011", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.S. in Cyber Forensics",                                   "specializations": "Digital Forensics, Cybersecurity, Law Enforcement",          "primary_soc": "15-1212", "secondary_soc": "33-3021", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.S. in Forensic Studies",                                  "specializations": "Crime Scene Investigation, Lab Analysis",                    "primary_soc": "19-4092", "secondary_soc": "33-3021", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.A. in Government and Public Policy",                      "specializations": "Policy Analysis, Legislative Affairs",                       "primary_soc": "11-1031", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.S. in Health Management",                                 "specializations": "Healthcare Administration, Quality Improvement",             "primary_soc": "11-9111", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.A. in Human Services Administration",                     "specializations": "Nonprofit Management, Social Services, Community Dev",       "primary_soc": "11-9151", "secondary_soc": "21-1099", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.A. in Community Studies and Civic Engagement",            "specializations": "Community Organizing, Civic Leadership, Nonprofit",          "primary_soc": "11-9151", "secondary_soc": "21-1099", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Undergraduate", "program": "B.A. in International Studies",                             "specializations": "Global Affairs, Diplomacy, International Development",       "primary_soc": "11-9199", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.P.A.",                                                    "specializations": "Nonprofit, Government, Policy Analysis",                     "primary_soc": "11-1031", "secondary_soc": "13-1071", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Criminal Justice",                                  "specializations": "Policy, Administration, Research",                           "primary_soc": "33-1011", "secondary_soc": "23-1011", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Cyber Forensics",                                   "specializations": "Digital Forensics, Cybercrime Investigation",                "primary_soc": "15-1212", "secondary_soc": "33-3021", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Forensic Science — High Technology Crime",          "specializations": "Digital Evidence, Cyber Investigation",                      "primary_soc": "19-4092", "secondary_soc": "15-1212", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Health Systems Management",                         "specializations": "Healthcare Leadership, Finance, Compliance",                  "primary_soc": "11-9111", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Human Services Administration",                     "specializations": "Nonprofit Leadership, Social Services Management",           "primary_soc": "11-9151", "secondary_soc": "21-1099", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.A. in Global Affairs and Human Security",                 "specializations": "International Development, Security Policy, Diplomacy",      "primary_soc": "11-9199", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.S. in Negotiations and Conflict Management",              "specializations": "Mediation, Labor Relations, International Conflict",          "primary_soc": "23-1022", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cpa" },
  { "school": "College of Public Affairs",                 "level": "Graduate",      "program": "M.P.S. in Justice Leadership and Management",               "specializations": "Public Safety Leadership, Command Administration",            "primary_soc": "11-9199", "secondary_soc": "33-1011", "url": "https://www.ubalt.edu/cpa" },
  # Yale Gordon College of Arts & Sciences
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.S. in Applied Information Technology",                    "specializations": "Networking, Web Development, IT Support — STEM",             "primary_soc": "15-1211", "secondary_soc": "15-1244", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.S. in Artificial Intelligence for IT Operations (AIOps)", "specializations": "AI/ML Operations, Automation, Data Systems — STEM",          "primary_soc": "15-2051", "secondary_soc": "15-1212", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Digital Communication",                             "specializations": "Social Media, Digital Marketing, Content Strategy",          "primary_soc": "27-3031", "secondary_soc": "11-2011", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in English",                                           "specializations": "Writing, Editing, Publishing, Communications",               "primary_soc": "27-3043", "secondary_soc": "27-3041", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Environmental Sustainability",                      "specializations": "Environmental Policy, Sustainability — STEM",                 "primary_soc": "19-2041", "secondary_soc": "11-9199", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in History",                                           "specializations": "Law, Education, Research, Public History",                   "primary_soc": "25-4031", "secondary_soc": "23-1011", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Integrated Arts",                                   "specializations": "Visual Art, Music, Creative Writing, Arts Management",       "primary_soc": "27-1019", "secondary_soc": "11-9199", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Interdisciplinary Studies",                         "specializations": "Business, Psychology, Human Services, Digital Comm",         "primary_soc": "13-1111", "secondary_soc": "11-9151", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Legal Studies",                                     "specializations": "Pre-Law, Paralegal, Legal Research",                         "primary_soc": "23-2011", "secondary_soc": "23-1011", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Philosophy, Law, and Ethics",                       "specializations": "Pre-Law, Ethics, Public Policy, Leadership",                 "primary_soc": "23-1011", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.A. in Psychology",                                        "specializations": "Clinical, I/O Psychology, Counseling, Research",             "primary_soc": "19-3031", "secondary_soc": "13-1071", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Undergraduate", "program": "B.S. in Simulation and Game Design",                        "specializations": "3D Modeling, Animation, Coding — STEM",                     "primary_soc": "15-1251", "secondary_soc": "27-1014", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.S. in Applied Psychology — Counseling",                   "specializations": "Mental Health, Counseling, Community Psychology",            "primary_soc": "21-1014", "secondary_soc": "19-3031", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.S. in Applied Psychology — I/O Psychology",               "specializations": "Workplace Behavior, HR Analytics, Org Development",          "primary_soc": "19-3032", "secondary_soc": "11-3121", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.F.A. in Creative Writing & Publishing Arts",              "specializations": "Fiction, Nonfiction, Poetry, Book Publishing",               "primary_soc": "27-3043", "secondary_soc": "27-3041", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "D.Sc. in Information and Interaction Design",               "specializations": "UX Research, Design Systems, Human-Computer Interaction",    "primary_soc": "15-1255", "secondary_soc": "15-2051", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.F.A. in Integrated Design",                               "specializations": "Graphic Design, Brand Identity, UX/UI",                      "primary_soc": "27-1024", "secondary_soc": "15-1255", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.S. in Interaction Design and Information Architecture",    "specializations": "UX Design, Information Architecture",                        "primary_soc": "15-1255", "secondary_soc": "27-1024", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.A. in Legal and Ethical Studies",                         "specializations": "Legal Research, Ethics, Policy, Pre-Doctoral",              "primary_soc": "23-1011", "secondary_soc": "13-1041", "url": "https://www.ubalt.edu/cas" },
  { "school": "Yale Gordon College of Arts & Sciences",    "level": "Graduate",      "program": "M.A. in Publications Design",                               "specializations": "Editorial Design, Book Design, Digital Publishing",          "primary_soc": "27-1024", "secondary_soc": "27-3041", "url": "https://www.ubalt.edu/cas" },
  # School of Law
  { "school": "School of Law",                             "level": "Professional",  "program": "J.D. — Juris Doctor",                                       "specializations": "General Practice, Business, Criminal, Public Interest",      "primary_soc": "23-1011", "secondary_soc": "23-1022", "url": "https://www.ubalt.edu/law" },
  { "school": "School of Law",                             "level": "Joint Degree",  "program": "J.D. / M.B.A.",                                             "specializations": "Business Law, Corporate Finance, Entrepreneurship",           "primary_soc": "23-1011", "secondary_soc": "11-1011", "url": "https://www.ubalt.edu/law" },
  { "school": "School of Law",                             "level": "Joint Degree",  "program": "J.D. / M.S. in Criminal Justice",                           "specializations": "Criminal Law, Prosecution, Policy",                          "primary_soc": "23-1011", "secondary_soc": "33-1011", "url": "https://www.ubalt.edu/law" },
]

# ══════════════════════════════════════════════════════════════════════════════
# BLS API
# ══════════════════════════════════════════════════════════════════════════════
def bls_fetch(series_ids: list[str]) -> dict:
    if not BLS_API_KEY:
        log.warning("No BLS_API_KEY — wages will use static fallback data")
        return {}
    try:
        payload = {
            "seriesid": series_ids,
            "registrationkey": BLS_API_KEY,
            "startyear": "2022",
            "endyear": str(datetime.now().year),
            "calculations": True,
        }
        r = requests.post(BLS_URL, json=payload, timeout=30)
        r.raise_for_status()
        result = r.json()
        if result.get("status") != "REQUEST_SUCCEEDED":
            log.warning("BLS status: %s — %s", result.get("status"), result.get("message", ""))
            return {}
        found = {s["seriesID"]: s["data"] for s in result["Results"]["series"]}
        log.info("BLS: %d/%d series returned data", len(found), len(series_ids))
        return found
    except Exception as e:
        log.error("BLS fetch error: %s", e)
        return {}


def latest_bls_value(data: list) -> float | None:
    for entry in sorted(data, key=lambda x: (x["year"], x.get("period", "")), reverse=True):
        try:
            v = float(entry["value"])
            if v > 0:
                return v
        except (KeyError, ValueError):
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# O*NET Web Services API
# ══════════════════════════════════════════════════════════════════════════════
def onet_get(path: str, params: dict = None) -> dict | None:
    """Make an authenticated GET to O*NET Web Services v2.0, return JSON."""
    if not ONET_API_KEY:
        return None
    try:
        url = f"{ONET_BASE}/{path.lstrip('/')}"
        headers = {"Accept": "application/json"}
        r = requests.get(url, auth=(ONET_API_KEY, ""),
                         headers=headers, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            return None
        else:
            log.warning("O*NET %s → HTTP %d", path, r.status_code)
            return None
    except Exception as e:
        log.error("O*NET fetch error (%s): %s", path, e)
        return None


def onet_career_report(soc: str) -> dict:
    """
    Fetch the My Next Move career report for a SOC code.
    Returns a dict with: title, description, bright_outlook, tasks,
    skills, technology, education, outlook, job_postings_url
    """
    # O*NET uses XX-XXXX.00 format
    code = soc if "." in soc else soc + ".00"

    result = {
        "soc": soc,
        "onet_code": code,
        "onet_url":         f"https://www.onetonline.org/link/summary/{code}",
        "job_postings_url": f"https://www.careeronestop.org/Toolkit/Jobs/find-jobs.aspx?keyword={code}&location=Baltimore%2C%20MD",
        "mynextmove_url":   f"https://www.mynextmove.org/profile/summary/{code}",
        "bright_outlook":   False,
        "description":      "",
        "tasks":            [],
        "top_skills":       [],
        "tech_skills":      [],
        "education":        "",
        "outlook":          "",
    }

    # 1. Career overview (title, description, bright_outlook)
    overview = onet_get(f"mnm/careers/{code}")
    if overview:
        result["bright_outlook"] = overview.get("tags", {}).get("bright_outlook", False)
        result["description"]    = overview.get("what_they_do", "")[:280]

    # 2. Skills (top 5 by importance score)
    skills_data = onet_get(f"mnm/careers/{code}/skills")
    if skills_data:
        skills = skills_data.get("element", [])
        result["top_skills"] = [s["name"] for s in
                                 sorted(skills, key=lambda x: x.get("score", {}).get("value", 0), reverse=True)[:5]]

    # 3. Technology skills (hot technologies from employer job postings)
    tech_data = onet_get(f"online/occupations/{code}/summary/technology_skills")
    if tech_data:
        tech = tech_data.get("category", [])
        hot = []
        for cat in tech:
            for ex in cat.get("example", []):
                if ex.get("hot_technology"):
                    hot.append(ex.get("name", ""))
        result["tech_skills"] = hot[:6]

    # 4. Education requirements
    edu_data = onet_get(f"mnm/careers/{code}/education")
    if edu_data:
        edu = edu_data.get("education", [])
        if edu:
            # Most common education level
            top_edu = max(edu, key=lambda x: x.get("percent", 0), default=None)
            if top_edu:
                result["education"] = top_edu.get("category", "")

    # 5. Job outlook
    outlook_data = onet_get(f"mnm/careers/{code}/outlook")
    if outlook_data:
        result["outlook"] = outlook_data.get("outlook", {}).get("category", "")

    # 6. Top tasks (first 3)
    tasks_data = onet_get(f"mnm/careers/{code}/tasks")  # Not in all versions; fallback gracefully
    # Try O*NET OnLine tasks endpoint
    if not tasks_data:
        tasks_data = onet_get(f"online/occupations/{code}/summary/tasks")
    if tasks_data:
        tasks = tasks_data.get("task", tasks_data.get("element", []))
        result["tasks"] = [t.get("name", t.get("statement", "")) for t in tasks[:3]]

    time.sleep(0.25)  # Be polite to the API (rate limit: 15 req/sec)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# CareerOneStop job postings URL builder (no API key needed — direct links)
# ══════════════════════════════════════════════════════════════════════════════
def job_posting_urls(soc: str, title: str) -> dict:
    """Build direct search URLs for job postings — no API key required."""
    encoded_title = title.replace(" ", "+").replace(",", "")
    encoded_title_url = title.replace(" ", "%20")
    return {
        "careeronestop":  f"https://www.careeronestop.org/Toolkit/Jobs/find-jobs.aspx?keyword={soc}&location=Baltimore%2C+MD&radius=25",
        "usajobs":        f"https://www.usajobs.gov/Search/Results?k={encoded_title}&l=Baltimore+MD",
        "idealist":       f"https://www.idealist.org/en/jobs?q={encoded_title}&location=Baltimore+MD",
        "linkedin":       f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}&location=Baltimore%2C+Maryland",
        "indeed":         f"https://www.indeed.com/jobs?q={encoded_title_url}&l=Baltimore%2C+MD",
        "maryland_state": f"https://www.jobaps.com/MD/sup/BulList.aspx",
    }


# ══════════════════════════════════════════════════════════════════════════════
# BUILD OUTPUT
# ══════════════════════════════════════════════════════════════════════════════
def build_occupations(bls_data: dict, onet_cache: dict) -> list:
    out = []
    for soc, meta in OCCUPATION_META.items():
        # BLS wage
        series_id = OCCUPATION_SERIES.get(soc)
        median = meta["entry"] * 1.45  # fallback
        if series_id and series_id in bls_data:
            v = latest_bls_value(bls_data[series_id])
            if v:
                median = v * 1000  # BLS OEWS reports in $thousands
                log.info("  BLS live wage %s (%s): $%,.0f", soc, meta["title"], median)

        # O*NET enrichment
        onet = onet_cache.get(soc, {})

        out.append({
            "soc":              soc,
            "title":            meta["title"],
            "industry":         meta["industry"],
            "naics":            meta["naics"],
            "entry":            meta["entry"],
            "median":           round(median),
            "future":           meta["future"],
            "projGrowth":       meta["proj_growth"],
            "talentGap":        meta["talent_gap"],
            "demand":           meta["demand"],
            # O*NET fields
            "description":      onet.get("description", ""),
            "topSkills":        onet.get("top_skills", []),
            "techSkills":       onet.get("tech_skills", []),
            "education":        onet.get("education", ""),
            "brightOutlook":    onet.get("bright_outlook", False),
            "outlook":          onet.get("outlook", ""),
            "tasks":            onet.get("tasks", []),
            # Links
            "onetUrl":          onet.get("onet_url",         f"https://www.onetonline.org/link/summary/{soc}.00"),
            "myNextMoveUrl":    onet.get("mynextmove_url",   f"https://www.mynextmove.org/profile/summary/{soc}.00"),
            "jobPostings":      job_posting_urls(soc, meta["title"]),
        })
    return out


def build_programs(occupations: list) -> list:
    occ_map = {o["soc"]: o for o in occupations}
    result = []
    for p in UB_PROGRAMS:
        pri = occ_map.get(p["primary_soc"], {})
        sec = occ_map.get(p["secondary_soc"], {})
        result.append({
            **p,
            "primary_title":      pri.get("title", ""),
            "primary_median":     pri.get("median", 0),
            "primary_growth":     pri.get("projGrowth", 0),
            "primary_outlook":    pri.get("outlook", ""),
            "primary_bright":     pri.get("brightOutlook", False),
            "primary_skills":     pri.get("topSkills", []),
            "primary_tech":       pri.get("techSkills", []),
            "primary_onet_url":   pri.get("onetUrl", ""),
            "primary_jobs_url":   pri.get("jobPostings", {}).get("careeronestop", ""),
            "secondary_title":    sec.get("title", ""),
            "secondary_median":   sec.get("median", 0),
            "secondary_growth":   sec.get("projGrowth", 0),
        })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# SYMPLICITY / UBWORKS  —  Live job posting counts
# Auth: Authorization: Token <key>  (note: "Token" not "Bearer")
# Rate limit: 100 calls / 10 per second / 10,000 per 24 hours
# ══════════════════════════════════════════════════════════════════════════════

def fetch_ubworks_postings():
    """
    Pull active job posting counts from UBWorks (Symplicity CSM).
    Returns dict with total count and breakdown by job type.
    Gracefully skips if credentials are not set.
    """
    if not SYMPLICITY_BASE or not SYMPLICITY_KEY:
        log.warning("No Symplicity credentials — UBWorks posting counts skipped.")
        return {"total": 0, "by_type": {}}

    headers = {
        "Authorization": f"Token {SYMPLICITY_KEY}",
        "Accept":        "application/json",
    }

    all_jobs = []
    page     = 1

    try:
        while True:
            url    = f"{SYMPLICITY_BASE}/api/public/v1/jobs"
            params = {"status": "approved", "per_page": 500, "page": page}

            r = requests.get(url, headers=headers, params=params, timeout=30)

            if r.status_code == 401:
                log.error("Symplicity 401 Unauthorized — verify SYMPLICITY_API_KEY is correct.")
                return {"total": 0, "by_type": {}}

            if r.status_code == 404:
                log.error(f"Symplicity 404 — verify SYMPLICITY_BASE_URL is correct: {SYMPLICITY_BASE}")
                return {"total": 0, "by_type": {}}

            if r.status_code == 429:
                log.warning("Symplicity rate limit — waiting 15s and retrying.")
                time.sleep(15)
                continue

            r.raise_for_status()
            payload = r.json()

            # API may return {"data": [...]} or a bare list
            if isinstance(payload, list):
                batch = payload
            elif isinstance(payload, dict):
                batch = payload.get("data", payload.get("jobs", payload.get("results", [])))
            else:
                batch = []

            all_jobs.extend(batch)
            log.info(f"  UBWorks page {page}: {len(batch)} postings")

            # Stop paging when we get a short page
            if len(batch) < 500:
                break
            page += 1

        log.info(f"UBWorks total: {len(all_jobs)} active postings fetched")

        # Count by job type / category
        by_type = {}
        for job in all_jobs:
            category = (
                (job.get("job_type")   or {}).get("label")
                or (job.get("position_type") or {}).get("label")
                or job.get("type", "General")
            )
            by_type[category] = by_type.get(category, 0) + 1

        return {"total": len(all_jobs), "by_type": by_type}

    except requests.exceptions.ConnectionError:
        log.error(f"Symplicity connection failed — check SYMPLICITY_BASE_URL: {SYMPLICITY_BASE}")
        return {"total": 0, "by_type": {}}
    except Exception as e:
        log.error(f"Symplicity API error: {e}")
        return {"total": 0, "by_type": {}}


def main():
    log.info("═" * 60)
    log.info("UB Labor Market weekly refresh — %s", datetime.now(timezone.utc).isoformat())
    log.info("═" * 60)

    # 1. BLS — fetch all 39 wage series in one batched call
    all_series = list(OCCUPATION_SERIES.values())
    log.info("Fetching %d BLS wage series…", len(all_series))
    bls_data = bls_fetch(all_series)

    # 2. O*NET — fetch career reports for all unique SOC codes
    unique_socs = sorted(OCCUPATION_META.keys())
    onet_cache = {}
    if ONET_API_KEY:
        log.info("Fetching O*NET data for %d occupations…", len(unique_socs))
        for i, soc in enumerate(unique_socs, 1):
            log.info("  [%d/%d] O*NET %s — %s", i, len(unique_socs), soc, OCCUPATION_META[soc]["title"])
            onet_cache[soc] = onet_career_report(soc)
    else:
        log.warning("No ONET_API_KEY — O*NET enrichment skipped. Add GitHub secret ONET_API_KEY.")

    # 3. Build output
    occupations = build_occupations(bls_data, onet_cache)
    programs    = build_programs(occupations)

    # ── Fetch UBWorks (Symplicity) live posting counts ────────────────────
    ubworks = fetch_ubworks_postings()

    # ── Load current labor_market.json to preserve industries/programs/sources/formulas ──
    # The dashboard needs industries (by region), regions, sources, formulas
    # These are static from the workbook — preserve them from the existing file
    existing = {}
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE) as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    output = {
        "refreshed":    datetime.now(timezone.utc).isoformat(),
        "dataWindow":   "2022-2026",
        "regions":      existing.get("regions", ["Baltimore Metro","Maryland","DC Metro","Virginia Metro"]),
        "apiSources":   {
            "bls":        "https://www.bls.gov/developers/",
            "onet":       "https://services.onetcenter.org/",
            "symplicity": SYMPLICITY_BASE or "not configured",
        },
        "ubworks": {
            "total":   ubworks.get("total", 0),
            "by_type": ubworks.get("by_type", {}),
        },
        # Live-updated fields
        "occupations":  occupations,
        "programs":     programs,
        # Preserved static fields from existing file
        "industries":   existing.get("industries", {}),
        "sources":      existing.get("sources", []),
        "formulas":     existing.get("formulas", []),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    log.info("✓ Wrote %s — %d occupations, %d programs", OUTPUT_FILE, len(occupations), len(programs))
    log.info("  BLS live wages:  %d/%d series", len(bls_data), len(all_series))
    log.info("  O*NET records:   %d/%d occupations", len(onet_cache), len(unique_socs))


if __name__ == "__main__":
    main()
