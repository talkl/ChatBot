"""
This is the template server side for ChatBot
"""
import json
import random
from textblob import TextBlob
from geotext import GeoText
import requests
from textblob import Word
from nltk.corpus import movie_reviews
from textblob.classifiers import NaiveBayesClassifier
from nltk.tokenize import word_tokenize
from bottle import route, run, template, static_file, request

# constants
with open("./jokes/jokes.txt", encoding="utf-8") as f:
    JOKES = sorted(joke for text in f for joke in text.split(';'))
with open("./swear_words/swear_words.txt") as f:
    SWEAR_WORDS = sorted(word.strip(" ") for line in f for word in line.split(','))
GREETING_KEYWORDS = ("hello", "hi", "greetings", "sup", "what's up", 'hey')
GREETING_RESPONSES = ["'sup bro", "hey", "How are you dear?", "hey you get my snap?"]
with open("./positive_quotes/positive_quotes.txt", encoding="utf-8") as f:
    POSITIVE_QUOTES = sorted(word.strip(" ") for line in f for word in line.split(';'))
EMERGENCY = 'You are not alone in this. I’m here for you. I will now automatically connect you with a human' \
            ' health professional. Eran health center communication: 1201 or 076-8844402 or info@eran.org.il'
JOKE_INQUIRY = ['what', 'how', 'can', 'do']
WEATHER_WORDS = ['weather', 'forecast', 'climate', 'temperature', 'cold', 'warm', 'raining', 'sunny', 'wind',
                 'humidity', 'cloudiness', 'precipitation', 'snowing', 'rainy', 'snow', 'blizzard', 'snowstorm',
                 'fog', 'foggy', 'downpour']

DUO = ['kill myself', 'commit suicide']
TRIO = ['no one cares', "im stressed out", "i dont care", "im just tired"]
QUARTET = ["i should just kill", "i want to disappear", "im just stressed out",
           "im not feeling good"]
QUINT = ["i just want to sleep", 'i cant keep doing this',
         'what will heaven be like', "im having a hard time",
         "i feel so much better"]
SEXTET = ["i just want to be done", "i just want to be alone"]
SEPTET = []
OCTET = ["i dont think ill be at school next"]
NONET = ["if anything happens to me promise to take care",
         "i want to tell you something oh never mind",
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

# Template for responses that include a direct noun which is indefinite/uncountable
SELF_VERBS_WITH_NOUN_CAPS_PLURAL = [
    "My last startup totally crushed the {noun} vertical",
    "Were you aware I was a serial entrepreneur in the {noun} sector?",
    "My startup is Uber for {noun}",
    "I really consider myself an expert on {noun}",
]

SELF_VERBS_WITH_NOUN_LOWER = [
    "Yeah but I know a lot about {noun}",
    "My bros always ask me about {noun}",
    "Oh you mentioned {noun}, i dreamt about it last night"
]

SELF_VERBS_WITH_ADJECTIVE = [
    "I consider myself to be a {adjective}",
    "I am what i am, sometimes {adjective}, sometimes not, riding inside the matrix",
    "Is being {adjective} a good thing?"
]


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
        if part_of_speech == 'NNP' and word.lower() == 'boto':
            return word.lower().capitalize()
        elif part_of_speech == 'NN' or 'NNS' or 'NNP' or 'NNPS':
            noun = word.lower()
    return noun


def find_verb(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    verb = None

    for word, part_of_speech in sent.pos_tags:
        if part_of_speech == 'VB' or 'VBD' or 'VBN' or 'VBP' or 'VBZ':
            verb = word.lower()
    return verb


def find_adjective(sent):
    """Given a sentence, find a preferred pronoun to respond with. Returns None if no candidate
    pronoun is found in the input"""
    adjective = None

    for word, part_of_speech in sent.pos_tags:
        if part_of_speech == 'JJ':
            adjective = word.lower()
    return adjective


def find_candidates_parts_of_speech(input):
    sentences = TextBlob(input).sentences
    pronoun = None
    noun = None
    verb = None
    adjective = None
    for sentence in sentences:
        pronoun = find_pronoun(sentence)
        noun = find_noun(sentence)
        verb = find_verb(sentence)
        adjective = find_adjective(sentence)
    return pronoun, noun, adjective, verb


def check_for_comment_about_bot(pronoun, noun, adjective):
    resp = None
    if pronoun == 'I' or noun == 'Boto' and (noun or adjective):
        if noun and not adjective:
            if random.choice((True, False)):
                resp = random.choice(SELF_VERBS_WITH_NOUN_CAPS_PLURAL).format(
                    **{'noun': TextBlob(noun).words.pluralize()})
            else:
                resp = random.choice(SELF_VERBS_WITH_NOUN_LOWER).format(**{'noun': noun})
        else:
            resp = random.choice(SELF_VERBS_WITH_ADJECTIVE).format(**{'adjective': adjective})
    return resp


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
    b = TextBlob(text.replace("'", ""))
    # iterating through n-grams of 2,3,4,5,6,7,8,9
    for (key, value) in NGRAM_DICT.items():
        ngrams = b.ngrams(n=value)
        for ngram in ngrams:
            composed_sentence = ''
            for word in ngram:
                composed_sentence += word.lower()
                composed_sentence += ' '
            composed_sentence_trimmed = composed_sentence.strip()
            if composed_sentence_trimmed in eval(key):
                return 1, EMERGENCY, 'afraid'
    return 0, None, None


def respond_to_neutral_speech(text):
    pronoun, noun, adjective, verb = find_candidates_parts_of_speech(text)
    resp = check_for_comment_about_bot(pronoun, noun, adjective)
    if resp:
        return resp
    else:
        return "Ok, i hear you. Try asking me for a joke or the weather. I'm good at it"


def check_for_mood(text):
    classification = TextBlob(text).sentiment.polarity
    if classification >= 0.3:
        return 0.85, "I see you are happy today. that's very good. I'm glad", 'laughing'
    elif -0.2 <= classification < 0.3:
        return 0.85, respond_to_neutral_speech(text), 'takeoff'
    elif classification <= -0.70:
        return 1, EMERGENCY, 'afraid'
    else:
        return 0.85, random.choice(POSITIVE_QUOTES), 'ok'


def check_for_name(text):
    b = TextBlob(text)
    pairs = b.ngrams(n=2)
    for pair in pairs:
        composed_sentence = ''
        for word in pair:
            composed_sentence += word.lower()
            composed_sentence += ' '
        composed_sentence_trimmed = composed_sentence.strip()
        if composed_sentence_trimmed == 'my name':
            for word, part_of_speech in b.pos_tags:
                if part_of_speech == 'NNP':
                    return 0.91, 'Hello {0}'.format(word), 'giggling'
    return 0, None, None


def check_if_wants_joke(text):
    b = TextBlob(text)
    for sentence in b.sentences:
        inquiry = False
        for word in sentence.words:
            if word.lower() in JOKE_INQUIRY:
                inquiry = True
        if sentence[-1][-1] == '?':
            inquiry = True
        if inquiry and ('joke' in sentence or 'jokes' in sentence or 'Joke' in sentence or 'Jokes' in sentence):
            return 0.92, random.choice(JOKES), 'laughing'
    return 0, None, None


def get_weather_api(city):
    """
    limit:
    {
    "cod": 429,
    "message": "Your account is temporary blocked due to exceeding of requests limitation of your subscription type.
    Please choose the proper subscription http://openweathermap.org/price"
    }
    We recommend making calls to the API no more than one time every 10 minutes for one location (city / coordinates / zip-code). This is due to the fact that weather data in our system is updated no more than one time every 10 minutes.
    :param city:
    :return the conditions in the specific city:
    """
    api_url = 'http://api.openweathermap.org/data/2.5/forecast'
    app_id = '7139cf25a9d480c56d195b4cb0a5d493'
    r = requests.get(url=api_url, params=dict(q=city, APPID=app_id))
    response_json = r.json()
    weather_description = response_json.get('list')[0].get('weather')[0].get(
        'description')
    weather_temperature = round(response_json.get('list')[0].get('main').get(
        'temp') - 273.15)
    weather_wind_speed = round(response_json.get('list')[0].get('wind').get(
        'speed'))
    weather_wind_direction = round(response_json.get('list')[0].get('wind').get(
        'deg'))
    if response_json.get('cod') == '429':
        return 'I think we requested too many weather conditions for that location. you can try in 10 minutes'
    elif response_json.get('cod') == '200':
        weather_msg = 'Current condition in {0} is {1}. The temperature is {2} celsius. Wind is {3} meter/sec with a' \
                      ' direction of {4} degrees.'.format(
            city,
            weather_description,
            weather_temperature, weather_wind_speed, weather_wind_direction)
        return weather_msg
    else:
        print('unexpected code from the API')
        return "sorry i couldn't fetch the weather this time. try again later"


def check_for_weather(text):
    b = TextBlob(text)
    cities = GeoText(text).cities
    for sentence in b.sentences:
        wants_weather = None
        for word in sentence.words:
            if word.lower() in WEATHER_WORDS:
                wants_weather = True
        if wants_weather and cities:
            return 0.92, get_weather_api(cities[0]), 'dog'
    return 0, None, None


analyze_functions = [cursing_exists, check_for_greeting, check_for_mood, check_for_suicide, check_for_name,
                     check_if_wants_joke, check_for_weather]


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
