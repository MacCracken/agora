#!/usr/bin/env python3
# scripts/gen-decode-guesses.py — regenerate Decode/Words' guess dictionary
# (src/decode_words.cyr, decode_guess_blob) from the ENABLE word list.
#
# Why (1.12.0): the 532-word answer pool doubled as the guess dictionary, so
# most real English words came back "not a word" (ADR 0018 § Consequences;
# roadmap 1.12.0). The answer pool is unchanged — its order is what a seeded
# Words game draws from, so a save and the Handler's decrypt lever replay the
# same secrets — and a second, sorted list now decides what a guess may be.
#
# Source: ENABLE (Enhanced North American Benchmark Lexicon), public domain;
# the copy used at 1.12.0 is enable1.txt from github.com/dolph/dictionary,
# sha256 3f16130220645692ed49c7134e24a18504c2ca55b3c012f7290e3e77c63b1a89.
# Rule: every entry of exactly five ASCII lowercase letters, plus every answer
# (none were missing at 1.12.0), deduplicated and sorted bytewise — the binary
# search in decode_guess_ok depends on that order.
#
# Usage: scripts/gen-decode-guesses.py <enable1.txt>
# Rewrites the GUESS_COUNT value and the decode_guess_blob literal in place;
# exits 1 if the file does not have the shape this script expects.

import re
import sys

SRC = "src/decode_words.cyr"


def main():
    if len(sys.argv) != 2:
        print("usage: scripts/gen-decode-guesses.py <enable1.txt>")
        return 2
    words = set()
    with open(sys.argv[1], encoding="ascii") as f:
        for line in f:
            w = line.strip()
            if re.fullmatch(r"[a-z]{5}", w):
                words.add(w)
    src = open(SRC).read()
    m = re.search(r'fn decode_word_blob\(\): i64 \{\n    return "([a-z]+)";', src)
    if m is None or len(m.group(1)) % 5 != 0:
        print("gen-decode-guesses: the answer blob was not found")
        return 1
    answers = [m.group(1)[i:i + 5] for i in range(0, len(m.group(1)), 5)]
    missing = [a for a in answers if a not in words]
    words.update(answers)
    guesses = sorted(words)
    blob = "".join(guesses)
    n_count = len(re.findall(r"GUESS_COUNT\s*=\s*\d+;", src))
    n_blob = len(re.findall(r'fn decode_guess_blob\(\): i64 \{\n    return "[a-z]*";', src))
    if n_count != 1 or n_blob != 1:
        print("gen-decode-guesses: GUESS_COUNT / decode_guess_blob not found exactly once")
        return 1
    src = re.sub(r"GUESS_COUNT\s*=\s*\d+;", "GUESS_COUNT = %d;" % len(guesses), src)
    src = re.sub(r'(fn decode_guess_blob\(\): i64 \{\n    return ")[a-z]*(";)',
                 lambda mm: mm.group(1) + blob + mm.group(2), src)
    open(SRC, "w").write(src)
    print("gen-decode-guesses: %d guesses (%d answers, %d added from the answers)"
          % (len(guesses), len(answers), len(missing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
