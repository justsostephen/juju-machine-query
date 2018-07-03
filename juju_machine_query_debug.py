#!/usr/bin/env python3

"""
# juju_machine_query.py

Copyright (C) 2017 Canonical Ltd.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License version 3, as published by the Free
Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <https://www.gnu.org/licenses/>.


## Notes

* juju 1.x: services; juju 2.x applications
"""

__version__ = "0.1.0"
__author__ = "Stephen Mather <stephen.mather@canonical.com>"

import argparse
import json
import re
from subprocess import check_output

SOFTWARE = "services"
# JUJU_VERSION = check_output(["juju", "--version"],
#                             universal_newlines=True)
# if JUJU_VERSION[0] == "1":
#     SOFTWARE = "services"
# else:
#     SOFTWARE = "applications"
STATUS = json.load(open("status-juju1.json"))
# JUJU_STATUS = check_output(["juju", "status", "--format", "json"],
#                            universal_newlines=True)
# STATUS = json.loads(JUJU_STATUS)


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
        help="include units hosted on LXCs"
    )
    parser.add_argument(
        "-s", "--subordinates", action="store_true",
        help="list subordinate units, in addition to principal units"
    )
    args = parser.parse_args()
    return args


def output_results(machine_id, csv_format, include_lxcs, include_subordinates):
    units = query_machine(machine_id)
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


def query_machine(machine_id):
    units = [
        {
            "principal": principal,
            "machine": STATUS[SOFTWARE][app]["units"]
            [principal]["machine"],
            "subordinates": (
                STATUS[SOFTWARE][app]["units"][principal]["subordinates"].keys()
                if "subordinates" in STATUS[SOFTWARE][app]["units"][principal]
                else []
            )
        }
        for app in STATUS[SOFTWARE]
        if "units" in STATUS[SOFTWARE][app]
        for principal in STATUS[SOFTWARE][app]["units"]
        if re.match(
            "^{0}$|{0}\/lxc".format(machine_id),
            STATUS[SOFTWARE][app]["units"][principal]["machine"]
        )
    ]
    return units
    # # Non-comprehension.
    # units = []
    # for app in STATUS[SOFTWARE]:
    #     if "units" in STATUS[SOFTWARE][app]:
    #         for principal in STATUS[SOFTWARE][app]["units"]:
    #             if re.match(
    #                     "^{0}$|{0}\/lxc".format(machine_id),
    #                     STATUS[SOFTWARE][app]
    #                     ["units"][principal]["machine"]):
    #                 units.append({
    #                     "principal": principal,
    #                     "machine": STATUS[SOFTWARE][app]["units"]
    #                     [principal]["machine"]
    #                 })
    #                 if ("subordinates" in STATUS[SOFTWARE]
    #                         [app]["units"][principal]):
    #                     units[-1]["subordinates"] = (
    #                         STATUS[SOFTWARE][app]["units"][principal]
    #                         ["subordinates"].keys()
    #                     )
    # return units


def main():
    args = parse_arguments()
    output_results(args.id, args.csv, args.lxc, args.subordinates)


if __name__ == "__main__":
    main()
