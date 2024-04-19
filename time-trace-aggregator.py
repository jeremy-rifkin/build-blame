import json
import copy

path = "..."

# hacky but whatever
def filter_templates(s: str):
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

def main():
    # load data
    # format: https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview#heading=h.yr4qxyxotyw
    with open(path, "r") as f:
        data = json.load(f)
    events = data["traceEvents"]

    # filter template instantiations
    instantiations = []
    for event in events:
        if event["ph"] != "X":
            continue # filter out non-complete events
        if event["name"].startswith("Instantiate"):
            instantiations.append({
                "dur": event["dur"],
                "ts": event["ts"],
                "thing": filter_templates(event["args"]["detail"]),
            })

    # do an analysis of nested events and try to exclude children time from parents
    instantiations = sorted(instantiations, key=lambda item: item["ts"])
    active_events = [] # a stack
    events = {}
    count = 0
    for item in instantiations:
        new_item = copy.deepcopy(item)
        new_item["id"] = count
        new_item["parent"] = None
        now = item["ts"]
        while len(active_events) > 0 and active_events[-1]["ts"] + active_events[-1]["dur"] <= now:
            active_events.pop()
        if len(active_events) > 0:
            new_item["parent"] = active_events[-1]["id"]
        active_events.append(new_item)
        events[count] = new_item
        count += 1
    for event in events.values():
        if event["parent"] is not None:
            events[event["parent"]]["dur"] -= event["dur"]

    # print instantiations in order of duration
    print("print instantiations in order of duration")
    instantiations = sorted(instantiations, key=lambda item: item["dur"])
    for item in instantiations:
        print(item["dur"], item["thing"])

    # aggregate instantiation times
    print('-' * 50)
    print("aggregate instantiation times")
    buckets = {}
    for item in instantiations:
        if item["thing"] not in buckets:
            buckets[item["thing"]] = 0
        buckets[item["thing"]] += item["dur"]
    for name, dur in sorted(buckets.items(), key=lambda item: item[1]):
        print(dur, name)

    # print instantiations in order of duration, excluding children
    print('-' * 50)
    print("print instantiations in order of duration, excluding children")
    instantiations = list(events.values())
    instantiations = sorted(instantiations, key=lambda item: item["dur"])
    for item in instantiations:
        print(item["dur"], item["thing"])

    # aggregate instantiation times, including children
    print('-' * 50)
    print("aggregate instantiation times, including children")
    buckets = {}
    for item in instantiations:
        if item["thing"] not in buckets:
            buckets[item["thing"]] = 0
        buckets[item["thing"]] += item["dur"]
    for name, dur in sorted(buckets.items(), key=lambda item: item[1]):
        print(dur, name)

main()
