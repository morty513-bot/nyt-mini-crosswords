from __future__ import annotations

from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "src" / "nyt_mini_crosswords" / "data" / "words.tsv"

from wordfreq import top_n_list, zipf_frequency

from nyt_mini_crosswords.wordlist_filters import is_allowed_word, normalize_word


def main() -> None:
    seen: set[str] = set()
    rows: list[str] = []
    rank = 1
    for word in top_n_list("en", 20000):
        normalized = normalize_word(word)
        if not is_allowed_word(normalized, zipf_frequency(normalized, "en")):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        rows.append(f"{normalized}\t{rank}")
        rank += 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} words to {OUTPUT}")


if __name__ == "__main__":
    main()
