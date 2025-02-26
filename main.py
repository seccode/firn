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
    symbols=[]
    for i in range(256):
        for j in range(len(ws)//200):
            symbols.append("0"*j+chr(i)+"0"*(len(ws)//200-j))
    d={word:symbol for word,symbol in zip(ws,symbols)}
    new_words=[]
    for word in words:
        new_words.append(d[word])

    print(len(zstd.compress("".join(words).encode("utf-8","replace"),level=1)))

    x=list("".join(new_words))
    m=500/(len(ws)//200)
    inds=[]
    for i in range(10_000):
        samples=random.sample(x,75)
        if samples.count("0")==75:
            inds.append(i)
            print(i)

    v=" ".join(set(words))

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
