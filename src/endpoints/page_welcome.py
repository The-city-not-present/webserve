
from .lib.htmltmpl.src import make_html

def render(path,request):
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
