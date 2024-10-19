## Firn, definition:
granular snow, especially on the upper part of a glacier, where it has not yet been compressed into ice.

<img src="img.png" alt="firn" width="400">

# How it works
Firn uses a subset of most common chars in the text as dictionary replacement symbols using 1, 2, and 3 char combinations

# Results on 50KB of dickens text
| Compressor | Compressed Size (Bytes) | Improvement (%) |
|------------|--------------------------|-----------------|
| Firn + zstd (lvl 22)       | 18,374                   | **9.4%**        |
| zstd (lvl 22) | 19,460                | -               |

# Limitations
firn works well for file sizes under 100KB
