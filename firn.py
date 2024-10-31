from collections import Counter
import zlib
import zstandard as zstd

SEP={",",".",";","?","!"}

def compress(s,comp):
    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")

    # Use most common chars in text as symbols
    symbols=[m[0] for m in Counter(s).most_common()][:35]
    symbols.remove(" ")
    one_char_symbols=symbols[:]

    # Add two char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            if l1 in SEP:
                continue
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in one_char_symbols:
        for l1 in one_char_symbols:
            for l2 in one_char_symbols:
                if l2 in SEP:
                    continue
                symbols.append(l0+l1+l2)

    # Map most common words to symbols
    d={word:symbol for word,symbol in zip(most_common_words,symbols)}
    g=set(d.values())

    # Replace words with symbols
    words=s.split(" ")
    new_words=[]
    m=[]
    for i,word in enumerate(words):
        if word in d: # Replace with symbol
            new_words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            new_words.append(d[word[:-1]]+word[-1])
        elif word in g: # Word is a used symbol, add a marker
            new_words.append(chr(0)+word)
        elif word[:-1] in g and word[-1] in SEP:
            new_words.append(chr(1)+word)
        else: # Default case, word is not common
            new_words.append(word)
        if word[1:] in d:
            m.append(ord(word[0]))

    # To decompress, we need one char symbols and new words
    v=chr(2).join([
        "".join(one_char_symbols),
        " ".join(new_words),
    ])

    # Return zstd compressed object
    #return zlib.compress(v.encode("utf-8","replace"),level=-1)
    return comp.compress(v.encode("utf-8","replace"))

def decompress(b):
    # zstd decompress
    #symbols,new_words=zlib.decompress(b).decode("utf-8","replace").split(chr(2))
    symbols,new_words=zstd.decompress(b).decode("utf-8","replace").split(chr(2))
    symbols=list(symbols)
    new_words=new_words.split(" ")

    # Get most common words from predefined dictionary
    most_common_words=open("dict").read().split("\n")
    most_common_words.remove("")

    # Use most common chars in text as symbols
    t=symbols[:]
    for l0 in t:
        for l1 in t:
            if l1 in SEP:
                continue
            symbols.append(l0+l1)

    # Add three char symbols
    for l0 in t:
        for l1 in t:
            for l2 in t:
                if l2 in SEP:
                    continue
                symbols.append(l0+l1+l2)

    # Map most symbols to most common words
    d={symbol:word for symbol,word in zip(symbols,most_common_words)}

    # Replace symbols with original words
    words=[]
    for word in new_words:
        if word in d: # Symbol used, replace with original word
            words.append(d[word])
        elif word[:-1] in d and word[-1] in SEP:
            words.append(d[word[:-1]]+word[-1])
        elif len(word)>0 and word[0]==chr(0): # Marker
            words.append(word[1:])
        elif len(word)>0 and word[0]==chr(1): # Marker
            words.append(word[1:])
        else: # Default case, word was not replaced
            words.append(word)
    return " ".join(words)

if __name__=="__main__":
    # Read dickens
    s=open("dickens",encoding="latin-1").read()[:50_000] # Take first chunk of text

    f=open("s","w")
    f.write(s)
    f.close()

    comp=zstd.ZstdCompressor(level=22)
    #_b=zlib.compress(s.encode("utf-8","replace"),level=-1)
    _b=comp.compress(s.encode("utf-8","replace"))

    # Compress with our custom algorithm
    b=compress(s,comp)

    # Print results
    print("\n************************************************")
    print("Compressed "+str(len(s))+" bytes to "+str(len(b))+" bytes")
    print(str(round(100*(len(_b)-len(b))/len(_b),2))+"% improvement")
    print("************************************************\n")

    # Decompress with our custom algorithm
    _s=decompress(b)

    # Assert equality
    assert _s==s
