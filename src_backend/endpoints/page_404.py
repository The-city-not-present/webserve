
import html
from urllib.parse import urlparse, parse_qs

from .lib.htmltmpl.src import make_html #, wrap_div


def render(request, config, msg = None):
    path = f'{urlparse(request.path).path}'
    msg = f'{msg}' if msg is not None else f'{path} was not found on this server'
    main_section = f'''
<div class="container">
{html.escape(msg)}
</div>
    '''
    response = make_html(
        title = '404 not found',
        page = 'Fileshare',
        h1 = '404 not found',
        meta = [],
        assets = [],
        cssclasses = ['page-error','page-error-404'],
        banners = [],
        sections = [main_section],
    )
    return response, 'text/html'
