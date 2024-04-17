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

from src.dependency_analysis import analyze_project
from src.ninja_trace import analyze_ninja

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

    analyze_ninja(build_folder, output_dir)
    analyze_project(build_folder, output_dir, args.exclude_deps)


main()
