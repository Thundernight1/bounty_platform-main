#!/usr/bin/env python3
import argparse
import json
import sys
import requests


def main():
    parser = argparse.ArgumentParser(prog="bp", description="Bug Bounty Platform CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    runp = sub.add_parser("run", help="Start a job")
    runp.add_argument("--api", default="http://localhost:8000", help="Backend API URL")
    runp.add_argument("--project", required=True, help="Project name")
    runp.add_argument("--type", required=True, choices=["attack_surface", "sca", "smart_contract"])
    runp.add_argument("--url", help="Target URL (attack_surface) or repo path (sca)")
    runp.add_argument("--source", help="Solidity source file for smart_contract")
    runp.add_argument("--scope", nargs="*", default=[], help="Allowed domains/repos")
    runp.add_argument("--no-accept", action="store_true", help="Do not accept terms (will fail)")

    args = parser.parse_args()

    payload = {
        "project_name": args.project,
        "job_type": args.type,
        "accept_terms": not args.no_accept,
    }

    if args.scope:
        payload["scope"] = args.scope

    if args.type == "attack_surface":
        if not args.url:
            print("Error: --url is required for attack_surface", file=sys.stderr)
            sys.exit(2)
        payload["target_url"] = args.url

    if args.type == "sca":
        if not args.url:
            print("Error: --url must point to local repo path for SCA", file=sys.stderr)
            sys.exit(2)
        payload["target_url"] = args.url

    if args.type == "smart_contract":
        if not args.source:
            print("Error: --source .sol file required for smart_contract", file=sys.stderr)
            sys.exit(2)
        payload["contract_source"] = open(args.source, "r", encoding="utf-8").read()

    r = requests.post(f"{args.api}/jobs", json=payload)
    try:
        r.raise_for_status()
    except Exception:
        print(r.text, file=sys.stderr)
        sys.exit(1)

    data = r.json()
    print(json.dumps(data, indent=2))
