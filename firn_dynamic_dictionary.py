from collections import Counter
import zstandard as zstd

def compress(s,comp):
    # Get most common words
    words=s.split(" ")
    most_common_words=[m[0] for m in Counter(words).most_common() if m[1]>15]
    most_common_words.remove("")

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
    new_words=[]
    for word in words:
        if word in d: # Replace with symbol
            _d=d[word]
            if len(_d)==1:
                new_words.append(_d)
            else:
                new_words.append(_d)
        elif word in g: # Word is a used symbol, add a marker
            new_words.append(chr(0)+word)
        else: # Default case, word is not common
            new_words.append(word)

    # To decompress, we need one char symbols and new words
    v=chr(300).join([
        "".join(one_char_symbols),
        " ".join(new_words),
        " ".join(most_common_words),
    ])

    # Return zstd compressed object
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    # zstd decompress
    symbols,new_words,most_common_words=zstd.decompress(b).decode("utf-8","replace").split(chr(300))
    symbols=list(symbols)
    most_common_words=most_common_words.split(" ")
    new_words=new_words.split(" ")

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
    s=open("dickens",encoding="latin-1").read()[:1_000_000] # Take first chunk of text

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
