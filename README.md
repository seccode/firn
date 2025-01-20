
## Firn, definition:
Granular snow, especially on the upper part of a glacier, where it has not yet been _compressed_ into ice.

<img src="img.png" alt="firn" width="400">

# Usage
```
python firn.py --f <file> --e <encoding>
```

# How it works
Firn uses a sorted subset of most common chars in the text as dictionary replacement symbols using 1, 2, and 3 char combinations. By restricting the replacement chars to a subset of chars present in the text, compression is improved.

Using a sorted subset of chars increases the homogeneity of the transformed text, making it easier to compress.

# Results on 50KB of dickens text
| Compressor | Compressed Size (Bytes) | Improvement (%) |
|------------|--------------------------|-----------------|
| Firn (with dictionary trained on enwik9) + zstd (level 1)       | 16,888                   | **21.69%**        |
| zstd (level 1, with dictionary trained on enwik9) | 21,565                | -               |

# Limitations
Works well for readable text-based files

# Donations
If you would like to sponsor further development of this compressor, please make donations via the Ethereum network:
0x258db63bc7ea9B511D1576Aac5c41a7C8d1193D4
Thank you!

