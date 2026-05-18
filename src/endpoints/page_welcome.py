
from .lib.htmltmpl.compiled.html_bundle import make_html

def render(path,request):
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
