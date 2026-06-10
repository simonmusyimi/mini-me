from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re

from core.file_store import FileStore
from core.pattern_taxonomy import match_pattern_groups


GENERATED_START = "<!-- MINI-ME:PATTERNS:START -->"
GENERATED_END = "<!-- MINI-ME:PATTERNS:END -->"
RECENT_REVIEW_LIMIT = 14
MIN_PATTERN_MENTIONS = 2


@dataclass(frozen=True)
class ReviewEntry:
    completed: str
    blocked: str
    learned: str
    change: str


@dataclass(frozen=True)
class GroupedPattern:
    name: str
    frequency: int
    evidence: tuple[str, ...]
    suggested_response: str


@dataclass(frozen=True)
class PatternWarning:
    name: str
    frequency: int
    suggested_response: str


def analyze_and_update_patterns(store: FileStore) -> list[GroupedPattern]:
    reviews = store.read_file("reviews.md", "# Reviews\n")
    patterns = detect_patterns(reviews)
    memory = store.read_file("memory.md", "# Memory\n")
    store.write_file("memory.md", update_memory_patterns(memory, patterns))
    return patterns


def detect_patterns(
    reviews_markdown: str,
    min_mentions: int = MIN_PATTERN_MENTIONS,
    recent_review_limit: int = RECENT_REVIEW_LIMIT,
) -> list[GroupedPattern]:
    reviews = parse_reviews(reviews_markdown)
    recent_reviews = reviews[-recent_review_limit:]

    group_counts: Counter[str] = Counter()
    evidence_counts: dict[str, Counter[str]] = {}
    suggested_responses: dict[str, str] = {}
    fields = [
        "blocked",
        "learned",
        "change",
    ]

    for review in recent_reviews:
        for attribute in fields:
            for phrase in _split_review_items(getattr(review, attribute)):
                if _is_empty_review_value(phrase):
                    continue

                for group in match_pattern_groups(phrase):
                    group_counts[group.name] += 1
                    evidence_counts.setdefault(group.name, Counter())[phrase] += 1
                    suggested_responses[group.name] = group.suggested_response

    patterns: list[GroupedPattern] = []
    for group_name, frequency in group_counts.items():
        if frequency < min_mentions:
            continue

        evidence = tuple(
            phrase
            for phrase, _count in sorted(
                evidence_counts[group_name].items(),
                key=lambda item: (-item[1], item[0].lower()),
            )
        )
        patterns.append(
            GroupedPattern(
                name=group_name,
                frequency=frequency,
                evidence=evidence,
                suggested_response=suggested_responses[group_name],
            )
        )

    return sorted(patterns, key=lambda item: (-item.frequency, item.name.lower()))


def parse_reviews(reviews_markdown: str) -> list[ReviewEntry]:
    review_pattern = re.compile(
        r"^## Review - .+?\n(?P<body>.*?)(?=^## Review - |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    return [
        ReviewEntry(
            completed=_section_text(match.group("body"), "Completed"),
            blocked=_section_text(match.group("body"), "Blocked"),
            learned=_section_text(match.group("body"), "Learned"),
            change=_section_text(match.group("body"), "Change Tomorrow"),
        )
        for match in review_pattern.finditer(reviews_markdown)
    ]


def update_memory_patterns(memory_markdown: str, patterns: list[GroupedPattern]) -> str:
    memory = memory_markdown.strip() or "# Memory"
    generated_block = _format_generated_patterns(patterns)
    pattern_section = re.compile(
        r"(^## Patterns[ \t]*\n)(?P<body>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern_section.search(memory)

    if not match:
        return memory.rstrip() + f"\n\n## Patterns\n\n{generated_block}\n"

    existing_body = _remove_generated_block(match.group("body")).rstrip()
    if existing_body:
        replacement = f"{match.group(1)}{existing_body}\n\n{generated_block}\n\n"
    else:
        replacement = f"{match.group(1)}{generated_block}\n\n"

    updated = memory[: match.start()] + replacement + memory[match.end() :]
    return updated.rstrip() + "\n"


def extract_pattern_warnings(memory_markdown: str) -> list[PatternWarning]:
    pattern_body = _patterns_section_body(memory_markdown)
    if not pattern_body:
        return []

    warning_pattern = re.compile(
        r"^### (?P<name>.+?)\n+"
        r"Frequency:\s*(?P<frequency>\d+).*?"
        rf"Suggested Response:\n(?P<response>.*?)(?=^### |^{re.escape(GENERATED_END)}|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )

    warnings = []
    for match in warning_pattern.finditer(pattern_body):
        warnings.append(
            PatternWarning(
                name=match.group("name").strip(),
                frequency=int(match.group("frequency")),
                suggested_response=" ".join(match.group("response").strip().split()),
            )
        )
    return warnings


def format_pattern_warnings(memory_markdown: str) -> str:
    warnings = extract_pattern_warnings(memory_markdown)
    if not warnings:
        return ""

    lines = ["=== Pattern Warnings ===", ""]
    for warning in warnings:
        lines.append(
            f"* {warning.name} is recurring: {warning.suggested_response}"
        )
    return "\n".join(lines)


def _section_text(review_body: str, section: str) -> str:
    section_pattern = re.compile(
        rf"^### {re.escape(section)}[ \t]*\n(?P<body>.*?)(?=^### |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = section_pattern.search(review_body)
    if not match:
        return ""
    return match.group("body").strip()


def _patterns_section_body(memory_markdown: str) -> str:
    section_pattern = re.compile(
        r"^## Patterns[ \t]*\n(?P<body>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = section_pattern.search(memory_markdown)
    if not match:
        return ""
    return match.group("body")


def _split_review_items(text: str) -> list[str]:
    items: list[str] = []
    for line in re.split(r"[\n,;]+", text):
        cleaned = line.strip().lstrip("-*").strip()
        if cleaned:
            items.append(cleaned)
    if not items and text.strip():
        items.append(text.strip())
    return items


def _is_empty_review_value(phrase: str) -> bool:
    cleaned = phrase.strip().lower()
    return cleaned in {"", "nothing recorded", "none", "n/a", "na"}


def _format_generated_patterns(patterns: list[GroupedPattern]) -> str:
    if not patterns:
        body = "\n".join(
            [
                "No grouped patterns detected yet.",
                "",
                "Evidence: Fewer than 2 matching review entries found.",
                "Suggested Response: Keep completing daily reviews until trends are visible.",
            ]
        )
    else:
        blocks = []
        for pattern in patterns:
            evidence_lines = "\n".join(f"- {evidence}" for evidence in pattern.evidence)
            blocks.append(
                "\n".join(
                    [
                        f"### {pattern.name}",
                        "",
                        f"Frequency: {pattern.frequency}",
                        "Evidence:",
                        evidence_lines,
                        "",
                        "Suggested Response:",
                        pattern.suggested_response,
                    ]
                )
            )
        body = "\n\n".join(blocks)

    return f"{GENERATED_START}\n{body}\n{GENERATED_END}"


def _remove_generated_block(text: str) -> str:
    generated_pattern = re.compile(
        rf"\s*{re.escape(GENERATED_START)}.*?{re.escape(GENERATED_END)}\s*",
        flags=re.DOTALL,
    )
    return generated_pattern.sub("\n", text)
