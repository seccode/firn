import zstandard as zstd

def compress(s,comp):
    s=s.replace("  ",chr(0))
    mcw=open("dict").read().split("\n")[14:]
    d={m:"0"*(i+1) for i,m in enumerate(mcw)}
    words=s.split(" ")
    x=[]
    y=[]
    for word in words:
        if word in d:
            x.append(d[word])
        else:
            x.append("")
            y.append(word)
    x="1".join(x)
    x=x.replace("0"*16,"2")
    x=x.replace("2"*18,"3")
    return comp.compress(x.encode()),comp.compress(" ".join(y).encode("utf-8","replace"))

def decompress(x, y):
    x=zstd.decompress(x).decode()
    y=zstd.decompress(y).decode("utf-8","replace").split(" ")
    mcw=open("dict").read().split("\n")[14:]
    d={"0"*(i+1):m for i, m in enumerate(mcw)}
    x=x.replace("3","2"*18)
    x=x.replace("2","0"*16)
    words=[]
    i=0
    c=0
    while i < len(x):
        if x[i]=="1":
            if c>0:
                words.append(d["0"*c])
            else:
                words.append(y.pop(0))
            c=0
        elif x[i]=="0":
            c+=1
        i+=1
    if c>0:
        words.append(d["0"*c])
    else:
        words.append(y.pop())
    return " ".join(words).replace(chr(0),"  ")

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()[:80000]
    f=open("s","w")
    f.write(s)
    f.close()
    comp=zstd.ZstdCompressor(level=22)
    _b=comp.compress(s.encode("utf-8","replace"))
    f=open("1","wb")
    f.write(_b)
    f.close()
    x,y=compress(s,comp)
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(x+y))+" bytes")
    print(str(round(100*(len(_b)-len(x+y))/len(_b),2))+"% improvement over zstd")
    print("************************************************\n")
    f=open("2","wb")
    f.write(x+y)
    f.close()
    _s=decompress(x,y)
    assert _s==s
