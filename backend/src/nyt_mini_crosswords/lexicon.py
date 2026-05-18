from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class WordEntry:
    word: str
    rank: int
    weight: float


def _normalize_word(value: str) -> str:
    cleaned = value.strip().upper()
    if not cleaned or not cleaned.isalpha():
        raise ValueError(f"Invalid crossword word: {value!r}")
    if len(cleaned) > 5:
        raise ValueError(f"Crossword words must be at most 5 letters: {value!r}")
    return cleaned


class Lexicon:
    def __init__(self, entries: Iterable[WordEntry]):
        self._entries = list(entries)
        self._entries.sort(key=lambda entry: (-entry.weight, entry.word))
        self._by_length: dict[int, list[WordEntry]] = {}
        self._position_index: dict[int, list[dict[str, list[WordEntry]]]] = {}
        for entry in self._entries:
            self._by_length.setdefault(len(entry.word), []).append(entry)
        for length, entries_for_length in self._by_length.items():
            buckets = [dict() for _ in range(length)]
            for entry in entries_for_length:
                for index, letter in enumerate(entry.word):
                    buckets[index].setdefault(letter, []).append(entry)
            self._position_index[length] = buckets

    @classmethod
    def from_tsv(cls, path: Path) -> "Lexicon":
        entries: list[WordEntry] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(f"Invalid lexicon line: {line!r}")
            word = _normalize_word(parts[0])
            rank = int(parts[1])
            if rank <= 0:
                raise ValueError(f"Rank must be positive for {word!r}")
            entries.append(WordEntry(word=word, rank=rank, weight=1_000_000.0 / rank))
        return cls(entries)

    @property
    def size(self) -> int:
        return len(self._entries)

    def words_of_length(self, length: int) -> list[WordEntry]:
        return list(self._by_length.get(length, []))

    def candidates(
        self,
        length: int,
        pattern: str,
        used_words: set[str],
        limit: int | None = None,
    ) -> list[WordEntry]:
        if len(pattern) != length:
            return []
        buckets = self._position_index.get(length)
        if not buckets:
            return []
        candidate_pool: set[WordEntry] | None = None
        for index, letter in enumerate(pattern):
            if letter == ".":
                continue
            bucket = set(buckets[index].get(letter, []))
            candidate_pool = bucket if candidate_pool is None else candidate_pool & bucket
            if not candidate_pool:
                return []
        if candidate_pool is None:
            candidate_pool = set(self._by_length.get(length, []))
        filtered = [entry for entry in candidate_pool if entry.word not in used_words]
        filtered.sort(key=lambda entry: (-entry.weight, entry.word))
        if limit is not None:
            return filtered[:limit]
        return filtered
