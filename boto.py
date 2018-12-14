"""
This is the template server side for ChatBot
"""
import json
import random
from textblob import TextBlob
from nltk.corpus import movie_reviews
from textblob.classifiers import NaiveBayesClassifier
from nltk.tokenize import word_tokenize
from bottle import route, run, template, static_file, request

# constants
with open("./swear_words/swear_words.txt") as f:
    SWEAR_WORDS = sorted(word.strip(" ") for line in f for word in line.split(','))
GREETING_KEYWORDS = ("hello", "hi", "greetings", "sup", "what's up", 'hey')
GREETING_RESPONSES = ["'sup bro", "hey", "*nods*", "hey you get my snap?"]
with open("./positive_quotes/positive_quotes.txt", encoding="utf-8") as f:
    POSITIVE_QUOTES = sorted(word.strip(" ") for line in f for word in line.split(';'))
EMERGENCY = 'You are not alone in this. I’m here for you. I will now automatically connect you with a human' \
            ' health professional. Eran health center communication: 1201 or 076-8844402 or info@eran.org.il'
DUO = ['kill myself', 'commit suicide']
TRIO = ['no one cares', "i do n't care", "i dont care"]
QUARTET = ["i 'm just tired", "im just tired", "i should just kill", "i want to disappear", "im just stressed out",
           "im not feeling good"]
QUINT = ["i just want to sleep", 'i cant keep doing this', "i ’m just stressed out",
         'what will heaven be like', "im having a hard time",
         "i feel so much better", "i ’m not feeling good"]
SEXTET = ["i just want to be done", "i just want to be alone", "i ’m having a hard time",
          "i ca n’t keep doing this"]
SEPTET = []
OCTET = ["i dont think ill be at school next", "i donâ\x80\x99t think iâ\x80\x99ll be at school next"]
NONET = ["if anything happens to me promise to take care", "i can’t imagine living the rest of my life",
         "i want to tell you something oh never mind", "i don’t think i ’ll be at school next",
         "i cant imagine living the rest of my life"]

NGRAM_DICT = {
    'DUO': 2,
    'TRIO': 3,
    'QUARTET': 4,
    'QUINT': 5,
    'SEXTET': 6,
    'SEPTET': 7,
    'OCTET': 8,
    'NONET': 9
}


@route('/', method='GET')
def index():
    return template("chatbot.html")


def find_pronoun(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    pronoun = None

    for word, part_of_speech in sent.pos_tags:
        # Disambiguate pronouns
        if part_of_speech == 'PRP' and word.lower() == 'you':
            pronoun = 'I'
        elif part_of_speech == 'PRP' and word.lower() == 'i':
            # If the user mentioned themselves, then they will definitely be the pronoun
            pronoun = 'You'
    return pronoun


def find_noun(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    noun = None

    for word, part_of_speech in sent.pos_tags:
        if part_of_speech == 'NN':
            return word.lower()
    return noun


def cursing_exists(user_text):
    words = user_text.split(" ")
    if any(word in SWEAR_WORDS for word in words):
        return 0.95, "I see you are very angry today, try rephrasing your thoughts without abusing words.", 'heartbroke'
    else:
        return 0, None, None


def check_for_greeting(sentence):
    """If any of the words in the user's input was a greeting, return a greeting response"""
    for word in sentence.split(' '):
        if word.lower() in GREETING_KEYWORDS:
            return 0.9, random.choice(GREETING_RESPONSES), 'excited'
    return 0, None, None


def check_for_language(text):
    b = TextBlob(text)
    if b.detect_language() != 'en':
        return str(b.translate(to="en"))
    return text


def check_for_suicide(text):
    b = TextBlob(text)
    # iterating through n-grams of 2,3,4,5,6,7,8,9
    for (key, value) in NGRAM_DICT.items():
        ngrams = b.ngrams(n=value)
        for ngram in ngrams:
            composed_sentence = ''
            for word in ngram:
                composed_sentence += word.lower()
                composed_sentence += ' '
            composed_sentence_trimmed = composed_sentence.strip()
            print(composed_sentence_trimmed)
            print(eval(key))
            if composed_sentence_trimmed in eval(key):
                return 1, EMERGENCY, 'afraid'
    return 0, None, None


def check_for_mood(text):
    classification = TextBlob(text).sentiment.polarity
    if classification >= 0:
        return 0.85, 'I see you are happy today. try asking me for a joke or the weather', 'laughing'
    else:
        return 0.85, random.choice(POSITIVE_QUOTES), 'ok'


analyze_functions = [cursing_exists, check_for_greeting, check_for_mood, check_for_suicide]


def analyze_user_message(msg):
    # translate first to english if the input is not english
    msg_translated = check_for_language(msg)
    response_message, animation = "Sorry, seems like i don't have an appropriate response in my algorithm", 'crying'
    highest_score = 0
    for fn in analyze_functions:
        temp_score, temp_message, temp_animation = fn(msg_translated)
        if temp_score > highest_score:
            highest_score = temp_score
            response_message = temp_message
            animation = temp_animation
    return response_message, animation


@route("/chat", method='POST')
def chat():
    user_message = request.POST.get('msg')
    response_message, animation = analyze_user_message(user_message)
    return json.dumps({"animation": animation, "msg": response_message})


@route("/test", method='POST')
def chat():
    user_message = request.POST.get('msg')
    return json.dumps({"animation": "inlove", "msg": user_message})


@route('/js/<filename:re:.*\.js>', method='GET')
def javascripts(filename):
    return static_file(filename, root='js')


@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='css')


@route('/images/<filename:re:.*\.(jpg|png|gif|ico)>', method='GET')
def images(filename):
    return static_file(filename, root='images')


def main():
    run(host='localhost', port=7000)


if __name__ == '__main__':
    main()
