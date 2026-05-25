
from .lib.htmltmpl.src import make_html

def render(request, config, msg = None):
    response = make_html(
        title = 'Home',
        page = 'Home',
        h1 = 'Welcome!',
        meta = [],
        assets = [],
        cssclasses = ['page-home'],
        banners = [],
        sections = [],
    )
    return response, 'text/html'
