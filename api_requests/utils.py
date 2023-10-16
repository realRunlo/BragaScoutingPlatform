import jellyfish

def get_similar(list : [str],word : str):
    return max([(jellyfish.jaro_similarity(word, w),w) for w in list])[1]