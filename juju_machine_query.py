#!/usr/bin/env python3

"""
# juju_machine_query.py

* List units hosted on a given machine
* Optionally list subordinate units
* Optionally list units hosted on LXCs/LXDs
* Output results in CSV format ready to be passed to `juju run`
* Compatible with Juju 1 and Juju 2
"""

__version__ = "0.2.0"
__author__ = "Stephen Mather <stephen.mather@canonical.com>"

import argparse
import json
import re
from subprocess import check_output


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="List units hosted on a given machine."
    )
    parser.add_argument(
        "id", help="specify ID of machine to query"
    )
    parser.add_argument(
        "-c", "--csv", action="store_true",
        help="CSV output format"
    )
    parser.add_argument(
        "-l", "--lxc", action="store_true",
        help="include units hosted on LXCs/LXDs"
    )
    parser.add_argument(
        "-s", "--subordinates", action="store_true",
        help="list subordinate units, in addition to principal units"
    )
    args = parser.parse_args()
    return args


def query_juju():
    """Determine term used for software (dependent on Juju version), and obtain
    Juju status output in JSON format.
    """
    juju_version = check_output(["juju", "--version"],
                                universal_newlines=True)
    if juju_version[0] == "1":
        software = "services"
    else:
        software = "applications"
    juju_status = check_output(["juju", "status", "--format", "json"],
                               universal_newlines=True)
    status = json.loads(juju_status)
    return software, status


def query_machine(machine_id, software, status):
    """Extract machine data from Juju status JSON."""
    units = [
        {
            "principal": principal,
            "machine": status[software][app]["units"]
            [principal]["machine"],
            "subordinates": (
                status[software][app]["units"][principal]["subordinates"].keys()
                if "subordinates" in status[software][app]["units"][principal]
                else []
            )
        }
        for app in status[software]
        if "units" in status[software][app]
        for principal in status[software][app]["units"]
        if re.match(
            "^{0}$|{0}\/lx".format(machine_id),
            status[software][app]["units"][principal]["machine"]
        )
    ]
    return units


def output_results(units, machine_id, csv_format, include_lxcs,
                   include_subordinates):
    """Output query results."""
    # Filter LXCs/LXDs from unit list, if necessary.
    if include_lxcs:
        output = units
    else:
        output = [unit for unit in units if unit["machine"] == machine_id]
    output.sort(key=lambda output: output["principal"])
    if csv_format:
        values = []
        for unit in output:
            values.append(unit["principal"])
            if include_subordinates:
                values += sorted(unit["subordinates"])
        print(",".join(values))
    else:
        for unit in output:
            print("{} ({})".format(unit["principal"], unit["machine"]))
            if include_subordinates:
                subordinates = sorted(unit["subordinates"])
                for subordinate in subordinates:
                    print("  {}".format(subordinate))


def main():
    args = parse_arguments()
    software, status = query_juju()
    units = query_machine(args.id, software, status)
    output_results(units, args.id, args.csv, args.lxc, args.subordinates)


if __name__ == "__main__":
    main()
