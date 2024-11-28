import argparse
from charset_normalizer import detect
from collections import Counter
import zstandard as zstd

SEP={",",".",";","?","!","\n"}

def compress(s,comp):
    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")

    # Use most common chars in text as symbols
    mc=[m[0] for m in Counter(s).most_common()]
    g=set(mc)
    i=0
    C0,C1=None,None
    while i<256:
        c=chr(i)
        if c not in g:
            if not C0:
                C0=c
            elif not C1:
                C1=c
            else:
                break
        i+=1
    if not any([C0,C1]):
        return comp.compress(s.encode("utf-8","replace"))

    symbols=mc[:35]
    symbols.remove(" ")
    one_char_symbols=symbols[:]

    # Add two char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            if l1 in SEP:
                continue
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            for l2 in one_char_symbols:
                if l2 in SEP:
                    continue
                symbols.append(l0+l1+l2)

    # Map most common words to symbols
    d={word:symbol for word,symbol in zip(most_common_words,symbols)}
    g=set(d.values())

    # Replace words with symbols
    words=s.split(" ")
    new_words=[]
    for i,word in enumerate(words):
        if word in d: # Replace with symbol
            new_words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            new_words.append(d[word[:-1]]+word[-1])
        elif word in g: # Word is a used symbol, add a marker
            new_words.append(C0+word)
        elif word[:-1] in g and word[-1] in SEP:
            new_words.append(word+C0)
        else: # Default case, word is not common
            new_words.append(word)

    # To decompress, we need one char symbols and new words
    v=C1.join([
        C0,
        "".join(one_char_symbols),
        " ".join(new_words),
    ])

    # Return zstd compressed object
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    # zstd decompress
    d=zstd.decompress(b).decode("utf-8","replace")
    C0,C1=d[0],d[1]
    symbols,new_words=d[2:].split(C1)
    symbols=list(symbols)
    new_words=new_words.split(" ")

    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")

    # Use most common chars in text as symbols
    t=symbols[:]
    for l0 in t:
        for l1 in t:
            if l1 in SEP:
                continue
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in t:
        for l1 in t:
            for l2 in t:
                if l2 in SEP:
                    continue
                symbols.append(l0+l1+l2)

    # Map most symbols to most common words
    d={symbol:word for symbol,word in zip(symbols,most_common_words)}

    # Replace symbols with original words
    words=[]
    for word in new_words:
        if word in d: # Symbol used, replace with original word
            words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            words.append(d[word[:-1]]+word[-1])
        elif len(word)>0 and word[0]==C0: # Marker
            words.append(word[1:])
        elif len(word)>1 and word[-1]==C0 and word[-2] in SEP: # Marker
            words.append(word[:-1])
        else: # Default case, word was not replaced
            words.append(word)
    return " ".join(words)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--f",help="File")
    parser.add_argument("--e",help="Encoding")
    args=parser.parse_args()

    # Read dickens
    s=open(args.f,encoding=args.e).read()[50_000:100_000] # Take first chunk of text

    comp=zstd.ZstdCompressor(level=1)

    # Compress with our custom algorithm
    b=compress(s,comp)

    # Decompress with our custom algorithm
    _s=decompress(b)

    # Assert equality
    assert _s==s
