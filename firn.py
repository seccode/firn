import argparse
from collections import Counter,defaultdict
import json
import numpy as np
import random
import zlib
import zstandard as zstd
from tqdm import tqdm

SEP={",",".",";","?","!","\n"}
M=250

def compress(s,comp):
    most_common_words=open("dict").read().split("\n")
    mcws=set(most_common_words)

    # Use most common chars in text as symbols
    mc=[m[0] for m in Counter(s).most_common()]
    g=set(mc)
    i=0
    C0,C1,C2=None,None,None
    while i<256:
        c=chr(i)
        if c not in g:
            if not C0:
                C0=c
            elif not C1:
                C1=c
            elif not C2:
                C2=c
            else:
                break
        i+=1
    if not any([C0,C1,C2]):
        return comp.compress(s.encode("utf-8","replace"))

    symbols=mc[:45]
    if " " in symbols:
        symbols.remove(" ")
    if "\n" in symbols:
        symbols.remove("\n")
    if "a" in symbols:
        symbols.remove("a")
    if "I" in symbols:
        symbols.remove("I")
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

    # Replace words with symbols
    words=s.split(" ")
    c=Counter(words)
    mc=c.most_common()

    Q="0"
    inds=[]
    if len(s)>300_000:
        reordered_top=sorted(most_common_words[:M],key=lambda word:-c[word])
        for w in reordered_top:
            inds.append(chr(most_common_words[:M].index(w)+ord(C2)))

        most_common_words = reordered_top + most_common_words[M:]
        Q="1"

    d={word:symbol for word,symbol in zip(most_common_words,symbols)}
    g=set(d.values())

    new_words=[]
    x=[]
    for i,word in enumerate(words):
        if "\n" in word:
            ws=word.split("\n")
            w=""
            for wo in ws:
                if wo in d:
                    w+=d[wo]+"\n"
                elif wo[:-1] in d and wo[-1] in SEP:
                    w+=d[wo[:-1]]+wo[-1]+"\n"
                elif wo in g:
                    w+=C0+wo+"\n"
                elif wo[:-1] in g and wo[-1] in SEP:
                    w+=C0+wo+"\n"
                else:
                    w+=wo+"\n"
            new_words.append(w[:-1])
        elif word in d: # Replace with symbol
            new_words.append(d[word])
            x.append("1")
        elif word[:-1] in d and word[-1] in SEP:
            new_words.append(d[word[:-1]]+word[-1])
            x.append("0")
        elif word in g: # Word is a used symbol, add a marker
            new_words.append(C0+word)
        elif word[:-1] in g and word[-1] in SEP:
            new_words.append(C0+word)
        else: # Default case, word is not common
            new_words.append(word)

    # To decompress, we need one char symbols and new words
    v=Q+C1.join([
        C0+C2,
        "".join(one_char_symbols),
        " ".join(new_words).replace("  ",C2),
        "".join(inds),
    ])

    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    d=zstd.decompress(b).decode("utf-8","replace")
    Q,C0,C2,C1=d[0],d[1],d[2],d[3]
    symbols,new_words,_map=d[4:].split(C1)
    symbols=list(symbols)
    new_words=new_words.replace(C2,"  ").split(" ")
    m=set(_map)

    most_common_words=open("dict").read().split("\n")
    if Q:
        most_common_words=[most_common_words[ord(_m)-ord(C2)] for _m in _map]+most_common_words[M:]

    t=symbols[:]
    for l0 in t:
        for l1 in t:
            if l1 in SEP:
                continue
            symbols.append(l0+l1)

    for l0 in t:
        for l1 in t:
            for l2 in t:
                if l2 in SEP:
                    continue
                symbols.append(l0+l1+l2)

    d={symbol:word for symbol,word in zip(symbols,most_common_words)}
    h={symbols[i]:i for i in range(len(d))}

    words=[]
    for word in new_words:
        if "\n" in word:
            ws=word.split("\n")
            w=""
            for wo in ws:
                if wo in d:
                    w+=d[wo]+"\n"
                elif wo[:-1] in d and wo[-1] in SEP:
                    w+=d[wo[:-1]]+wo[-1]+"\n"
                elif len(wo)>0 and wo[0]==C0:
                    w+=wo[1:]+"\n"
                else:
                    w+=wo+"\n"
            words.append(w[:-1])
        elif word in d: # Symbol used, replace with original word
            words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            words.append(d[word[:-1]]+word[-1])
        elif len(word)>0 and word[0]==C0: # Marker
            words.append(word[1:])
        else: # Default case, word was not replaced
            words.append(word)
    return " ".join(words)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--f",help="File")
    parser.add_argument("--e",help="Encoding")
    args=parser.parse_args()

    # Read dickens
    s=open(args.f,encoding=args.e).read()

    f=open("s","w")
    f.write(s)
    f.close()

    comp=zstd.ZstdCompressor(level=1)

    # Compress with our custom algorithm
    b=compress(s,comp)
    print(len(b))

    f=open("compressed","wb")
    f.write(b)
    f.close()

    # Decompress with our custom algorithm
    _s=decompress(b)

    # Assert equality
    assert _s==s

