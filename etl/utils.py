import datetime
import jellyfish

def get_similar(list : [str],word : str):
    return max([(jellyfish.jaro_similarity(word, w),w) for w in list])[1]

def similarity(word : str, right_word : str):
    return jellyfish.jaro_similarity(right_word, word)

def working_hours():
    '''Returns True if current time is between 8h and 19h'''
    now = datetime.datetime.now()
    return now.hour >= 8 and now.hour < 19