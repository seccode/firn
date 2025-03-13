
## Firn, definition:
Granular snow, especially on the upper part of a glacier, where it has not yet been _compressed_ into ice.

<img src="img.png" alt="firn" width="400">

# Usage
```
python firn.py --f <file> --e <encoding>
```

# How it works
Firn uses a sorted subset of most common chars in the text as dictionary replacement symbols using 1, 2, 3, and sometimes 4 char combinations.

Using a sorted by frequency subset of chars increases the zipfian characteristics of the transformed text, making it easier to compress.

# Results on 50KB of dickens text
| Compressor | Compressed Size (Bytes) | Improvement (%) |
|------------|--------------------------|-----------------|
| Firn (with dictionary trained on enwik9) + zstd (level 1)       | 16,888                   | **21.69%**        |
| zstd (level 1, with dictionary trained on enwik9) | 21,565                | -               |

# Limitations
Works well for readable text-based files


This is a demonstration of the algorithm. Work is being done to create a production ready package. Also considering making a zstd fork with the change of offset,length being remapped to the most frequent bytes. This should make things more Zipfian-like. This is a work in progress so the most recent files might not be the most up to date code, the history stores all versions

