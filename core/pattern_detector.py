from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re

from core.file_store import FileStore


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
class DetectedPattern:
    source: str
    phrase: str
    count: int
    pattern: str
    evidence: str
    suggested_response: str


def analyze_and_update_patterns(store: FileStore) -> list[DetectedPattern]:
    reviews = store.read_file("reviews.md", "# Reviews\n")
    patterns = detect_patterns(reviews)
    memory = store.read_file("memory.md", "# Memory\n")
    store.write_file("memory.md", update_memory_patterns(memory, patterns))
    return patterns


def detect_patterns(
    reviews_markdown: str,
    min_mentions: int = MIN_PATTERN_MENTIONS,
    recent_review_limit: int = RECENT_REVIEW_LIMIT,
) -> list[DetectedPattern]:
    reviews = parse_reviews(reviews_markdown)
    recent_reviews = reviews[-recent_review_limit:]

    counts: dict[tuple[str, str], set[int]] = defaultdict(set)
    originals: dict[tuple[str, str], str] = {}
    fields = [
        ("blocker", "blocked"),
        ("lesson", "learned"),
        ("tomorrow rule", "change"),
    ]

    for review_index, review in enumerate(recent_reviews):
        for source, attribute in fields:
            seen_in_review: set[str] = set()
            for phrase in _split_review_items(getattr(review, attribute)):
                normalized = _normalize_phrase(phrase)
                if not normalized or normalized in {"nothing recorded", "none", "n/a", "na"}:
                    continue

                key = (source, normalized)
                originals.setdefault(key, phrase)
                seen_in_review.add(normalized)

            for normalized in seen_in_review:
                counts[(source, normalized)].add(review_index)

    patterns: list[DetectedPattern] = []
    for (source, normalized), review_indexes in counts.items():
        count = len(review_indexes)
        if count < min_mentions:
            continue

        phrase = originals[(source, normalized)]
        patterns.append(_build_pattern(source, phrase, count))

    source_rank = {"blocker": 0, "lesson": 1, "tomorrow rule": 2}
    return sorted(patterns, key=lambda item: (-item.count, source_rank[item.source], item.phrase.lower()))


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


def update_memory_patterns(memory_markdown: str, patterns: list[DetectedPattern]) -> str:
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


def _section_text(review_body: str, section: str) -> str:
    section_pattern = re.compile(
        rf"^### {re.escape(section)}[ \t]*\n(?P<body>.*?)(?=^### |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = section_pattern.search(review_body)
    if not match:
        return ""
    return match.group("body").strip()


def _split_review_items(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        cleaned = line.strip().lstrip("-*").strip()
        if cleaned:
            items.append(cleaned)
    if not items and text.strip():
        items.append(text.strip())
    return items


def _normalize_phrase(phrase: str) -> str:
    normalized = phrase.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _build_pattern(source: str, phrase: str, count: int) -> DetectedPattern:
    readable_phrase = _sentence_case(phrase)
    if source == "blocker":
        pattern = f"{readable_phrase} appears repeatedly"
    elif source == "lesson":
        pattern = f"Lesson repeats: {readable_phrase}"
    else:
        pattern = f"Tomorrow rule repeats: {readable_phrase}"

    return DetectedPattern(
        source=source,
        phrase=phrase,
        count=count,
        pattern=pattern,
        evidence=f"Mentioned in {count} reviews as a {source}",
        suggested_response=_suggest_response(source, phrase),
    )


def _sentence_case(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return cleaned
    return cleaned[0].upper() + cleaned[1:]


def _suggest_response(source: str, phrase: str) -> str:
    normalized = _normalize_phrase(phrase)

    if source == "blocker":
        if "context switch" in normalized or "switching" in normalized:
            return "Start the day with one execution task before research"
        if "doom" in normalized or "scroll" in normalized or "social" in normalized:
            return "Put the phone away before deep work and check it only after the first task"
        if "tool" in normalized or "research" in normalized:
            return "Timebox research, then ship the smallest useful version"
        return f"Choose one prevention step before work starts: {phrase}"

    if source == "lesson":
        if "ship" in normalized or "shipping" in normalized:
            return "Turn this lesson into tomorrow's first concrete shipping action"
        return "Turn this lesson into one visible action in tomorrow's plan"

    return "Make this tomorrow rule the first check before choosing tasks"


def _format_generated_patterns(patterns: list[DetectedPattern]) -> str:
    if not patterns:
        body = "\n".join(
            [
                "- Pattern: No repeated blockers, lessons, or tomorrow rules detected yet",
                "  Evidence: Fewer than 2 matching review entries found",
                "  Suggested response: Keep completing daily reviews until trends are visible",
            ]
        )
    else:
        blocks = []
        for pattern in patterns:
            blocks.append(
                "\n".join(
                    [
                        f"- Pattern: {pattern.pattern}",
                        f"  Evidence: {pattern.evidence}",
                        f"  Suggested response: {pattern.suggested_response}",
                    ]
                )
            )
        body = "\n".join(blocks)

    return f"{GENERATED_START}\n{body}\n{GENERATED_END}"


def _remove_generated_block(text: str) -> str:
    generated_pattern = re.compile(
        rf"\s*{re.escape(GENERATED_START)}.*?{re.escape(GENERATED_END)}\s*",
        flags=re.DOTALL,
    )
    return generated_pattern.sub("\n", text)
