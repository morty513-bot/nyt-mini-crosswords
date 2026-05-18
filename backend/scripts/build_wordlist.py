from __future__ import annotations

import urllib.request
from pathlib import Path

SOURCE_URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt"
OUTPUT = Path(__file__).resolve().parents[1] / "src" / "nyt_mini_crosswords" / "data" / "words.tsv"


def main() -> None:
    raw = urllib.request.urlopen(SOURCE_URL, timeout=30).read().decode("utf-8")
    seen: set[str] = set()
    rows: list[str] = []
    rank = 1
    for line in raw.splitlines():
        word = line.strip().lower()
        if not word.isalpha() or len(word) > 5 or len(word) < 3:
            continue
        if word in seen:
            continue
        seen.add(word)
        rows.append(f"{word}\t{rank}")
        rank += 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} words to {OUTPUT}")


if __name__ == "__main__":
    main()
