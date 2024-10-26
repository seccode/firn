import random
import zstandard as zstd

def compress(s,comp):
    o=f=s.split(".")[1001].split(" ")
    x=len(comp.compress(" ".join(f).encode("utf-8")))
    print(x)
    mn=x
    for i in range(1_000):
        f=o
        random.seed(i)
        random.shuffle(f)
        x=len(comp.compress(" ".join(f).encode("utf-8")))
        if x<mn:
            mn=x
            print(x)
    a
    # Return zstd compressed object
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    # zstd decompress
    symbols,new_words=zstd.decompress(b).decode("utf-8","replace").split(chr(300))
    symbols=list(symbols)
    new_words=new_words.split(" ")

    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")[14:]
    most_common_words.remove("")

    # Use most common chars in text as symbols
    t=symbols[:]
    for l0 in t:
        for l1 in t:
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in t:
        for l1 in t:
            for l2 in t:
                symbols.append(l0+l1+l2)

    # Map most symbols to most common words
    d={symbol:word for symbol,word in zip(symbols,most_common_words)}

    # Replace symbols with original words
    words=[]
    for word in new_words:
        if word in d: # Symbol used, replace with original word
            words.append(d[word])
        elif len(word)>0 and word[0]==chr(0): # Marker
            words.append(word[1:])
        else: # Default case, word was not replaced
            words.append(word)
    return " ".join(words)

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()[:1000000] # Take first chunk of text

    # Save chunk for testing with other compressors
    f=open("s","w")
    f.write(s)
    f.close()

    # Compress purely with zstd for comparison
    comp=zstd.ZstdCompressor(level=22) # Use highest level 22
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
