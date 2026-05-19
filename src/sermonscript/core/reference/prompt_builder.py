from dataclasses import dataclass


@dataclass
class ReferencePrompt:
    title: str | None
    bible_refs: list[str]
    keywords: list[str]
    custom_terms: list[str]


def build_reference_prompt(ref: ReferencePrompt) -> str:
    lines = [
        "이 음성은 한국어 설교입니다.",
        "성경책 이름, 장절, 인명, 신학 용어를 정확히 기록합니다.",
    ]

    if ref.title:
        lines.append(f"설교 제목: {ref.title}")

    if ref.bible_refs:
        lines.append("성경 본문: " + ", ".join(ref.bible_refs[:5]))

    terms = [*ref.keywords[:20], *ref.custom_terms[:20]]
    terms = list(dict.fromkeys(terms))

    if terms:
        lines.append("주요 용어: " + ", ".join(terms[:40]))

    return "
".join(lines)
