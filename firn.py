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
    h=set(mc)
    i=0
    C0,C1=None,None
    reserved={"0","1"}
    while i<256:
        c=chr(i)
        if c not in h and c not in reserved:
            if not C0:
                C0=c
            elif not C1:
                C1=c
            else:
                break
        i+=1
    if not all([C0,C1]):
        return comp.compress(s.encode("utf-8","replace"))

    if len(s)>300_000:
        symbols=mc[:20]
    else:
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
        for l0 in one_char_symbols:
            for l1 in one_char_symbols:
                for l2 in one_char_symbols:
                    for l3 in one_char_symbols:
                        if l3 in SEP:
                            continue
                        symbols.append(l0+l1+l2+l3)

        reordered_top=sorted(most_common_words[:M],key=lambda word:-c[word])
        for w in reordered_top:
            inds.append(chr(most_common_words[:M].index(w)+ord(C1)+1))

        most_common_words = reordered_top + most_common_words[M:]
        Q="1"

    d={word:symbol for word,symbol in zip(most_common_words,symbols)}
    g=set(d.values())

    new_words=words[:2]
    x=[]
    i=2
    for word in words[2:]:
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
        elif "-" in word:
            ws=word.split("-")
            w=""
            for wo in ws:
                if wo in d:
                    w+=d[wo]+"-"
                elif wo[:-1] in d and wo[-1] in SEP:
                    w+=d[wo[:-1]]+wo[-1]+"-"
                elif wo in g:
                    w+=C0+wo+"-"
                elif wo[:-1] in g and wo[-1] in SEP:
                    w+=C0+wo+"-"
                else:
                    w+=wo+"-"
            new_words.append(w[:-1])
        elif word in d: # Replace with symbol
            new_words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            new_words.append(d[word[:-1]]+word[-1])
        elif word in g: # Word is a used symbol, add a marker
            new_words.append(C0+word)
        elif word[:-1] in g and word[-1] in SEP:
            new_words.append(C0+word)
        else: # Default case, word is not common
            new_words.append(word)
        i+=1

    nn=[]
    x=[]
    i=0
    for word in new_words:
        if word.count("\n")==1:
            wos=word.split("\n")
            nn.append(wos[0])
            nn.append(wos[1])
            x.append(chr(i+ord(C1)+1))
            i=0
        else:
            nn.append(word)
            i+=1
    v=C1.join([
        C0,
        "".join(inds),
        "".join(x),
        " ".join(one_char_symbols),
        " ".join(nn),
    ])+Q

    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    d=zstd.decompress(b).decode("utf-8","replace")
    Q,C0,C1=d[-1],d[0],d[1]
    _map,x,symbols,nn=d[2:-1].split(C1)
    symbols=symbols.split(" ")
    nn=nn.split(" ")
    new_words=[]
    i=0
    j=0
    count_since_newline=0
    while i<len(nn):
        if j<len(x):
            target=ord(x[j])-ord(C1)-1
        else:
            target=None
        if target is not None and count_since_newline==target and i+1<len(nn):
            new_words.append(nn[i]+"\n"+nn[i+1])
            i+=2
            j+=1
            count_since_newline=0
        else:
            new_words.append(nn[i])
            i+=1
            count_since_newline+=1

    m=set(_map)

    most_common_words=open("dict").read().split("\n")
    if Q=="1":
        most_common_words=[most_common_words[ord(_m)-ord(C1)-1] for _m in _map]+most_common_words[M:]

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

    if Q=="1":
        for l0 in t:
            for l1 in t:
                for l2 in t:
                    for l3 in t:
                        if l3 in SEP:
                            continue
                        symbols.append(l0+l1+l2+l3)

    d={symbol:word for symbol,word in zip(symbols,most_common_words)}

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
        elif "-" in word:
            ws=word.split("-")
            w=""
            for wo in ws:
                if wo in d:
                    w+=d[wo]+"-"
                elif wo[:-1] in d and wo[-1] in SEP:
                    w+=d[wo[:-1]]+wo[-1]+"-"
                elif len(wo)>0 and wo[0]==C0:
                    w+=wo[1:]+"-"
                else:
                    w+=wo+"-"
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

    comp=zstd.ZstdCompressor(level=22)

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

