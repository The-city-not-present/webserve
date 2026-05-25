
from .lib.htmltmpl.src import make_html

def render(request, config, msg = None):
    response = make_html(
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
