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
        while j%len(x) not in seen and x[j%len(x)]=="0" and len(seen)<300:
            seen.add(j%len(x))
            j+=i
        if len(seen)==300:
            seeds.append(chr(i-last))
            last=i
            t.update(seen)
    y=[]
    for i in range(len(x)):
        if i not in t:
            y.append(x[i])
    v=chr(1114110).join([
        chr(len(x)),
        "".join(seeds),
        " ".join(mc)
    ])
    return comp.compress("".join(y).encode()),comp.compress(v.encode("utf-8","replace"))

def decompress(y,b):
    y=list(zstd.decompress(y).decode())
    d=zstd.decompress(b).decode("utf-8","replace")
    _x,seeds,mc=d.split(chr(1114110))
    d={"0"*i:m for i,m in enumerate(mc)}
    x=[]
    inds=set()
    o=ord(_x)
    for seed in seeds:
        j=ord(seed)
        for i in range(300):
            inds.add((j*i)%o)

    #TODO:Fix why these values aren't the same
    print(o)
    print(len(y)+len(inds))

    for i in range(o):
        if i in inds:
            x.append("0")
        else:
            x.append(y.pop())
    x="".join(x)
    words=[]
    for z in x.split("1"):
        words.append(d[z])
    s=" ".join(words)
    return s

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()[:1000]
    comp=zstd.ZstdCompressor(level=22)
    _b=comp.compress(s.encode("utf-8","replace"))
    f=open("1","wb")
    f.write(_b)
    f.close()
    y,b=compress(s,comp)
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(y)+len(b))+" bytes")
    print(str(round(100*(len(_b)-(len(y)+len(b)))/len(_b),2))+"% improvement over zstd")
    print("************************************************\n")
    f=open("y","wb")
    f.write(y)
    f.close()
    f=open("b","wb")
    f.write(b)
    f.close()
    _s=decompress(y,b)
    assert _s==s
