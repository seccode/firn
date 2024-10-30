from collections import Counter,defaultdict
import time
from tqdm import tqdm
import zstandard as zstd

def compress(s,comp):
    most_common_words=open("dict").read().split("\n")
    g=set(most_common_words)

    words=s.split(" ")
    new_words=[]
    d=defaultdict(set)
    j=set([m[0] for m in Counter(s).most_common()][:30])
    h={}
    x=[]
    for word in tqdm(words):
        if (word in g or word[:-1] in g or word[1:] in g) and any(c in word for c in j):
            w=word
            for _j in j:
                w=w.replace(_j,"")
            if word in g:
                if word not in h:
                    h[word]=len(d[w])
                x.append(chr(h[word]+1))
                d[w].add(word)
            elif word[:-1] in g:
                if word[:-1] not in h:
                    h[word[:-1]]=len(d[w])
                x.append(chr(h[word[:-1]]+1))
                d[w].add(word[:-1])
            else:
                if word[1:] not in h:
                    h[word[1:]]=len(d[w])
                x.append(chr(h[word[1:]]+1))
                d[w].add(word[1:])
            new_words.append(w)
        elif word.count("\n")==1:
            l=word.split("\n")
            word0=l[0]
            word1=l[0]
            y=""
            if (word0 in g or word0[:-1] in g) and any(c in word0 for c in j):
                w=word0
                for _j in j:
                    w=w.replace(_j,"")
                if word0 in g:
                    if word0 not in h:
                        h[word0]=len(d[w])
                    x.append(chr(h[word0]+1))
                    d[w].add(word0)
                else:
                    if word0[:-1] not in h:
                        h[word0[:-1]]=len(d[w])
                    x.append(chr(h[word0[:-1]]+1))
                    d[w].add(word0[:-1])
                y+=w
            else:
                y+=word0
            y+="\n"
            if (word1 in g or word1[:-1] in g) and any(c in word1 for c in j):
                w=word1
                for _j in j:
                    w=w.replace(_j,"")
                if word1 in g:
                    if word1 not in h:
                        h[word1]=len(d[w])
                    x.append(chr(h[word1]+1))
                    d[w].add(word1)
                else:
                    if word1[:-1] not in h:
                        h[word1[:-1]]=len(d[w])
                    x.append(chr(h[word1[:-1]]+1))
                    d[w].add(word1[:-1])
                y+=w
            else:
                y+=word1
            new_words.append(y)
        else:
            new_words.append(word)

    v=chr(0).join([
        " ".join(new_words).replace("  ",chr(0)),
        "".join(x)
    ])
    #return zlib.compress(v.encode("utf-8"),level=9)
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    new_words=zlib.decompress(b).decode("utf-8")
    words=[]
    return " ".join(words)

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()

    f=open("s","w")
    f.write(s)
    f.close()

    comp=zstd.ZstdCompressor(level=22)
    _b=comp.compress(s.encode("utf-8","replace"))

    # Compress with our custom algorithm
    b=compress(s,comp)

    # Print results
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(b))+" bytes")
    print(str(round(100*(len(_b)-len(b))/len(_b),2))+"% improvement over zstd")
    print("************************************************\n")

    # Decompress with our custom algorithm
    _s=decompress(b)

    # Assert equality
    assert _s==s
