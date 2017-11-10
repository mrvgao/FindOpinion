from bottle import post, run, request
from format_parser import get_an_article_speech


@post('/quotes/')
def get_article_quotes():
    content = request.forms.content
    result = get_an_article_speech(content)
    result = format_http_return_value(result)

    return {'result': result}


def format_http_return_value(results):
    results = [
        {'entity': n, 'verb': v, 'speech': s, 'confidence': c} for n, v, s, c in results
    ]

    return results


run(host='0.0.0.0', port=9999, reloader=True)

