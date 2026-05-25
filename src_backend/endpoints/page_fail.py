
from .lib.htmltmpl.src import make_html

def render(request, config, msg = None):
    raise Exception('Hello, I am the fail')
    response = make_html.make_html(
        title = 'Welcome',
        page = 'Welcome',
        h1 = 'Welcome!',
        meta = [],
        assets = [],
        cssclasses = ['page-welcome'],
        banners = [],
        sections = [],
    )
    return response, 'text/html'
