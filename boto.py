"""
This is the template server side for ChatBot
"""
import json

from bottle import route, run, template, static_file, request

with open("./swear_words/swear_words.txt") as f:
    swear_words = sorted(word.strip(" ") for line in f for word in line.split(','))


@route('/', method='GET')
def index():
    return template("chatbot.html")


def cursing_exists(user_text):
    words = user_text.split(" ")
    if any(word in swear_words for word in words):
        return "Hey! your'e not allowed to swear", 'heartbroke'
    else:
        return False


def analyze_user_message(msg):
    response_message, animation = "Sorry, seems like i don't have an appropriate response in my algorithm", 'crying'
    if cursing_exists(msg):
        response_message, animation = cursing_exists(msg)
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
