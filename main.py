import argparse
import os
import json
from pathlib import Path
import logging
from prettytable import PrettyTable
import subprocess

from src.project import Project, Target, TimingEntry

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

def is_tu(target: Target):
    return target.target.endswith(".o")

def is_link(target: Target):
    return not is_tu(target)

def time_to_human(ms: int) -> str:
    if ms >= 60 * 1000:
        return f"{ms // (60 * 1000)}m {(ms % (60 * 1000)) / 1000:.2f}s"
    if ms >= 1000:
        return f"{ms / 1000}s"
    else:
        return f"{ms}ms"

def print_slow(slow_entries: list[TimingEntry]):
    table = PrettyTable(border=False)
    table.field_names = ["Time", "Target"]
    table.align["Time"] = "r"
    table.align["Target"] = "l"
    for target in slow_entries:
        table.add_row([time_to_human(target.duration), target.name])
    print(table)

def main():
    logging.basicConfig(level=logging.INFO)
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

    project_folder = Path(args.project_folder)
    build_folder = Path(args.build_folder) if args.build_folder is not None else project_folder / "build"
    output_dir = Path(args.output)

    if os.path.exists(output_dir):
        assert os.path.isdir(output_dir)
    else:
        output_dir.mkdir(parents=True)

    project = Project(project_folder, build_folder)

    logging.info("Writing ninja_trace.json")
    with open(output_dir / "ninja_trace.json", "w") as f:
        f.write(json.dumps({
            "traceEvents": project.get_ninja_trace_events(),
            "displayTimeUnit": "ms",
        }))

    logging.info("Writing full_trace.json")
    with open(output_dir / "full_trace.json", "w") as f:
        f.write(json.dumps({
            "traceEvents": project.get_full_trace_events(),
            "displayTimeUnit": "ms",
        }))

    logging.info("Generating includes graph")
    with open(output_dir / "includes.gv", "w") as f:
        f.write(project.dependency_analysis.generate_graphviz(project.get_target_times()))

    logging.info("Rendering includes graph")
    subprocess.run(["dot", "-Tsvg", "-o", output_dir / "includes.svg", output_dir / "includes.gv"])

    print("\nSlowest translation unit targets:")
    print_slow(project.get_slow_targets(is_tu))
    print("\nSlowest link targets:")
    print_slow(project.get_slow_targets(is_link))
    print("\nFrontend/Backend:")
    print_slow(project.get_frontend_backend_totals())




main()
