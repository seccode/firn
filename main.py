import argparse
from collections import Counter, defaultdict
import json
import numpy as np
import random
import zlib
import zstandard as zstd
from tqdm import tqdm

def compress(s):
    most_common_words=open("dict").read().split("\n")
    mcws=set(most_common_words)
    words=s.split(" ")
    ws=set(words)
    b=[]
    n=[]
    for word in most_common_words:
        if word in ws:
            n.append(word)
            b.append("0")
        else:
            b.append("1")
    ws=set(words)
    symbols=[]
    for i in range(256):
        for j in range(len(ws)//100):
            symbols.append("0"*j+chr(i)+"0"*(len(ws)//100-j))
    d={word:symbol for word,symbol in zip(n,symbols)}
    new_words=[]
    j=len(d)
    e=set()
    for word in words:
        if word in d:
            new_words.append(d[word])
        else:
            e.add(word)
            d[word]=symbols[j]
            new_words.append(d[word])
            j+=1

    print(len(zstd.compress("".join(words).encode("utf-8","replace"),level=1)))

    x=list("".join(new_words))
    m=500/(len(ws)//100)
    inds=[]
    last=0
    for i in tqdm(range(100_000)):
        samples=random.sample(x,100)
        if samples.count("0")==100:
            inds.append(chr(i-last))
            last=i
    print(len(inds)*100/len(x))

    v=" ".join(list(e))+\
        "".join(inds)+\
        "".join(b)

    return zstd.compress(v.encode("utf-8","replace"),level=1)


def decompress(b):
    d_str=zstd.decompress(b).decode("utf-8","replace")
    words=[]
    return " ".join(words)


if __name__ == "__main__":
    s=open("dickens",encoding="latin-1").read()[50_000:100_000]

    with open("s","w") as f:
        f.write(s)

    b=compress(s)
    print(len(b))

    _s=decompress(b)
    assert _s==s
