import num2fawords
import regex
from parsivar import FindStems

num_words = [
    "صفر", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه",
    "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده",
    "ده", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود",
    "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد", 
    "هزار", "میلیون", "میلیارد", "تریلیون"
    ]


def text2int(textnum, numwords={}):
    if not numwords:
        units       = ["صفر", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
        tenlings    = ["یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده",]
        tens        = ["ده", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
        hundreds    = ["صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
        scales      = ["هزار", "میلیون", "میلیارد", "تریلیون"]

        numwords["و"] = (1, 0)
        for idx, word in enumerate(units):      numwords[word] = (1, idx)
        for idx, word in enumerate(tenlings):   numwords[word] = (1, list(range(11, 20))[idx])
        for idx, word in enumerate(tens):       numwords[word] = (1, (idx+1) * 10)
        for idx, word in enumerate(hundreds):   numwords[word] = (1, (idx+1) * 100)
        for idx, word in enumerate(scales):     numwords[word] = (10 ** ((idx+1) * 3 or 2), 0)

    current = result = 0
    
    textnum = FindStems().convert_to_stem(textnum)
    
    dummy_textnum = textnum.split()
    # handling adversary cases, i.e., 'هفت و پانصد'
    if 'و' in dummy_textnum and 'هزار' not in dummy_textnum:
        textnum = textnum.replace('و', 'هزار و')

    for word in textnum.split():
        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0
    
    return result + current


def tokenize(text):

    markers = [] # start and end of a number occurence
    words = regex.sub(
        # there is a space or an end of a string after it
        r"[^\w#@&]+(?=\s|$)|"
        # there is a space or beginning of a string before it
        # not followed by a number
        r"(\s|^)[^\w#@&]+(?=[^0-9\s])|"
        # not in between numbers and not . or @ or & or - or #
        # e.g. 10'000.00 or blabla@gmail.com
        # and not url characters
        r"(?<=[^0-9\s])[^\w._~:/?#\[\]()@!$&*+,;=-]+(?=[^0-9\s])",
        " ",
        text,
    ).split()

    mid_number_flag = False
    
    for i, word in enumerate(text.split()):
        if word.isdigit():
            words[i] = num2fawords.words(word)
            text = text.replace(word, words[i])
    
    words = text.split()

    for i, word in enumerate(words):
        if mid_number_flag:
            if word in num_words+['و']:
                if i == len(words)-1:
                    end = len(''.join(text.split()[:i])) + i + len(text.split()[i])
                    markers.append((start, end))
                mid_number_flag = True
            else:
                mid_number_flag = False
                end = len(''.join(text.split()[:i])) + i
                markers.append((start, end))
        else: # begining of a number
            if word in num_words:
                start = len(''.join(words[:i])) + i
                mid_number_flag = True
    mappings = {}

    if len(markers) > 0:
        for loc in markers:
            mappings[text[loc[0]: loc[1]]] = text2int(text[loc[0]: loc[1]])
        for key in mappings:
            text = text.replace(key, ' '+str(mappings[key])+' ')
    return text
