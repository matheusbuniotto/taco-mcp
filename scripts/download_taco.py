#!/usr/bin/env python3
"""Download TACO CSV from GitHub."""

import argparse
import urllib.request
from pathlib import Path


def download_taco_csv(force: bool = False) -> Path:
    """Download TACO CSV file."""
    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = raw_dir / "alimentos.csv"
    
    if csv_path.exists() and not force:
        print(f"CSV already exists at {csv_path}")
        print("Use --force to re-download")
        return csv_path
    
    url = "https://raw.githubusercontent.com/machine-learning-mocha/taco/main/tabelas/alimentos.csv"
    
    print(f"Downloading TACO CSV from {url}...")
    urllib.request.urlretrieve(url, csv_path)
    print(f"Downloaded to {csv_path}")
    
    # Check file size
    size = csv_path.stat().st_size
    print(f"File size: {size:,} bytes")
    
    return csv_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download TACO CSV")
    parser.add_argument("--force", action="store_true", help="Re-download even if exists")
    args = parser.parse_args()
    
    download_taco_csv(force=args.force)
