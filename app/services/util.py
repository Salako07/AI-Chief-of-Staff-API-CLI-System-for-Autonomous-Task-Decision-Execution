def resolve_task_decision_conflicts(tasks, decisions):
    task_titles = {t["title"].strip().lower() for t in tasks}

    filtered_decisions = []

    for d in decisions:
        decision_text = d["decision"].strip().lower()

        if decision_text in task_titles:
            continue  # drop duplicate task-as-decision

        filtered_decisions.append(d)

    return filtered_decisions


import re

def enrich_tasks(tasks):
    enriched = []

    for t in tasks:
        title = t.get("title", "")

        # deadline inference (safe regex only)
        if not t.get("deadline") or t["deadline"] == "none":
            match = re.search(r"(monday|tuesday|wednesday|thursday|friday)", title.lower())
            if match:
                t["deadline"] = match.group(1).capitalize()
            else:
                t["deadline"] = "none"

        # owner fix
        if not t.get("owner"):
            t["owner"] = "unassigned"

        # priority fix
        if not t.get("priority"):
            t["priority"] = "medium"

        enriched.append(t)

    return enriched



def filter_risks(risks, tasks, decisions):
    valid_keywords = set()

    for t in tasks:
        valid_keywords.add(t["title"].lower())

    for d in decisions:
        valid_keywords.add(d["decision"].lower())

    filtered = []

    for r in risks:
        text = r["risk"].lower()

        if any(k in text for k in valid_keywords):
            filtered.append(r)

    return filtered


def build_canonical_state(state):
    tasks = enrich_tasks(state.get("tasks", []))

    decisions = resolve_task_decision_conflicts(
        tasks,
        state.get("decisions", [])
    )

    risks = filter_risks(
        state.get("risks", []),
        tasks,
        decisions
    )

    return {
        "tasks": tasks,
        "decisions": decisions,
        "risks": risks
    }