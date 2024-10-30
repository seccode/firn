from collections import Counter,defaultdict
import zlib

def compress(s):
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")
    g=set(most_common_words)

    words=s.split(" ")
    new_words=[]
    d=defaultdict(set)
    j=set([m[0] for m in Counter(s).most_common()][:28])
    h={}
    x=[]
    for word in words:
        if word in g and any(c in word for c in j):
            w=word
            for _j in j:
                w=w.replace(_j,"")
            if word not in h:
                h[word]=len(d[w])
            x.append(chr(h[word]+1))
            d[w].add(word)
            new_words.append(w)
        else:
            new_words.append(word)
    v=chr(0).join([
        " ".join(new_words).replace("  ",chr(0)),
        "".join(x)
    ])
    return zlib.compress(v.encode("utf-8"),level=9)

def decompress(b):
    new_words=zlib.decompress(b).decode("utf-8")
    words=[]
    return " ".join(words)

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()[:10_000_000] # Take first chunk of text

    f=open("s","w")
    f.write(s)
    f.close()

    _b=zlib.compress(s.encode("utf-8","replace"),level=9)

    # Compress with our custom algorithm
    b=compress(s)

    # Print results
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(b))+" bytes")
    print(str(round(100*(len(_b)-len(b))/len(_b),2))+"% improvement over zstd")
    print("************************************************\n")

    # Decompress with our custom algorithm
    _s=decompress(b)

    # Assert equality
    assert _s==s
