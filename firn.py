from collections import Counter,defaultdict
from tqdm import tqdm
import zstandard as zstd

def compress(s):
    comp=zstd.ZstdCompressor(level=22)
    words=s.split(" ")
    mc=Counter(words).most_common()
    g=defaultdict(dict)
    for m in tqdm(mc):
        if m[0]=="":
            continue
        g[m[0][0]][m[0]]=0
    d={}
    h=defaultdict(dict)
    u=defaultdict(dict)
    for k,v in tqdm(g.items()):
        i=0
        for word in v.keys():
            l=len(word)
            if l<2:
                continue
            if l in h[k] and l not in u[k]:
                u[k][l]=word
            else:
                h[k][l]=word
            d[word]=word[0]
    new_words=[]
    x=[]
    word_set=set(words)
    for word in tqdm(words):
        l=len(word)
        if word in d:
            w=word[0]+chr(l)
            if w in word_set:
                new_words.append(w+chr(0))
            else:
                new_words.append(w)
            if word==h[word[0]][l]:
                x.append("0")
            elif word==u[word[0]][l]:
                x.append("1")
        else:
            new_words.append(word)
    _h=[]
    for v in h.values():
        _h.extend(v.values())
    _u=[]
    for v in u.values():
        _u.extend(v.values())
    ws=[word for word in word_set if len(word)==2 or len(word)==3]
    sc=(chr(0)+chr(0)).join([" ".join(new_words),"".join(x)," ".join(_h)," ".join(_u)," ".join(ws)])
    return comp.compress(sc.encode("utf-8","replace"))

def decompress(b):
    sc=zstd.decompress(b).decode("utf-8","replace")
    new_words,x,_h,_u,ws=sc.split((chr(0)+chr(0)))
    ws=set(ws.split(" "))
    h=defaultdict(dict)
    for word in _h.split(" "):
        h[word[0]][len(word)]=word
    u=defaultdict(dict)
    for word in _u.split(" "):
        u[word[0]][len(word)]=word
    words=[]
    i=0
    for word in new_words.split(" "):
        l=len(word)
        if (l==2 or l==3) and word not in ws:
            o=ord(word[1])
            if x[i]=="0":
                words.append(h[word[0]][o])
            else:
                # TODO: fix bug
                words.append(u[word[0]][o])
            i+=1
    s=" ".join(words)
    return s

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()
    comp=zstd.ZstdCompressor(level=22)
    b=comp.compress(s.encode("utf-8","replace"))
    f=open("1","wb")
    f.write(b)
    f.close()

    b=compress(s)
    f=open("2","wb")
    f.write(b)
    f.close()
    _s=decompress(b)

    assert _s==s
