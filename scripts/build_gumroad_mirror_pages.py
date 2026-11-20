#!/usr/bin/env python3
"""Build the official public site sections for Gumroad standalone HTML pages."""
import argparse
from pathlib import Path
from mirror_gumroad import PAGE_SOURCES, mirror_standalone

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for slug in PAGE_SOURCES:
        body = mirror_standalone(slug)
        path = target / (slug + ".html")
        path.write_text(body, encoding="utf-8")
        print(slug + ": " + str(len(body)) + " characters, mirrored from official website")

if __name__ == "__main__":
    main()
