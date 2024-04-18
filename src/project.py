import copy
from pathlib import Path
import os
import json
from dataclasses import dataclass

class Target:
    def __init__(self, build_folder: Path, start: int, end: int, restat: int, target: str, command_hash: str):
        self.build_folder = build_folder
        self.start = start # milliseconds
        self.end = end # milliseconds
        self.restat = restat
        self.target = target
        self.command_hash = command_hash
        self.tid = -1
        self.clang_trace = None

        self.load_clang_trace_events()

    def get_event(self):
        return {
            "name": os.path.basename(self.target),
            "ph": "X",
            "ts": self.start * 1000,
            "dur": (self.end - self.start) * 1000,
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
class PhonyTarget:
    start: int
    end: int
    target: str

class Project:
    def __init__(self, project_folder: Path, build_folder: Path):
        self.project_folder = project_folder
        self.build_folder = build_folder
        self.targets = []

        self.load_targets()
        self.try_to_make_thread_assignments()

    def load_targets(self):
        ninja_log = self.build_folder / ".ninja_log"
        if os.path.isfile(ninja_log):
            with open(ninja_log, "r") as f:
                header = next(f).rstrip()
                assert header == "# ninja log v5"
                for line in f:
                    start, end, restat, target, command_hash = line.split()
                    self.targets.append(
                        Target(self.build_folder, int(start), int(end), int(restat), target, command_hash)
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

    def get_slow_targets(self, n=20):
        targets = sorted(self.targets, key=lambda target: target.end - target.start, reverse=True)
        entries = targets[:n]
        if len(targets) > n:
            entries.append(
                PhonyTarget(
                    start=0,
                    end=sum(map(lambda target: target.end - target.start, targets[n:])),
                    target="Other"
                )
            )
        return entries
