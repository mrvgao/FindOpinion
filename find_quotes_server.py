from bottle import post, run, request
from format_parser import get_an_article_speech


@post('/quotes/')
def get_article_quotes():
    content = request.forms.content
    result = get_an_article_speech(content)
    return {'result': result}


run(host='localhost', port=9999, reloader=True)

