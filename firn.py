from collections import Counter,OrderedDict
from tqdm import tqdm
import zstandard as zstd

def get_symbols():
    t=["e","t","o","n","i","h","s","r","d","l","u","m",",","w","c","f","g","y","p","b","'","v","k","-","M",'"',";","S","!","H","C","x","W","D","?"]
    a=t[:]
    for l0 in a:
        for l1 in a:
            t.append(l0+l1)
    return t

def compress(s,C,possible):
    comp=zstd.ZstdCompressor(level=22)
    if possible:
        words=s.split(" ")
        c=Counter(words).most_common()
        d=OrderedDict()
        i=0
        j=0
        t=get_symbols()
        while i<len(t):
            if len(c[j][0])==1 or \
                (len(c[j][0])<=len(t[i])):
                j+=1
            else:
                d[c[j][0]]=t[i]
                i+=1
                j+=1
        y=set(d.values())
        r=[]
        for i,word in tqdm(enumerate(words),total=len(words)):
            if word in d:
                if i==0:
                    r.append(d[word])
                else:
                    r.append(" "+d[word])
            else:
                if word in y:
                    if i==0:
                        r.append(C+word)
                    else:
                        r.append(" "+C+word)
                else:
                    if i==0:
                        r.append(word)
                    else:
                        r.append(" "+word)
        x="^".join(d.keys())+"`"+"".join(r)
        c=comp.compress(x.encode("utf-8","replace"))
    else:
        c=comp.compress(s.encode("utf-8","replace"))
    return c

def decompress(c,C):
    d=zstd.decompress(c).decode("utf-8","replace")
    split_string=d.split("`",1)
    dic=split_string[0].split("^")
    text=split_string[1]
    words=text.split(" ")
    t=get_symbols()
    d=OrderedDict()
    for i,S in enumerate(t[:len(dic)]):
        d[S]=dic[i]
    j=set(d.keys())
    res=[]
    for word in words:
        if word[1:] in d and word[0]==C:
            res.append(word[1:])
        elif word in d:
            res.append(d[word])
        else:
            res.append(word)
    s=" ".join(res)
    return s

if __name__=="__main__":
    s=open("dickens",encoding="Windows-1252").read()
    comp=zstd.ZstdCompressor(level=22)
    b=comp.compress(s.encode("utf-8","replace"))
    f=open("1","wb")
    f.write(b)
    f.close()
    t=get_symbols()
    i=420
    possible=True
    word_set=set(s.split(" "))
    while True:
        found=False
        try:
            for S in t:
                if chr(i)+S in word_set:
                    found=True
                    break
        except:
            possible=False
        if not found:
            break
        i+=1
    C=chr(i)
    b=compress(s,C,possible)
    f=open("2","wb")
    f.write(b)
    f.close()
    _s=decompress(b,C)
    assert _s==s
