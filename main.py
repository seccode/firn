from collections import defaultdict,Counter
import json
import sys
from tqdm import tqdm
import zstandard as zstd

def compress(s):
    comp=zstd.ZstdCompressor()
    separator="!!!!!!!!"
    while separator in s:
        separator+="!"

    words=s.split(" ")
    x=[]
    d=defaultdict(list)
    for word in tqdm(words):
        if word=="":
            x.append(chr(0))
        else:
            x.append(word[0])
            d[word[0]].append(word)

    r={}
    e={}
    for k,v in tqdm(d.items()):
        mc=Counter(v).most_common()
        g={}
        l=[]
        for i,m in enumerate(mc):
            g[m[0]]=i
            l.append(m[0])
        r[k]=l
        e[k]=g

    k=[]
    for word in tqdm(words):
        if word=="":
            pass
        else:
            k.append(chr(e[word[0]][word]))

    sc="".join(k)+"".join(x)+json.dumps(r,separators=(",",":"))
    return comp.compress(sc.encode("utf-8","replace")),k,x,r

def decompress(k,x,r):
    words=[]
    j=0
    for i in range(len(x)):
        if x[i]==chr(0):
            words.append("")
        else:
            words.append(r[x[i]][ord(k[j])])
            j+=1
    return " ".join(words)

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()
    b,k,x,r=compress(s)
    f=open("compressed","wb")
    f.write(b)
    f.close()
    _s=decompress(k,x,r)
    assert _s[:1000]==s[:1000]



