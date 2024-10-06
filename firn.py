from collections import Counter,defaultdict
import numpy as np
from tqdm import tqdm
import zstandard as zstd

def compress(s,comp):
    words=s.split(" ")
    mc=[m[0] for m in Counter(words).most_common()]
    d={m:"0"*i for i,m in enumerate(mc)}
    x=[]
    for word in words:
        x.append(d[word])
    x="1".join(x)
    seeds=[]
    t=set()
    last=0
    for i in tqdm(range(1,len(x)-1)):
        j=0
        seen=set()
        seeds=[]
        while j%len(x) not in seen and x[j%len(x)]=="0" and len(seen)<800:
            seen.add(j%len(x))
            j+=i
        if len(seen)==800:
            seeds.append(chr(i-last))
            last=i
            t.update(seen)
    y=[]
    for i in range(len(x)):
        if i not in t:
            y.append(x[i])
    v=chr(1114110).join([
        "".join(seeds),
        " ".join(mc)
    ])
    return comp.compress("".join(y).encode())+comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    v=zstd.decompress(b).decode("utf-8","replace")
    words=[]
    s=" ".join(words)
    return s

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()[:10000]
    comp=zstd.ZstdCompressor(level=22)
    b=comp.compress(s.encode("utf-8","replace"))
    f=open("1","wb")
    f.write(b)
    f.close()
    b=compress(s,comp)
    f=open("2","wb")
    f.write(b)
    f.close()
    _s=decompress(b)
    assert _s==s
