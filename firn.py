import ast
from collections import defaultdict,Counter
import json
import zstandard as zstd

def compress(s):
    comp=zstd.ZstdCompressor()
    sp="qqqqq"
    while sp in s:
        sp+="q"
    words=s.split(" ")
    x=[]
    d=defaultdict(list)
    for word in words:
        if word=="":
            x.append(chr(0))
        else:
            x.append(word[0])
            d[word[0]].append(word)

    r={}
    e={}
    for k,v in d.items():
        mc=Counter(v).most_common()
        g={}
        l=[]
        for i,m in enumerate(mc):
            g[m[0]]=i
            l.append(m[0])
        r[k]=l
        e[k]=g

    k=[]
    for word in words:
        if word=="":
            pass
        else:
            k.append(chr(e[word[0]][word]))

    sc="".join(k)+sp+"".join(x)+sp+json.dumps(r,separators=(",",":"))
    return comp.compress(sc.encode("utf-8","replace")),sp

def decompress(b,sp):
    k,x,r=zstd.decompress(b).decode("utf-8","replace").split(sp)
    r=ast.literal_eval(r)
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
    s=open("dickens",encoding="Windows-1252").read()
    b,sp=compress(s)
    f=open("compressed","wb")
    f.write(b)
    f.close()
    _s=decompress(b,sp)
    f=open("decompressed","w",encoding="Windows-1252")
    f.write(_s)
    f.close()



