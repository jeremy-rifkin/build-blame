import argparse
import colorama
from enum import Enum
import os
import re
import sys
import json
import math
from pathlib import Path
import logging
from prettytable import PrettyTable

from src.project import Project

def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise RuntimeError(f"Invalid file path {string}")

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise RuntimeError(f"Invalid directory {string}")

def main():
    # logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(
        prog="cpp-dependency-analyzer",
        description="Analyze C++ transitive dependencies"
    )
    parser.add_argument(
        "--project-folder",
        type=dir_path,
        required=True
    )
    parser.add_argument(
        "--build-folder",
        type=dir_path,
        required=True
    )
    parser.add_argument(
        "--output",
        required=True
    )
    parser.add_argument(
        "--exclude-deps",
        type=bool,
        default=True
    )
    args = parser.parse_args()

    build_folder = Path(args.build_folder)
    project_folder = Path(args.project_folder)
    output_dir = Path(args.output)

    if os.path.exists(output_dir):
        assert os.path.isdir(output_dir)
    else:
        output_dir.mkdir(parents=True)

    project = Project(project_folder, build_folder)

    with open(output_dir / "ninja_trace.json", "w") as f:
        f.write(json.dumps({
            "traceEvents": project.get_ninja_trace_events(),
            "displayTimeUnit": "ms",
        }))

    with open(output_dir / "full_trace.json", "w") as f:
        f.write(json.dumps({
            "traceEvents": project.get_full_trace_events(),
            "displayTimeUnit": "ms",
        }))

    slow = project.get_slow_targets()
    print("Slowest build targets:")
    table = PrettyTable(border=False)
    table.field_names = ["Time", "Target"]
    table.align["Time"] = "r"
    table.align["Target"] = "l"
    for target in slow:
        table.add_row([f"{target.end - target.start:,} ms", target.target])
    print(table)

main()
