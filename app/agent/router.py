import re
from typing import Any


FRESH_INFO_PATTERNS = [
    re.compile('最新'),
    re.compile('最近'),
    re.compile('当前'),
    re.compile('联网'),
    re.compile('网页'),
    re.compile('搜索'),
    re.compile(r'\bcurrent\b', re.IGNORECASE),
    re.compile(r'\blatest\b', re.IGNORECASE),
    re.compile(r'\brecent\b', re.IGNORECASE),
    re.compile(r'\bsearch\b', re.IGNORECASE),
    re.compile(r'\bweb\b', re.IGNORECASE),
    re.compile(r'\bnews\b', re.IGNORECASE)
]


def score_matches(question: str, patterns: list[str] | None = None) -> int:
    total = 0

    for pattern in patterns or []:
        if pattern.lower() in question:
            total += 20

    return total


def needs_fresh_info(question: str) -> bool:
    return any(pattern.search(question) for pattern in FRESH_INFO_PATTERNS)


def select_skill(question: str, skill_entries: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_question = question.lower()
    ranked_skills = []

    for skill in skill_entries:
        explicit_mentions = skill.get('triggers', {}).get('explicit_mentions', [])
        task_patterns = skill.get('triggers', {}).get('task_patterns', [])
        score = skill.get('priority', 0)

        if any(mention.lower() in normalized_question for mention in explicit_mentions):
            score += 100

        score += score_matches(normalized_question, task_patterns)

        if skill['id'] == 'skill.web-researcher' and needs_fresh_info(question):
            score += 80

        if skill['id'] == 'skill.local-explainer' and not needs_fresh_info(question):
            score += 40

        ranked_skills.append({
            **skill,
            'score': score
        })

    ranked_skills.sort(key=lambda item: item['score'], reverse=True)

    return ranked_skills[0]
