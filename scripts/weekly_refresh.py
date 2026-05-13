#!/usr/bin/env python3
"""
UB Labor Market Dashboard — Weekly BLS Data Refresh Script
University of Baltimore · Career & Internship Center
Version: 3.0 | WCAG 2.1 AA Compliant Dashboard Support

Usage:
    python weekly_refresh.py                    # Full refresh all regions
    python weekly_refresh.py --region baltimore # Single region
    python weekly_refresh.py --dry-run          # Validate without writing
    python weekly_refresh.py --backup           # Backup before refresh

Environment Variables:
    BLS_API_KEY     Your BLS API registration key (required for higher rate limits)
    DATA_FILE       Path to labor_market_data_v3.json (default: ./labor_market_data_v3.json)
    LOG_LEVEL       Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
"""

import os
import sys
import json
import time
import logging
import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

BLS_API_BASE = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_API_KEY = os.environ.get("BLS_API_KEY", "")
DATA_FILE = os.environ.get("DATA_FILE", "labor_market_data_v3.json")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
BACKUP_DIR = Path("./backups")
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries
REQUEST_DELAY = 1  # seconds between API calls (rate limiting)

# Region configurations
REGIONS = {
    "baltimore": {
        "name": "Baltimore Metro",
        "code": "CBSA 12580",
        "area_code": "C1258000000000",  # BLS QCEW area code
        "label": "Baltimore-Columbia-Towson, MD"
    },
    "maryland": {
        "name": "Maryland",
        "code": "State 24",
        "area_code": "S2400000000000",
        "label": "Maryland Statewide"
    },
    "dc": {
        "name": "DC Metro",
        "code": "CBSA 47900",
        "area_code": "C4790000000000",
        "label": "Washington-Arlington-Alexandria, DC-VA-MD-WV"
    },
    "virginia": {
        "name": "Virginia Metro",
        "code": "CBSA 40060",
        "area_code": "C4006000000000",
        "label": "Richmond, VA"
    }
}

# NAICS codes tracked (20 industries)
NAICS_CODES = [
    "5111", "5112", "5221", "5411", "5412", "5414", "5415", "5416",
    "5418", "5500", "6113", "6211", "6221", "6242", "7111",
    "9211", "9221", "9231", "9241", "9281"
]

# ═════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
log = logging.getLogger("ub_refresh")

# ═════════════════════════════════════════════════════════════════════════════
# BLS API CLIENT
# ═════════════════════════════════════════════════════════════════════════════

class BLSClient:
    """BLS Public API v2 client with retry logic and rate limiting."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if api_key:
            log.info("✅ BLS API key loaded — higher rate limits enabled (50 series/request)")
        else:
            log.warning("⚠️  No BLS_API_KEY found — limited to 25 series/request, 500/day")
            log.warning("   Register free at: https://api.bls.gov/registrationEngine/")

    def fetch_series(self, series_ids: List[str], start_year: int, end_year: int) -> Dict:
        """
        Fetch multiple series from BLS API with retry logic.
        Returns dict keyed by series ID.
        """
        results = {}
        
        # Chunk into batches (25 without key, 50 with key)
        batch_size = 50 if self.api_key else 25
        batches = [series_ids[i:i+batch_size] for i in range(0, len(series_ids), batch_size)]

        for batch_num, batch in enumerate(batches, 1):
            log.info(f"  📊 Fetching batch {batch_num}/{len(batches)} ({len(batch)} series)...")

            payload = {
                "seriesid": batch,
                "startyear": str(start_year),
                "endyear": str(end_year),
                "annualaverage": True
            }
            if self.api_key:
                payload["registrationkey"] = self.api_key

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    resp = self.session.post(BLS_API_BASE, json=payload, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("status") == "REQUEST_SUCCEEDED":
                        for series in data.get("Results", {}).get("series", []):
                            results[series["seriesID"]] = series.get("data", [])
                        log.info(f"     ✅ Batch {batch_num} successful")
                        break
                    elif data.get("status") == "REQUEST_FAILED":
                        msgs = "; ".join(data.get("message", ["Unknown error"]))
                        log.error(f"     ❌ BLS API error: {msgs}")
                        if attempt == MAX_RETRIES:
                            raise RuntimeError(f"BLS API failed after {MAX_RETRIES} attempts: {msgs}")
                    else:
                        log.warning(f"     ⚠️  Unexpected status: {data.get('status')}")

                except requests.exceptions.Timeout:
                    log.warning(f"     ⏱️  Timeout on attempt {attempt}/{MAX_RETRIES}")
                    if attempt == MAX_RETRIES:
                        raise
                    time.sleep(RETRY_DELAY * attempt)

                except requests.exceptions.HTTPError as e:
                    log.error(f"     🔴 HTTP error: {e}")
                    if attempt == MAX_RETRIES:
                        raise
                    time.sleep(RETRY_DELAY * attempt)

                except Exception as e:
                    log.error(f"     💥 Unexpected error: {e}")
                    if attempt == MAX_RETRIES:
                        raise
                    time.sleep(RETRY_DELAY * attempt)

            time.sleep(REQUEST_DELAY)  # Rate limiting between batches

        return results

    def get_annual_value(self, series_data: List, year: int) -> Optional[float]:
        """Extract annual average value for a specific year from series data."""
        for entry in series_data:
            if entry.get("year") == str(year) and entry.get("period") == "M13":
                try:
                    return float(entry["value"].replace(",", ""))
                except (ValueError, KeyError):
                    return None
        return None

# ═════════════════════════════════════════════════════════════════════════════
# LOCATION QUOTIENT CALCULATOR
# ═════════════════════════════════════════════════════════════════════════════

def calculate_lq(
    local_industry_emp: float,
    local_total_emp: float,
    national_industry_emp: float,
    national_total_emp: float
) -> Optional[float]:
    """
    Location Quotient = (Local Industry % of Local Total) / (National Industry % of National Total)
    LQ > 1.25 = Strong concentration
    LQ 1.0-1.25 = Moderate concentration
    LQ < 1.0 = Below average
    """
    try:
        if local_total_emp <= 0 or national_total_emp <= 0 or national_industry_emp <= 0:
            return None
        local_share = local_industry_emp / local_total_emp
        national_share = national_industry_emp / national_total_emp
        if national_share <= 0:
            return None
        return round(local_share / national_share, 2)
    except (ZeroDivisionError, TypeError):
        return None

def calculate_growth_rate(emp_start: float, emp_end: float) -> Optional[float]:
    """Calculate employment growth rate between two periods."""
    try:
        if emp_start <= 0:
            return None
        return round(((emp_end - emp_start) / emp_start) * 100, 1)
    except (ZeroDivisionError, TypeError):
        return None

# ═════════════════════════════════════════════════════════════════════════════
# DATA UPDATER
# ═════════════════════════════════════════════════════════════════════════════

class DashboardDataUpdater:
    """Orchestrates fetching, computing, and writing dashboard data."""

    def __init__(self, data_file: str, dry_run: bool = False):
        self.data_file = Path(data_file)
        self.dry_run = dry_run
        self.client = BLSClient(BLS_API_KEY)
        self.current_year = datetime.now().year
        self.start_year = self.current_year - 3

        # Load existing data
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Load existing JSON data file."""
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info(f"📂 Loaded existing data from {self.data_file}")
            return data
        else:
            log.error(f"❌ Data file not found: {self.data_file}")
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

    def backup(self):
        """Create timestamped backup of current data file."""
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"labor_market_data_v3_{timestamp}.json"
        shutil.copy2(self.data_file, backup_path)
        log.info(f"💾 Backup created: {backup_path}")
        return backup_path

    def refresh_region(self, region_key: str) -> dict:
        """Fetch and recompute data for a single region."""
        region_config = REGIONS[region_key]
        log.info(f"\n{'='*60}")
        log.info(f"🔄 Refreshing: {region_config['name']} ({region_config['code']})")
        log.info(f"{'='*60}")

        # Build QCEW series IDs
        # Format: ENU + area_code + ownership + size + industry
        # We use ownership=1 (private), size=0 (all sizes)
        area_code = region_config["area_code"]
        series_ids = []
        national_ids = []

        for naics in NAICS_CODES:
            # Local series
            local_id = f"ENU{area_code}10{naics.ljust(6, '0')}"
            series_ids.append(local_id)
            
            # National series for LQ calculation
            national_id = f"ENUC000000010{naics.ljust(6, '0')}"
            national_ids.append(national_id)

        all_series = series_ids + list(set(national_ids))
        
        # Add total employment series (NAICS 10 = all industries)
        local_total_id = f"ENU{area_code}1010------"
        national_total_id = "ENUC0000000101------"
        all_series.extend([local_total_id, national_total_id])

        log.info(f"📡 Fetching {len(all_series)} QCEW series from BLS API...")

        try:
            results = self.client.fetch_series(
                all_series,
                start_year=self.start_year,
                end_year=self.current_year
            )
        except Exception as e:
            log.error(f"❌ Failed to fetch data for {region_key}: {e}")
            return {}

        # Get total employment for LQ calculation
        local_total = self.client.get_annual_value(
            results.get(local_total_id, []), 
            self.current_year - 1
        )
        national_total = self.client.get_annual_value(
            results.get(national_total_id, []), 
            self.current_year - 1
        )

        # Process results into industry records
        industries_updated = []
        existing_industries = self.data.get("regions", {}).get(region_key, {}).get("industries", [])

        for i, naics in enumerate(NAICS_CODES):
            local_id = f"ENU{area_code}10{naics.ljust(6, '0')}"
            national_id = f"ENUC000000010{naics.ljust(6, '0')}"

            local_data = results.get(local_id, [])
            national_data = results.get(national_id, [])

            local_emp_current = self.client.get_annual_value(local_data, self.current_year - 1)
            local_emp_prior = self.client.get_annual_value(local_data, self.start_year)
            national_emp = self.client.get_annual_value(national_data, self.current_year - 1)

            # Find existing industry record to preserve name and other fields
            existing = next((ind for ind in existing_industries if ind.get("naics") == naics), {})

            lq = None
            growth = None
            
            if all(v is not None and v > 0 for v in [local_emp_current, local_total, national_emp, national_total]):
                lq = calculate_lq(local_emp_current, local_total, national_emp, national_total)
            
            if local_emp_prior and local_emp_current:
                growth = calculate_growth_rate(local_emp_prior, local_emp_current)

            industries_updated.append({
                "naics": naics,
                "name": existing.get("name", f"NAICS {naics}"),
                "employment": int(local_emp_current) if local_emp_current else existing.get("employment"),
                "lq": lq if lq is not None else existing.get("lq"),
                "growth": growth if growth is not None else existing.get("growth"),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })

        log.info(f"✅ Updated {len(industries_updated)} industries for {region_config['name']}")
        return {"industries": industries_updated}

    def refresh_all(self, regions: Optional[List[str]] = None):
        """Refresh all (or specified) regions."""
        target_regions = regions or list(REGIONS.keys())
        
        log.info(f"\n{'='*70}")
        log.info(f"🎓 UB Labor Market Dashboard — Weekly BLS Refresh")
        log.info(f"{'='*70}")
        log.info(f"⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
        log.info(f"🗺️  Target regions: {', '.join(target_regions)}")
        log.info(f"🧪 Dry run: {self.dry_run}")
        log.info(f"{'='*70}\n")

        updated_regions = {}
        errors = []

        for region_key in target_regions:
            if region_key not in REGIONS:
                log.warning(f"⚠️  Unknown region key: {region_key} — skipping")
                continue
            try:
                region_data = self.refresh_region(region_key)
                if region_data:
                    updated_regions[region_key] = region_data
            except Exception as e:
                log.error(f"❌ Error refreshing {region_key}: {e}")
                errors.append({"region": region_key, "error": str(e)})

        # Merge updates into existing data
        if "regions" not in self.data:
            self.data["regions"] = {}

        for region_key, region_data in updated_regions.items():
            if region_key not in self.data["regions"]:
                self.data["regions"][region_key] = {}
            self.data["regions"][region_key].update(region_data)

        # Update metadata
        self.data["metadata"] = {
            **self.data.get("metadata", {}),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "refresh_version": "3.0",
            "regions_updated": list(updated_regions.keys()),
            "errors": errors,
            "data_years": {
                "start": self.start_year,
                "end": self.current_year - 1
            }
        }

        if self.dry_run:
            log.info(f"\n{'='*70}")
            log.info("🧪 [DRY RUN] No files written.")
            log.info(f"   Would update {len(updated_regions)} regions")
            log.info(f"   {len(errors)} error(s) encountered")
            log.info(f"{'='*70}")
        else:
            self._write_data()
            log.info(f"\n{'='*70}")
            log.info(f"✅ Refresh complete!")
            log.info(f"   Updated {len(updated_regions)} region(s)")
            if errors:
                log.warning(f"   ⚠️  {len(errors)} region(s) had errors: {[e['region'] for e in errors]}")
            log.info(f"{'='*70}")

        return {"updated": len(updated_regions), "errors": errors}

    def _write_data(self):
        """Write updated data back to JSON file."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        size_kb = self.data_file.stat().st_size / 1024
        log.info(f"💾 Data written to {self.data_file}")
        log.info(f"   File size: {size_kb:.1f} KB")

# ═════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═════════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="UB Labor Market Dashboard — Weekly BLS Data Refresh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python weekly_refresh.py                          # Full refresh all 4 regions
  python weekly_refresh.py --region baltimore       # Baltimore Metro only
  python weekly_refresh.py --region baltimore dc    # Multiple regions
  python weekly_refresh.py --dry-run                # Validate without writing
  python weekly_refresh.py --backup                 # Backup before refresh

Available region keys: baltimore, maryland, dc, virginia
        """
    )
    parser.add_argument(
        "--region", nargs="+", choices=list(REGIONS.keys()),
        help="Region(s) to refresh (default: all)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch data but do not write to file"
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create timestamped backup before writing"
    )
    parser.add_argument(
        "--data-file", default=DATA_FILE,
        help=f"Path to data JSON file (default: {DATA_FILE})"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    updater = DashboardDataUpdater(
        data_file=args.data_file,
        dry_run=args.dry_run
    )

    if args.backup and not args.dry_run:
        updater.backup()

    result = updater.refresh_all(regions=args.region)

    # Exit with error code if any regions failed
    sys.exit(1 if result["errors"] else 0)

if __name__ == "__main__":
    main()
