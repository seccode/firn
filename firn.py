import argparse
from collections import Counter, defaultdict
import zstandard as zstd
from tqdm import tqdm

SEP = {",", ".", ";", "?", "!", "\n", "-"}
M = 252

def compress(s, comp):
    most_common_words = open("dict2").read().split("\n")
    mcws = set(most_common_words)

    mc = [m[0] for m in Counter(s).most_common()]
    h = set(mc)
    i = 0
    C0, C1 = None, None

    reserved = {"0", "1"}
    while i < 256:
        c = chr(i)
        if c not in h and c not in reserved:
            if not C0:
                C0 = c
            elif not C1:
                C1 = c
            else:
                break
        i += 1

    if not all([C0, C1]):
        print("No C0/C1 found, using zstd alone")
        return comp.compress(s.encode("utf-8", "replace"))

    if len(s) > 300_000:
        symbols = mc[:20]
    else:
        symbols = mc[:45]

    for char in ["-", " ", "\n", "a", "I"]:
        if char in symbols:
            symbols.remove(char)

    one_char_symbols = symbols[:]
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            if l1 in SEP:
                continue
            symbols.append(l0 + l1)

    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            for l2 in one_char_symbols:
                if l2 in SEP:
                    continue
                symbols.append(l0 + l1 + l2)

    words = s.split(" ")
    c = Counter(words)
    mcw = c.most_common()

    Q = "0"
    inds = []
    if len(s) > 300_000:
        for l0 in one_char_symbols:
            for l1 in one_char_symbols:
                for l2 in one_char_symbols:
                    for l3 in one_char_symbols:
                        if l3 in SEP:
                            continue
                        symbols.append(l0 + l1 + l2 + l3)
        reordered_top = sorted(most_common_words[:M], key=lambda word: -c[word])
        for w in reordered_top:
            inds.append(chr(most_common_words[:M].index(w) + ord(C1) + 1))
        most_common_words = reordered_top + most_common_words[M:]
        Q = "1"

    e = defaultdict(set)
    d_base = {word: symbol for word, symbol in zip(most_common_words, symbols) if len(symbol) < len(word)}
    y = {word: i for i, word in enumerate(most_common_words)}
    g = set(d_base.values())
    last = "the"

    for i in range(1, len(words)):
        if words[i] in d_base:
            e[last].add(words[i])
            last = words[i]
        elif words[i][:-1] in d_base and words[i][-1] in SEP:
            e[last].add(words[i][:-1])
            last = words[i][:-1]
        elif "\n" in words[i]:
            ws = words[i].split("\n")
            for w in ws:
                if w in d_base:
                    e[last].add(w)
                    last = w
                elif w[:-1] in d_base and w[-1] in SEP:
                    e[last].add(w[:-1])
                    last = w[:-1]
        elif "-" in words[i]:
            ws = words[i].split("-")
            for w in ws:
                if w in d_base:
                    e[last].add(w)
                    last = w
                elif w[:-1] in d_base and w[-1] in SEP:
                    e[last].add(w[:-1])
                    last = w[:-1]

    d = defaultdict(dict)
    for k, v in tqdm(e.items()):
        vl = sorted(v, key=lambda x: y[x])
        i = 0
        for _v in vl:
            if i >= len(symbols):
                break
            if len(symbols[i]) < len(_v):
                d[k][_v] = symbols[i]
            i += 1

    new_words = []
    last = "the"
    replacements = 0
    for word in words:
        if "\n" in word:
            ws = word.split("\n")
            w_parts = []
            for idx, wo in enumerate(ws):
                segment = wo
                if wo in d[last] and len(d[last][wo]) < len(wo):
                    segment = d[last][wo]
                    last = wo
                    replacements += 1
                elif wo[:-1] in d[last] and len(wo) > 0 and wo[-1] in SEP and len(d[last][wo[:-1]]) < len(wo[:-1]):
                    segment = d[last][wo[:-1]] + wo[-1]
                    last = wo[:-1]
                    replacements += 1
                if idx < len(ws) - 1:
                    segment += "\n"
                w_parts.append(segment)
            new_words.append("".join(w_parts))

        elif "-" in word:
            ws = word.split("-")
            w_parts = []
            for idx, wo in enumerate(ws):
                segment = wo
                if wo in d[last] and len(d[last][wo]) < len(wo):
                    segment = d[last][wo]
                    last = wo
                    replacements += 1
                elif wo[:-1] in d[last] and len(wo) > 0 and wo[-1] in SEP and len(d[last][wo[:-1]]) < len(wo[:-1]):
                    segment = d[last][wo[:-1]] + wo[-1]
                    last = wo[:-1]
                    replacements += 1
                if idx < len(ws) - 1:
                    segment += "-"
                w_parts.append(segment)
            new_words.append("".join(w_parts))

        elif word in d[last] and len(d[last][word]) < len(word):
            new_words.append(d[last][word])
            last = word
            replacements += 1
        elif word[:-1] in d[last] and len(word) > 0 and word[-1] in SEP and len(d[last][word[:-1]]) < len(word[:-1]):
            new_words.append(d[last][word[:-1]] + word[-1])
            last = word[:-1]
            replacements += 1
        else:
            new_words.append(word)

    nn = []
    x = []
    i = 0
    for word in new_words:
        if word.count("\n") == 1:
            wos = word.split("\n")
            nn.append(wos[0])
            nn.append(wos[1])
            x.append(chr(i + ord(C1) + 1))
            i = 0
        else:
            nn.append(word)
            i += 1

    # Count frequencies and build dictionary
    c = Counter(nn).most_common()
    d = {}
    uc = [chr(i) for i in range(ord(C1) + 1, 5000) if chr(i) not in h]
    i = 0
    if len(s) < 300_000:
        n = 100
    else:
        n = 250
    for m in c[:n]:  # m = (word, count)
        if m[0] not in g:
            if len(m[0]) > 1 and m[0][:-1] not in g:
                if m[-1] not in SEP:  # Should be m[0][-1], assuming typo
                    if len(m[0]) > len(uc[i]):  # Only replace if symbol is shorter
                        d[m[0]] = uc[i]
                        i += 1
                        if i >= len(uc):
                            break

    # Apply dictionary substitutions
    new = []
    replacements = 0
    for word in nn:
        if word in d:
            new.append(d[word])
            replacements += 1
        elif len(word) > 0 and word[:-1] in d and word[-1] in SEP:
            new.append(d[word[:-1]] + word[-1])
            replacements += 1
        else:
            new.append(word)

    # Construct the final string with minimal separators
    v_parts = [
        C0,
        "".join(inds),
        "".join(x),
        " ".join(one_char_symbols),  # Keep spaces here as it's metadata
        "".join(new),  # No spaces between words to reduce size
        " ".join(d.keys()),  # Spaces for parsing clarity
        "".join(d.values()),  # No spaces for efficiency
    ]
    v = C1.join(v_parts) + Q

    # Diagnostics
    input_bytes = s.encode("utf-8", "replace")
    v_bytes = v.encode("utf-8", "replace")
    compressed_bytes = zstd.compress(v_bytes,level=22)
    print(f"Original input size: {len(input_bytes)} bytes")
    print(f"Pre-zstd size (v): {len(v_bytes)} bytes")
    print(f"Replacements made: {replacements}")
    print(f"Final compressed size: {len(compressed_bytes)} bytes")

    return compressed_bytes

def main():
    parser = argparse.ArgumentParser(description="Compress a file")
    parser.add_argument("--f", required=True, help="Input file")
    parser.add_argument("--e", default="utf-8", help="Encoding")
    args = parser.parse_args()

    with open(args.f, "r", encoding=args.e) as f:
        s = f.read()

    comp = zstd.ZstdCompressor()
    compressed_data = compress(s, comp)

if __name__ == "__main__":
    main()
