import argparse
import colorama
from enum import Enum
import os
import re
import sys
import json
import math
from pathlib import Path

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

def analyze_ninja(build_folder: Path, out_dir: Path):
    ninja_log = build_folder / ".ninja_log"
    if os.path.isfile(ninja_log):
        events = []
        with open(ninja_log, "r") as f:
            header = next(f).rstrip()
            assert header == "# ninja log v5"
            for line in f:
                start, end, restat, target, hash = line.split()
                events.append({
                    "name": os.path.basename(target),
                    "ph": "X",
                    "ts": int(start) * 1000,
                    "dur": (int(end) - int(start)) * 1000,
                    "pid": 0,
                    "args": {
                        "target": target,
                        "hash": hash,
                    }
                })
        events = sorted(events, key=lambda event: event["ts"])
        # try to make thread assignments
        busy_threads = {} # map of tid -> event end time
        free_threads = []
        current_thread_count = 0
        for event in events:
            # advance time
            time = event["ts"]
            for tid in list(busy_threads.keys()):
                if time >= busy_threads[tid]:
                    del busy_threads[tid]
                    free_threads.append(tid)
            # get a thread assignment
            if len(free_threads) == 0:
                event["tid"] = current_thread_count
                current_thread_count += 1
            else:
                free_threads = sorted(free_threads)
                event["tid"] = free_threads.pop(0)
            busy_threads[event["tid"]] = event["ts"] + event["dur"]

        with open(out_dir / "ninja_trace.json", "w") as f:
            f.write(json.dumps({
                "traceEvents": events,
                "displayTimeUnit": "ms",
                # "beginningOfTime": 1713322015028770
            }))
    else:
        raise RuntimeError(f"Invalid file path {ninja_log}")

def main():
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
    args = parser.parse_args()

    build_folder = Path(args.build_folder)
    project_folder = Path(args.project_folder)
    output_dir = Path(args.output)

    output_dir.mkdir(parents=True)

    analyze_ninja(build_folder, output_dir)


main()
