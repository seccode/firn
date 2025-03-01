import argparse
from collections import Counter, defaultdict
import json
import numpy as np
import random
import zlib
import zstandard as zstd
from tqdm import tqdm

SEP = {",", ".", ";", "?", "!", "\n", "-"}
M = 252

def compress(s, comp):
    most_common_words = open("dict").read().split("\n")
    mcws = set(most_common_words)

    # Use most common chars in text as symbols
    mc = [m[0] for m in Counter(s).most_common()]
    h = set(mc)
    i = 0
    C0, C1 = None, None
    reserved = {"0", "1"}

    while i < 65536:
        c = chr(i)
        if c not in h and c not in reserved:
            if not C0:
                C0 = c
            elif not C1:
                C1 = c
            else:
                break
        i += 1

    if len(s) > 300_000:
        symbols = mc[:20]
    else:
        symbols = mc[:45]

    # Remove spaces/newlines or a/I if they exist in symbols
    if "-" in symbols:
        symbols.remove("-")
    if " " in symbols:
        symbols.remove(" ")
    if "\n" in symbols:
        symbols.remove("\n")
    if "a" in symbols:   # optional
        symbols.remove("a")
    if "I" in symbols:   # optional
        symbols.remove("I")

    one_char_symbols = symbols[:]

    # Add two-char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            if l1 in SEP:
                continue
            symbols.append(l0 + l1)

    # Add three-char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            for l2 in one_char_symbols:
                if l2 in SEP:
                    continue
                symbols.append(l0 + l1 + l2)

    # Replace words with symbols
    words = s.split(" ")
    c = Counter(words)
    mcw = c.most_common()

    Q = "0"
    inds = []
    if len(s) > 300_000:
        # Add four-char symbols
        for l0 in one_char_symbols:
            for l1 in one_char_symbols:
                for l2 in one_char_symbols:
                    for l3 in one_char_symbols:
                        if l3 in SEP:
                            continue
                        symbols.append(l0 + l1 + l2 + l3)

        # Reorder dictionary's top M words by frequency
        reordered_top = sorted(most_common_words[:M], key=lambda word: -c[word])
        for w in reordered_top:
            inds.append(chr(most_common_words[:M].index(w) + ord(C1) + 1))

        most_common_words = reordered_top + most_common_words[M:]
        Q = "1"

    rev_symbols=reversed(symbols[:len(most_common_words)])
    # Build a mapping from each dictionary word -> symbol
    d = {word: symbol for word, symbol in zip(most_common_words, rev_symbols)}
    g = set(d.values())

    new_words = []
    for word in words:
        # Handle newline-splitting
        if "\n" in word:
            ws = word.split("\n")
            w_parts = []
            for idx, wo in enumerate(ws):
                segment = ""
                # Try direct dictionary or punctuation
                if wo in d:
                    segment = d[wo]
                elif wo[:-1] in d and len(wo) > 0 and wo[-1] in SEP:
                    segment = d[wo[:-1]] + wo[-1]
                elif wo in g:
                    segment = C0 + wo
                elif len(wo) > 1 and wo[:-1] in g and wo[-1] in SEP:
                    segment = C0 + wo
                else:
                    segment = wo

                # Append "\n" if this isn't the last piece
                if idx < len(ws) - 1:
                    segment += "\n"
                w_parts.append(segment)

            new_words.append("".join(w_parts))

        # Handle dash-splitting
        elif "-" in word:
            ws = word.split("-")
            w_parts = []
            for idx, wo in enumerate(ws):
                segment = ""
                if wo in d:
                    segment = d[wo]
                elif wo[:-1] in d and len(wo) > 0 and wo[-1] in SEP:
                    segment = d[wo[:-1]] + wo[-1]
                elif wo in g:
                    segment = C0 + wo
                elif len(wo) > 1 and wo[:-1] in g and wo[-1] in SEP:
                    segment = C0 + wo
                else:
                    segment = wo

                # Add dash if not the last chunk
                if idx < len(ws) - 1:
                    segment += "-"
                w_parts.append(segment)

            new_words.append("".join(w_parts))

        # Normal word or punctuation
        elif word in d:
            new_words.append(d[word])
        elif word[:-1] in d and len(word) > 0 and word[-1] in SEP:
            new_words.append(d[word[:-1]] + word[-1])
        elif word in g:
            new_words.append(C0 + word)
        elif len(word) > 1 and word[:-1] in g and word[-1] in SEP:
            new_words.append(C0 + word)
        else:
            new_words.append(word)

    # Next, build the arrays for compression
    nn = []
    x = []
    i = 0
    for word in new_words:
        # If there's exactly one newline in this chunk, handle special marker
        if word.count("\n") == 1:
            wos = word.split("\n")
            nn.append(wos[0])
            nn.append(wos[1])
            x.append(chr(i + ord(C1) + 1))
            i = 0
        else:
            nn.append(word)
            i += 1

    # Construct the final string to compress
    # Format:  C0 C1-joined [ inds, x, one_char_symbols, nn ] + Q
    v = C1.join([
        C0,
        "".join(inds),
        "".join(x),
        " ".join(one_char_symbols),
        " ".join(nn),
    ]) + Q

    return comp.compress(v.encode("utf-8", "replace"))


def decompress(b):
    d_str = zstd.decompress(b).decode("utf-8","replace")

    # Q is last char; first 2 are C0, C1
    Q = d_str[-1]
    C0 = d_str[0]
    C1 = d_str[1]

    # Everything between d_str[2:-1]
    _map, x, symbols, nn = d_str[2:-1].split(C1)
    symbols = symbols.split(" ")
    nn = nn.split(" ")

    # Rebuild "new_words" by combining tokens that had a single newline
    new_words = []
    i = 0
    j = 0
    count_since_newline = 0
    while i < len(nn):
        if j < len(x):
            target = ord(x[j]) - ord(C1) - 1
        else:
            target = None

        if target is not None and count_since_newline == target and (i+1) < len(nn):
            new_words.append(nn[i] + "\n" + nn[i+1])
            i += 2
            j += 1
            count_since_newline = 0
        else:
            new_words.append(nn[i])
            i += 1
            count_since_newline += 1

    # If Q == "1", reorder dictionary
    m = set(_map)  # not strictly needed, but used if debugging
    most_common_words = open("dict").read().split("\n")
    if Q == "1":
        # Rebuild the top M portion using the order in _map
        # _map holds characters that indicate the new order
        # For each char in _map, we get the index in [0..M-1]
        # then pick that from the old top M
        reordered = []
        for _m in _map:
            idx = ord(_m) - ord(C1) - 1
            reordered.append(most_common_words[idx])
        most_common_words = reordered + most_common_words[M:]

    # Expand 2-char, 3-char, 4-char symbols in the same order
    t = symbols[:]
    # 2-char
    for l0 in t:
        for l1 in t:
            if l1 in SEP:
                continue
            symbols.append(l0 + l1)

    # 3-char
    for l0 in t:
        for l1 in t:
            for l2 in t:
                if l2 in SEP:
                    continue
                symbols.append(l0 + l1 + l2)

    # Possibly 4-char
    if Q == "1":
        for l0 in t:
            for l1 in t:
                for l2 in t:
                    for l3 in t:
                        if l3 in SEP:
                            continue
                        symbols.append(l0 + l1 + l2 + l3)

    rev_symbols=reversed(symbols[:len(most_common_words)])
    # Build reverse dictionary: symbol -> word
    d = {symbol: word for symbol, word in zip(rev_symbols, most_common_words)}

    # Final expansion of new_words back to original
    words = []
    for word in new_words:
        if "\n" in word:
            ws = word.split("\n")
            piece = []
            for idx, wo in enumerate(ws):
                if wo in d:
                    piece.append(d[wo])
                elif len(wo) > 1 and wo[:-1] in d and wo[-1] in SEP:
                    piece.append(d[wo[:-1]] + wo[-1])
                elif len(wo) > 0 and wo[0] == C0:
                    # marker indicates this was a literal symbol
                    piece.append(wo[1:])
                else:
                    piece.append(wo)
            words.append("\n".join(piece))

        elif "-" in word:
            ws = word.split("-")
            piece = []
            for idx, wo in enumerate(ws):
                if wo in d:
                    piece.append(d[wo])
                elif len(wo) > 1 and wo[:-1] in d and wo[-1] in SEP:
                    piece.append(d[wo[:-1]] + wo[-1])
                elif len(wo) > 0 and wo[0] == C0:
                    piece.append(wo[1:])
                else:
                    piece.append(wo)
            words.append("-".join(piece))

        elif word in d:
            words.append(d[word])
        elif len(word) > 1 and word[:-1] in d and word[-1] in SEP:
            words.append(d[word[:-1]] + word[-1])
        elif len(word) > 0 and word[0] == C0:
            words.append(word[1:])
        else:
            words.append(word)

    return " ".join(words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", help="File")
    parser.add_argument("--e", help="Encoding")
    args = parser.parse_args()

    # Read the input file
    s = open(args.f, encoding=args.e).read()

    # Save s to "s" (for debugging or other usage)
    with open("s", "w") as f:
        f.write(s)

    comp = zstd.ZstdCompressor(level=22)

    # Compress with our custom algorithm
    b = compress(s, comp)
    print(len(b))

    with open("compressed", "wb") as f:
        f.write(b)

    # Decompress
    _s = decompress(b)
    # Final assertion
    assert _s == s
