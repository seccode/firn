# firn
The firn data compression algorithm is to replace common words with short symbols. Even if short symbols such as "e" are already present in the text, though infrequent, we are able to use "e" as a replacement symbol by adding a special character to existing "e"'s.

## dickens dataset (Charles Dickens novels)
| Algorithm | Original Size | Compressed Size |
|----------------------|---------------|-----------------|
| firn+zstd (level 22) | 10.192 MB     | 2.788 MB        |
| zstd (level 22)      | 10.192 MB     | 2.832 MB        |
| firn+zstd            | 10.192 MB     | 3.393 MB        |
| zstd                 | 10.192 MB     | 3.631 MB        |


