from collections import Counter,defaultdict
import time
from tqdm import tqdm
import zlib
import zstandard as zstd

def compress(s,comp):
    most_common_words=open("dict").read().split("\n")
    g=set(most_common_words)

    d=defaultdict(set)
    h={}
    words=s.split(" ")
    new_words=[]
    c=set([m[0] for m in Counter(s).most_common()][:20])
    x=[]
    for i,word in tqdm(enumerate(words),total=len(words)):
        if (word in g) and any(c in word for c in c):
            w=word
            for _c in c:
                w=w.replace(_c,"")
            if word in g:
                if word not in h:
                    h[word]=len(d[w])
                d[w].add(word)
                x.append(chr(h[word]+1))
            else:
                if word[:-1] not in h:
                    h[word[:-1]]=len(d[w])
                d[w].add(word[:-1])
                x.append(chr(h[word[:-1]]+1))
            new_words.append(w)
        elif word.count("\n")==1:
            wi=word.split("\n")
            word0=wi[0]
            word1=wi[1]
            y=""
            if (word0 in g) and any(c in word0 for c in c):
                w=word0
                for _c in c:
                    w=w.replace(_c,"")
                if word0 in g:
                    if word0 not in h:
                        h[word0]=len(d[w])
                    d[w].add(word0)
                    x.append(chr(h[word0]+1))
                else:
                    if word0[:-1] not in h:
                        h[word0[:-1]]=len(d[w])
                    d[w].add(word0[:-1])
                    x.append(chr(h[word0[:-1]]+1))
                y+=w
            else:
                y+=word0
            y+="\n"
            if (word1 in g) and any(c in word1 for c in c):
                w=word1
                for _c in c:
                    w=w.replace(_c,"")
                if word1 in g:
                    if word1 not in h:
                        h[word1]=len(d[w])
                    d[w].add(word1)
                    x.append(chr(h[word1]+1))
                else:
                    if word1[:-1] not in h:
                        h[word1[:-1]]=len(d[w])
                    d[w].add(word1[:-1])
                    x.append(chr(h[word1[:-1]]+1))
                y+=w
            else:
                y+=word1
            new_words.append(y)
        else:
            new_words.append(word)

    v=chr(0).join([
        " ".join(new_words),
        "".join(x),
    ])
    #return comp.compress(v.encode("utf-8"))
    return zlib.compress(v.encode("utf-8","replace"),level=-1)

def decompress(b):
    d_keys,new_new_words,x,t,m,z,q,sym=zlib.decompress(b).decode("utf-8").split(chr(600))
    new_new_words=new_new_words.replace(chr(0),"    ").split(" ")
    sym=list(sym)
    z=list(z)
    q=list(q)
    t=sym[:]
    for l0 in t:
        for l1 in t:
            sym.append(l0+l1)
    mc=d_keys.split(" ")
    d={}
    j=0
    for i in range(len(mc)):
        if j==len(sym):
            break
        if len(mc[i])>len(sym[j]):
            d[sym[j]]=mc[i]
            j+=1
    new_words=[]
    l=0
    r=0
    for i,word in enumerate(new_new_words):
        if len(z)>0 and chr(i-l)==z[0]:
            new_words.append(word)
            z.pop(0)
            l=i
        elif len(q)>0 and chr(i-r)==q[0]:
            new_words.append(d[word[:-1]]+word[-1])
            q.pop(0)
            r=i
        elif word in d:
            new_words.append(d[word])
        else:
            new_words.append(word)
    words=[]
    return new_words

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()[:10_000]

    f=open("s","w")
    f.write(s)
    f.close()

    comp=zstd.ZstdCompressor(level=22)
    #_b=comp.compress(s.encode("utf-8"))
    _b=zlib.compress(s.encode("utf-8"),level=-1)

    # Compress with the custom algorithm
    b=compress(s,comp)

    # Print results
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(b))+" bytes")
    print(str(round(100*(len(_b)-len(b))/len(_b),2))+"% improvement")
    print("************************************************\n")

    # Decompress with the custom algorithm
    _s=decompress(b)
    assert _s==n
    a

    # Assert equality
    assert _s==s
