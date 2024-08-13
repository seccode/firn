# firn
The firn data compression algorithm is to store the first letter of every word and a dictionary that maps first letters to all possible words. In addition, a string is stored to indicate which item in the possible word list corresponds to the word that belongs.

## dickens dataset (Charles Dickens novels)
| Algorithm | Original Size | Compressed Size | Compression Ratio |
|-----------|---------------|-----------------|-------------------|
| zstd      | 10.192 MB     | 3.633 MB        | 2.81x             |
| firn      | 10.192 MB     | 3.529 MB        | 2.89x             |

