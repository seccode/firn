from collections import Counter,defaultdict
from tqdm import tqdm
import zstandard as zstd

def compress(s):
    mc=Counter(s).most_common()
    words=s.split(" ")
    word_set=set(words)
    g=set()
    for m in mc[:1000]:
        if m[0] in word_set:
            g.add(m[0])
    new_words=[]
    for word in words:
        if word in g:
            new_words.append(word+chr(0))
        else:
            new_words.append(word)
    return " ".join(new_words)

def decompress(b):
    words=[]
    for word in b.split(" "):
        if chr(0) in word:
            words.append(word[:-1])
        else:
            words.append(word)
    return " ".join(words)

if __name__=="__main__":
    s=open("dickens",encoding="latin-1").read()
    b=compress(s)
    f=open("compressed","w")
    f.write(b)
    f.close()
    _s=decompress(b)

    assert _s==s
