import copy
from pathlib import Path
import os
import json
from dataclasses import dataclass
import logging

from .dependency_analysis import DependencyAnalysis, parse_search_paths

class Target:
    def __init__(self, build_folder: Path, start: int, end: int, restat: int, target: str, compile_commands_entry, command_hash: str):
        self.build_folder = build_folder
        self.start = start # milliseconds
        self.end = end # milliseconds
        self.restat = restat
        self.compile_commands_entry = compile_commands_entry
        self.target = target
        self.command_hash = command_hash
        self.tid = -1
        self.clang_trace = None

        self.load_clang_trace_events()

        self.include_path = parse_search_paths(compile_commands_entry["command"]) if compile_commands_entry is not None else None

    @property
    def duration(self):
        return self.end - self.start

    def get_name(self):
        if self.compile_commands_entry is not None:
            return self.compile_commands_entry["file"]
        else:
            return self.target

    def get_event(self):
        return {
            "name": os.path.basename(self.target),
            "ph": "X",
            "ts": self.start * 1000,
            "dur": self.duration * 1000,
            "pid": 0,
            "tid": self.tid,
            "args": {
                "target": self.target,
                "hash": self.command_hash,
            }
        }

    def load_clang_trace_events(self):
        time_trace_json = (self.build_folder / self.target).parent / (Path(self.target).stem + ".json")
        # print(time_trace_json)
        if os.path.exists(time_trace_json):
            with open(time_trace_json, "r") as f:
                self.clang_trace = json.loads(f.read())["traceEvents"]
        # else:
        #     print("Could not find", time_trace_json)

    def get_clang_trace_events(self):
        if self.clang_trace is None:
            return []
        else:
            return self.clang_trace

@dataclass
class TimingEntry:
    duration: int
    name: str

class Project:
    def __init__(self, project_folder: Path, build_folder: Path):
        self.project_folder = project_folder
        self.build_folder = build_folder
        self.targets = []
        self.exclude_deps = True

        logging.info("Loading compile commands")
        self.load_compile_commands()
        logging.info("Loading targets")
        self.load_targets()
        logging.info("Making thread assignments")
        self.try_to_make_thread_assignments()
        logging.info("Analyzing includes")
        self.analyze_includes()

    def load_compile_commands(self):
        compile_commands = self.build_folder / "compile_commands.json"
        with open(compile_commands, "r") as f:
            self.compile_commands = json.load(f)

    def get_compile_commands_for(self, target: str):
        for entry in self.compile_commands:
            if entry["output"] == target:
                return entry
        return None

    def load_targets(self):
        ninja_log = self.build_folder / ".ninja_log"
        if os.path.isfile(ninja_log):
            with open(ninja_log, "r") as f:
                header = next(f).rstrip()
                assert header == "# ninja log v5"
                for line in f:
                    start, end, restat, target, command_hash = line.split()
                    self.targets.append(
                        Target(
                            self.build_folder,
                            int(start),
                            int(end), int(restat),
                            target,
                            self.get_compile_commands_for(target),
                            command_hash
                        )
                    )
        else:
            raise RuntimeError(f"Invalid file path {ninja_log}")

    def try_to_make_thread_assignments(self):
        targets = sorted(self.targets, key=lambda target: target.start)
        busy_threads = {} # map of tid -> event end time
        free_threads = []
        current_thread_count = 0
        for target in targets:
            # advance time
            time = target.start
            for tid in list(busy_threads.keys()):
                if time >= busy_threads[tid]:
                    del busy_threads[tid]
                    free_threads.append(tid)
            # get a thread assignment
            if len(free_threads) == 0:
                target.tid = current_thread_count
                current_thread_count += 1
            else:
                free_threads = sorted(free_threads)
                target.tid = free_threads.pop(0)
            busy_threads[target.tid] = target.end

    def analyze_includes(self):
        excludes = []
        sentinels = []
        if self.exclude_deps:
            excludes.append(str(self.build_folder / "_deps"))
        dependency_analysis = DependencyAnalysis(excludes, sentinels)
        for target in self.targets:
            if target.compile_commands_entry is None:
                continue
            cpp_file = Path(target.compile_commands_entry["directory"]) / target.compile_commands_entry["file"]
            dependency_analysis.process_file(str(cpp_file), target.include_path)

        dependency_analysis.build_matrix()
        self.dependency_analysis = dependency_analysis

    def get_target_times(self):
        times = {}
        for target in self.targets:
            if target.compile_commands_entry is not None:
                cpp_file = Path(target.compile_commands_entry["directory"]) / target.compile_commands_entry["file"]
                times[str(cpp_file)] = target.duration
        return times

    def get_ninja_trace_events(self):
        return [target.get_event() for target in self.targets]

    def get_full_trace_events(self):
        events = []
        for target in self.targets:
            target_event = target.get_event()
            events.append(target_event)
            for event in target.get_clang_trace_events():
                # filters
                if event["ph"] == "M":
                    continue
                if event["name"].startswith("Total "):
                    continue
                if "dur" not in event:
                    continue

                event = copy.deepcopy(event)
                event["ts"] += target.start * 1000
                event["pid"] = 0
                event["tid"] = target_event["tid"]
                if event["ts"] + event["dur"] >= target.end * 1000:
                    event["dur"] = target.end * 1000 - event["ts"]
                events.append(event)
        return events

    def get_slow_targets(self, target_filter = lambda _: True, n=20):
        targets = filter(target_filter, self.targets)
        targets = sorted(targets, key=lambda target: target.duration, reverse=True)
        entries = list(map(lambda target: TimingEntry(target.duration, target.get_name()), targets[:n]))
        if len(targets) > n:
            entries.append(
                TimingEntry(
                    duration=sum(map(lambda target: target.duration, targets[n:])),
                    name="Other"
                )
            )
        return entries

    def get_frontend_backend_totals(self):
        frontend = 0
        backend = 0

        for target in self.targets:
            last_frontend_end = 0
            last_backend_end = 0
            for event in target.get_clang_trace_events():
                if event["name"] == "Frontend":
                    assert event["ts"] >= last_frontend_end
                    frontend += event["dur"]
                    last_frontend_end = event["ts"] + event["dur"]
                elif event["name"] == "Backend":
                    assert event["ts"] >= last_backend_end
                    backend += event["dur"]
                    last_backend_end = event["ts"] + event["dur"]

        return [TimingEntry(frontend // 1000, "Frontend"), TimingEntry(backend // 1000, "Backend")]
