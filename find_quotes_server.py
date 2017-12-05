import bottle
from bottle import post, run, request, get
from spoken_string_finder import get_an_article_speech

bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024


@post('/quotes/')
def get_article_quotes():
    content = request.forms.content
    result = get_an_article_speech(content)
    result = format_http_return_value(result)

    return {'result': result}


@get('/ok')
def alive():
    return {'status': 'okay'}


def format_http_return_value(results):
    results = [
        {'entity': n, 'verb': v, 'speech': s, 'confidence': c} for n, v, s, c in results
    ]

    return results


run(host='0.0.0.0', port=8080, reloader=True)
