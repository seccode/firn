I stand on the shoulders of giants; I would like to acknowledge the following people whose algorithms/work I build on top of:
- David Huffman (Huffman coding)
- Abraham Lempel and Jacob Ziv (LZ77)
- Jarek Duda (ANS)
- Yann Collet (FSE)

## Firn, definition:
granular snow, especially on the upper part of a glacier, where it has not yet been _compressed_ into ice.

<img src="img.png" alt="firn" width="400">

# Usage
```
python firn.py --f <file> --e <encoding>
```

# How it works
Firn uses a subset of most common chars in the text as dictionary replacement symbols using 1, 2, and 3 char combinations. By restricting the replacement chars to a subset of chars present in the text, we improve compression.

# Results on 50KB of dickens text
| Compressor | Compressed Size (Bytes) | Improvement (%) |
|------------|--------------------------|-----------------|
| Firn (with dictionary trained on enwik9) + zstd (level 1)       | 18,730                   | **13.15%**        |
| zstd (level 1, with dictionary trained on enwik9) | 21,565                | -               |

# Limitations
Works well for readable text-based files under 5MB

