from collections import Counter
import zstandard as zstd

N=10

def compress(s,comp):
    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")

    h={word:i for i,word in enumerate(most_common_words[:N])}
    j={i:word for i,word in enumerate(most_common_words[:N])}

    words=s.split(" ")
    f={word:float("inf") for word in most_common_words[:N]}
    for i in range(1,len(words)):
        if words[i-1] in h and words[i] in h:
            f[words[i-1]]=min(f[words[i-1]],h[words[i]])
    new_words=[words[0]]
    for i in range(1,len(words)):
        if words[i-1] in h and words[i] in h and f[words[i-1]]!=float("inf"):
            new_words.append(j[h[words[i]]-f[words[i-1]]])
        else:
            new_words.append(words[i])
    x=[]
    for v in f.values():
        if v==float("inf"):
            x.append(chr(0))
        else:
            x.append(chr(v))

    # Use most common chars in text as symbols
    symbols=[m[0] for m in Counter(s).most_common()][:35]
    symbols.remove(" ")
    one_char_symbols=symbols[:]

    # Add two char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            for l2 in one_char_symbols:
                symbols.append(l0+l1+l2)

    # Map most common words to symbols
    d={word:symbol for word,symbol in zip(most_common_words,symbols)}
    g=set(d.values())

    # Replace words with symbols
    new_new_words=[]
    for word in new_words:
        if word in d: # Replace with symbol
            _d=d[word]
            if len(_d)==1:
                new_new_words.append(_d)
            else:
                new_new_words.append(_d)
        elif word in g: # Word is a used symbol, add a marker
            new_new_words.append(chr(0)+word)
        else: # Default case, word is not common
            new_new_words.append(word)

    # To decompress, we need one char symbols and new words
    v=chr(1).join([
        "".join(x),
        "".join(one_char_symbols),
        " ".join(new_new_words),
    ])

    # Return zstd compressed object
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    # zstd decompress
    x,symbols,new_new_words=zstd.decompress(b).decode("utf-8","replace").split(chr(1))
    symbols=list(symbols)
    new_new_words=new_new_words.split(" ")

    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
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

    new_words=[]
    for word in new_new_words:
        if word in d: # Symbol used, replace with original word
            new_words.append(d[word])
        elif len(word)>0 and word[0]==chr(0): # Marker for used symbol
            new_words.append(word[1:])
        else: # Default case, word was not replaced
            new_words.append(word)

    h={word:i for i,word in enumerate(most_common_words[:N])}
    j={i:word for i,word in enumerate(most_common_words[:N])}

    f={}
    for i,_x in enumerate(x):
        if _x!=chr(0):
            f[j[i]]=ord(_x)

    words=[new_words[0]]
    for i in range(1,len(new_words)):
        if words[-1] in h and new_words[i] in h:
            words.append(j[f[words[-1]]+h[new_words[i]]])
        else:
            words.append(new_words[i])
    return " ".join(words)

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()[:30_000] # Take first chunk of text

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
