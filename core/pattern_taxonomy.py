from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PatternGroup:
    name: str
    aliases: tuple[str, ...]
    suggested_response: str


PATTERN_GROUPS = (
    PatternGroup(
        name="Attention Fragmentation",
        aliases=(
            "context switching",
            "switching tasks",
            "too many tabs",
            "opening tabs",
            "opening too many tabs",
            "many tabs",
            "tabs",
            "jumping between tasks",
            "too many things",
            "too many projects",
            "scattered",
            "distracted",
            "lack of focus",
        ),
        suggested_response=(
            "Start with one execution task. Close unrelated tabs. "
            "Do not research until the first task is complete."
        ),
    ),
    PatternGroup(
        name="Avoidance / Escape Behavior",
        aliases=(
            "doom scrolling",
            "doom scroling",
            "doomscroling",
            "scrolling",
            "scroling",
            "x scrolling",
            "tiktok",
            "youtube",
            "rabbit hole",
            "procrastination",
            "avoiding",
            "wasting time",
        ),
        suggested_response=(
            "Block feeds before deep work. Use phone only after one meaningful task is complete."
        ),
    ),
    PatternGroup(
        name="Overplanning Instead of Shipping",
        aliases=(
            "researching tools",
            "researching instead of shipping",
            "tool hopping",
            "planning too much",
            "overthinking",
            "not shipping",
            "improving setup",
            "changing tools",
            "watching tutorials instead of building",
        ),
        suggested_response="Define one small output, ship it, then improve after.",
    ),
)


def normalize_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def match_pattern_groups(text: str) -> list[PatternGroup]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    matches = []
    for group in PATTERN_GROUPS:
        if any(_contains_alias(normalized, normalize_text(alias)) for alias in group.aliases):
            matches.append(group)
    return matches


def get_pattern_group(name: str) -> PatternGroup | None:
    for group in PATTERN_GROUPS:
        if group.name == name:
            return group
    return None


def _contains_alias(normalized_text: str, normalized_alias: str) -> bool:
    if not normalized_alias:
        return False
    return re.search(rf"(^|\s){re.escape(normalized_alias)}($|\s)", normalized_text) is not None
