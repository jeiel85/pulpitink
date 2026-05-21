"""Curated vocabularies used by the postprocess and correction layers.

This module ships two default dictionaries that anchor the postprocess
pipeline:

* :data:`DEFAULT_BIBLE_BOOKS` — common Korean sermon mistakes around bible
  book names. Whisper frequently inserts a space between the geography and
  the suffix (e.g. *고린도 전서* instead of *고린도전서*).
* :data:`DEFAULT_SERMON_TERMS` — a small list of doctrinal / liturgical
  terms whose canonical Korean spellings are easily corrupted by Whisper.

Both feed into :class:`Lexicon`, which the user can extend with a personal
dictionary file (JSON) via :func:`load_user_lexicon`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Canonical (correct) → list of common STT misrenderings.
DEFAULT_BIBLE_BOOKS: dict[str, tuple[str, ...]] = {
    "창세기": ("창 세기",),
    "출애굽기": ("출 애굽기", "출애 굽기"),
    "레위기": ("레 위기",),
    "민수기": ("민 수기",),
    "신명기": ("신 명기",),
    "여호수아": ("여호 수아",),
    "사사기": ("사 사기",),
    "사무엘상": ("사무엘 상",),
    "사무엘하": ("사무엘 하",),
    "열왕기상": ("열왕기 상",),
    "열왕기하": ("열왕기 하",),
    "역대상": ("역대 상",),
    "역대하": ("역대 하",),
    "에스라": ("에 스라",),
    "느헤미야": ("느 헤미야",),
    "에스더": ("에 스더",),
    "전도서": ("전 도서",),
    "아가": (),
    "이사야": ("이 사야",),
    "예레미야": ("예 레미야",),
    "예레미야애가": ("예레미야 애가",),
    "에스겔": ("에 스겔",),
    "다니엘": ("다 니엘",),
    "호세아": ("호 세아",),
    "요엘": ("요 엘",),
    "아모스": ("아 모스",),
    "오바댜": ("오 바댜",),
    "요나": (),
    "미가": (),
    "나훔": (),
    "하박국": ("하 박국",),
    "스바냐": ("스 바냐",),
    "학개": (),
    "스가랴": ("스 가랴",),
    "말라기": ("말 라기",),
    "마태복음": ("마태 복음",),
    "마가복음": ("마가 복음",),
    "누가복음": ("누가 복음",),
    "요한복음": ("요한 복음",),
    "사도행전": ("사도 행전",),
    "로마서": ("로 마서",),
    "고린도전서": ("고린도 전서",),
    "고린도후서": ("고린도 후서",),
    "갈라디아서": ("갈라 디아서", "갈라디아 서"),
    "에베소서": ("에 베소서", "에베소 서"),
    "빌립보서": ("빌립보 서",),
    "골로새서": ("골로새 서",),
    "데살로니가전서": ("데살로니가 전서",),
    "데살로니가후서": ("데살로니가 후서",),
    "디모데전서": ("디모데 전서",),
    "디모데후서": ("디모데 후서",),
    "디도서": ("디도 서",),
    "빌레몬서": ("빌레몬 서",),
    "히브리서": ("히브리 서",),
    "야고보서": ("야고보 서",),
    "베드로전서": ("베드로 전서",),
    "베드로후서": ("베드로 후서",),
    "요한일서": ("요한 일서",),
    "요한이서": ("요한 이서",),
    "요한삼서": ("요한 삼서",),
    "유다서": ("유다 서",),
    "요한계시록": ("요한 계시록",),
}

# Doctrinal/liturgical vocabulary the STT engine often mis-segments.
DEFAULT_SERMON_TERMS: dict[str, tuple[str, ...]] = {
    "예수 그리스도": ("예수그리스도",),
    "성령": (),
    "복음": (),
    "할렐루야": ("할 렐루야",),
    "아멘": (),
    "교회": (),
    "사도신경": ("사도 신경",),
    "주기도문": ("주 기도문",),
    "은혜": (),
    "구원": (),
    "회개": (),
    "축복": (),
    "장로교": ("장로 교",),
    "감리교": ("감리 교",),
    "성례": (),
    "세례": (),
    "예배": (),
    "찬송": (),
    "기도": (),
}


@dataclass
class Lexicon:
    """A canonical-to-misrendering substitution table.

    Lookup direction: we iterate the wrong forms and replace them with the
    canonical form. Longer wrong forms are matched before shorter ones so
    "고린도 전서" wins over a hypothetical "고린도 전" prefix.
    """

    entries: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def add(self, canonical: str, *wrong_forms: str) -> None:
        existing = list(self.entries.get(canonical, ()))
        for form in wrong_forms:
            if form and form != canonical and form not in existing:
                existing.append(form)
        self.entries[canonical] = tuple(existing)

    def update(self, other: Lexicon | dict[str, tuple[str, ...]]) -> None:
        items = other.entries.items() if isinstance(other, Lexicon) else other.items()
        for canonical, forms in items:
            self.add(canonical, *forms)

    def items(self) -> list[tuple[str, tuple[str, ...]]]:
        return sorted(
            self.entries.items(),
            key=lambda item: max((len(f) for f in item[1]), default=len(item[0])),
            reverse=True,
        )

    def apply(self, text: str) -> str:
        """Return ``text`` with every known wrong form replaced.

        For empty ``wrong_forms`` we still try to normalise ``"canonical "``-
        style spaced variants — but only when the canonical form contains
        Hangul (avoids over-aggressive substitution).
        """

        if not text:
            return text
        out = text
        for canonical, forms in self.items():
            for wrong in forms:
                if not wrong:
                    continue
                out = out.replace(wrong, canonical)
        return out


def default_lexicon() -> Lexicon:
    """Build a lexicon pre-populated with the shipped dictionaries."""

    lex = Lexicon()
    for canonical, forms in DEFAULT_BIBLE_BOOKS.items():
        lex.add(canonical, *forms)
    for canonical, forms in DEFAULT_SERMON_TERMS.items():
        lex.add(canonical, *forms)
    return lex


_USER_DICT_SCHEMA_HINT = (
    "사용자 사전 파일은 JSON 형식이어야 합니다. "
    '예: {"예수 그리스도": ["예수그리스도"], "은혜": []}'
)


def load_user_lexicon(path: Path | str | None) -> Lexicon:
    """Load an optional user dictionary on top of the shipped lexicon.

    The JSON shape is ``{canonical: [wrong1, wrong2, ...], ...}``. Empty
    arrays are allowed — they let the user register a canonical term
    without supplying explicit STT misrenderings (still useful as proper
    nouns later for correction suggestions).

    Missing or empty ``path`` simply returns the default lexicon.
    """

    lex = default_lexicon()
    if path is None:
        return lex
    p = Path(path)
    if not p.exists():
        return lex
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{_USER_DICT_SCHEMA_HINT} ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(_USER_DICT_SCHEMA_HINT)
    for canonical, forms in data.items():
        if not isinstance(canonical, str):
            continue
        if isinstance(forms, str):
            forms_iter: tuple[str, ...] = (forms,)
        elif isinstance(forms, (list, tuple)):
            forms_iter = tuple(str(f) for f in forms if isinstance(f, str))
        else:
            continue
        lex.add(canonical, *forms_iter)
    return lex


def save_user_lexicon(path: Path | str, entries: dict[str, list[str] | tuple[str, ...]]) -> None:
    """Save user lexicon entries to a JSON file.

    Saves the data securely by writing to a temporary file first,
    then renaming it to prevent corruption. If the target file exists,
    creates a backup (.bak) beforehand.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    bak_path = p.with_suffix(".json.bak")
    if p.exists():
        try:
            if bak_path.exists():
                bak_path.unlink()
            p.rename(bak_path)
        except OSError:
            pass

    tmp_path = p.with_suffix(".json.tmp")
    try:
        data_to_save = {canonical: list(forms) for canonical, forms in entries.items()}
        tmp_path.write_text(
            json.dumps(data_to_save, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        if tmp_path.exists():
            if p.exists():
                p.unlink()
            tmp_path.rename(p)

        if bak_path.exists():
            try:
                bak_path.unlink()
            except OSError:
                pass
    except Exception as exc:
        if bak_path.exists():
            try:
                if p.exists():
                    p.unlink()
                bak_path.rename(p)
            except OSError:
                pass
        raise OSError(f"사용자 사전을 저장하는 중 오류가 발생했습니다: {exc}") from exc


# A liberal regex that recognises a single bible reference candidate.
# Examples it matches:
#   로마서 1장 1절       (already canonical — left unchanged)
#   로마서 일장 일절    → 1장 1절
#   고린도 전서 5장     → 고린도전서 5장
_BOOK_NAMES = sorted(DEFAULT_BIBLE_BOOKS.keys(), key=len, reverse=True)
_BOOK_PATTERN = "(?:" + "|".join(re.escape(name) for name in _BOOK_NAMES) + ")"
BIBLE_REF_RE = re.compile(_BOOK_PATTERN)
