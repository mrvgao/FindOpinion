import bottle
from bottle import post, run, request, get
from spoken_string_finder import get_an_article_speech
from bottle import static_file

bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024


@post('/new-version/quotes/')
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
        {'entity': n, 'verb': v, 'speech': original.split(' '), 'confidence': c} for n, v, s, original, c in results
    ]

    return results


# @get('/new-version/')
# def get_new_version_demo():
#     return static_file('index.html', root='statics/')


@get('/new-version/')
def get_new_version_demo():
    return static_file('index_2.html', root='statics/')


@get('/static/<filepath:path>')
def get_static_file(filepath):
    return static_file(filepath, root='./statics/')


run(host='0.0.0.0', port=8080, reloader=True)
