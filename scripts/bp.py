#!/usr/bin/env python3
import argparse
import json
import sys
import time
import requests


def print_job_status(data):
    """Prints formatted job status."""
    print("\nJob Status:")
    print(f"  ID: {data.get('job_id')}")
    print(f"  Project: {data.get('project_name')}")
    print(f"  Type: {data.get('job_type')}")
    print(f"  Status: {data.get('status')}")
    print(f"  Created At: {data.get('created_at')}")
    if data.get("started_at"):
        print(f"  Started At: {data.get('started_at')}")
    if data.get("finished_at"):
        print(f"  Finished At: {data.get('finished_at')}")
    if data.get("result"):
        print("  Result:")
        print(f"    Findings: {len(data['result'].get('findings', []))}")
        print(f"    Output File: {data['result'].get('output_file')}")


def main():
    # Main parser
    parser = argparse.ArgumentParser(
        prog="bp",
        description="Bug Bounty Platform CLI.",
    )
    subparsers = parser.add_subparsers(dest="cmd", title="Available Commands")

    # Parser for the 'run' command
    run_parser = subparsers.add_parser(
        "run", help="Submit a new scan job (default command)"
    )
    run_parser.add_argument(
        "--api", default="http://localhost:8000", help="Backend API URL"
    )
    run_parser.add_argument("--project", required=True, help="Project name")
    run_parser.add_argument(
        "--type",
        required=True,
        choices=["attack_surface", "sca", "smart_contract"],
        help="Type of scan to run",
    )
    run_parser.add_argument(
        "--url", help="Target URL (for attack_surface) or repo path (for sca)"
    )
    run_parser.add_argument(
        "--source", help="Path to Solidity source file (for smart_contract)"
    )
    run_parser.add_argument(
        "--scope",
        nargs="*",
        default=[],
        help="Allowed domains or repositories for the scan",
    )
    run_parser.add_argument(
        "--no-accept",
        action="store_true",
        help="Do not accept terms (will cause the request to fail)",
    )
    run_parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for the job to complete and display results.",
    )

    # Parser for the 'status' command
    status_parser = subparsers.add_parser("status", help="Check the status of a job")
    status_parser.add_argument("job_id", help="The ID of the job to check")
    status_parser.add_argument(
        "--api", default="http://localhost:8000", help="Backend API URL"
    )

    # Default command logic: if no command is given, or an unknown command is given,
    # assume 'run' unless it's a help flag.
    argv = sys.argv[1:]
    if not argv or (
        argv[0] not in ("run", "status", "-h", "--help")
    ):
        argv.insert(0, "run")

    args = parser.parse_args(argv)

    if args.cmd == "status":
        # Handle 'status' command
        r = requests.get(f"{args.api}/jobs/{args.job_id}")
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching job status: {e}", file=sys.stderr)
            sys.exit(1)
        data = r.json()
        print_job_status(data)

    elif args.cmd == "run":
        # Handle 'run' command
        payload = {
            "project_name": args.project,
            "job_type": args.type,
            "accept_terms": not args.no_accept,
        }

        if args.scope:
            payload["scope"] = args.scope

        if args.type == "attack_surface":
            if not args.url:
                run_parser.error("--url is required for attack_surface")
            payload["target_url"] = args.url

        elif args.type == "sca":
            if not args.url:
                run_parser.error("--url must point to a local repo path for sca")
            payload["target_url"] = args.url

        elif args.type == "smart_contract":
            if not args.source:
                run_parser.error("--source .sol file is required for smart_contract")
            try:
                with open(args.source, "r", encoding="utf-8") as f:
                    payload["contract_source"] = f.read()
            except FileNotFoundError:
                print(f"Error: Source file not found at {args.source}", file=sys.stderr)
                sys.exit(1)

        try:
            r = requests.post(f"{args.api}/jobs", json=payload)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error submitting job: {e}", file=sys.stderr)
            sys.exit(1)

        data = r.json()
        job_id = data.get("job_id")
        project = data.get("project_name")
        print(f"Job submitted successfully for project '{project}'.")
        print(f"Job ID: {job_id}")

        if args.wait:
            spinner = "|/-\\"
            spinner_idx = 0
            print("Waiting for job to complete...", end="", flush=True)
            while True:
                print(
                    f"\rWaiting for job to complete... {spinner[spinner_idx]}",
                    end="",
                    flush=True,
                )
                spinner_idx = (spinner_idx + 1) % len(spinner)
                time.sleep(0.2)

                # Check status every 2 seconds
                if int(time.time() * 5) % 10 == 0:
                    try:
                        r = requests.get(f"{args.api}/jobs/{job_id}")
                        r.raise_for_status()
                        status_data = r.json()
                        status = status_data.get("status")

                        if status == "finished":
                            print("\rJob finished!               ")
                            print_job_status(status_data)
                            break
                        elif status not in ["pending", "running"]:
                            print(
                                f"\rJob in unexpected state: {status}", file=sys.stderr
                            )
                            break
                    except requests.exceptions.RequestException as e:
                        print(f"\rError fetching status: {e}", file=sys.stderr)
                        break
        else:
            print(f"To check status, run: bp status {job_id}")


if __name__ == "__main__":
    main()
