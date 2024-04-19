import argparse
import os
import json
from pathlib import Path
import logging
from prettytable import PrettyTable
import subprocess
import copy

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

def time_to_human(ms: int) -> str:
    if ms >= 60 * 1000:
        return f"{ms // (60 * 1000)}m {(ms % (60 * 1000)) / 1000:.2f}s"
    if ms >= 1000:
        return f"{ms / 1000}s"
    else:
        return f"{ms}ms"

# Hacky. Hopefully temporary.
def strip_template_parameters(s: str):
    out = ""
    depth = 0
    for c in s:
        if c == '<':
            depth += 1
        elif c == '>':
            depth -= 1
        elif depth == 0:
            out += c
    return out

def strip_template_parameters_in_event(event):
    new_event = copy.deepcopy(event)
    new_event["args"]["detail"] = strip_template_parameters(new_event["args"]["detail"])
    return new_event

def print_slow(slow_entries: list[TimingEntry]):
    table = PrettyTable(border=False)
    table.field_names = ["Time", "Count", "Target"]
    table.align["Time"] = "r"
    table.align["Count"] = "l"
    table.align["Target"] = "l"
    for target in slow_entries:
        table.add_row([time_to_human(target.duration), target.count, target.name])
    print(table)

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        prog="cpp-dependency-analyzer",
        description="Analyze C++ transitive dependencies"
    )
    parser.add_argument("--project-folder", type=dir_path, required=True)
    parser.add_argument("--build-folder", type=dir_path, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--exclude-deps", type=bool, default=True)
    parser.add_argument('--exclude', action='append', nargs=1)
    parser.add_argument('--sentinel', action='append', nargs=1)
    args = parser.parse_args()

    project_folder = Path(args.project_folder)
    build_folder = Path(args.build_folder) if args.build_folder is not None else project_folder / "build"
    output_dir = Path(args.output)

    if os.path.exists(output_dir):
        assert os.path.isdir(output_dir)
    else:
        output_dir.mkdir(parents=True)

    excludes = []
    if args.exclude:
        for exclude in args.exclude:
            abspath = os.path.abspath(exclude[0])
            if os.path.isdir(abspath):
                excludes.append(abspath + os.path.sep)
            else:
                excludes.append(abspath)
    sentinels = []
    if args.sentinel:
        sentinels = [s[0] for s in args.sentinel]

    project = Project(project_folder, build_folder, excludes, sentinels)

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

    def is_tu(target: Target):
        return target.target.endswith(".o")

    def is_link(target: Target):
        return not is_tu(target)

    def is_include(event):
        return event["name"] == "Source"

    def is_instantiation(event):
        return event["name"].startswith("Instantiate")

    def is_parse(event):
        return event["name"].startswith("Parse")

    def is_codegen(event):
        return event["name"].startswith("CodeGen ")

    def is_project_include(event):
        return event["name"] == "Source" # and event["args"]["detail"].startswith(os.path.abspath(project_folder))

    print("\nSlowest translation unit targets:")
    print_slow(project.get_slow_targets(is_tu))
    print("\nSlowest link targets:")
    print_slow(project.get_slow_targets(is_link))
    print("\nFrontend/Backend:")
    print_slow(project.get_frontend_backend_totals())

    print("\nIncludes:")
    print_slow(project.get_expensive_trace_events(is_include))

    print("\nIncludes excluding children:")
    print_slow(project.get_expensive_trace_events_excluding(is_include))

    print("\nInstantiations:")
    print_slow(project.get_expensive_trace_events(is_instantiation))

    print("\nInstantiations excluding children:")
    print_slow(project.get_expensive_trace_events_excluding(is_instantiation))

    print("\nTemplates with the most total instantiation time:")
    print_slow(project.get_expensive_trace_events(is_instantiation, pre_transform=strip_template_parameters_in_event))

    print("\nTemplates with the most total instantiation time excluding children:")
    print_slow(project.get_expensive_trace_events_excluding(is_instantiation, pre_transform=strip_template_parameters_in_event))

    print("\nSlow parses:")
    print_slow(project.get_expensive_trace_events(is_parse))

    print("\nSlow parses excluding children:")
    print_slow(project.get_expensive_trace_events_excluding(is_parse))

    print("\nSlow codegen:")
    print_slow(project.get_expensive_trace_events(is_codegen))

    print("\nSlow codegen excluding children:")
    print_slow(project.get_expensive_trace_events_excluding(is_codegen))

    # print("\nIncludes in project:")
    # print_slow(project.get_expensive_trace_events(is_project_include, 30))

    # print("\nIncludes in project excluding children:")
    # print_slow(project.get_expensive_trace_events_excluding(is_project_include, 30))


main()
