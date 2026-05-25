
import html
from urllib.parse import urlparse, parse_qs

from .lib.htmltmpl.src import make_html #, wrap_div


def render(request, config, msg = None):
    path = f'{urlparse(request.path).path}'
    msg = f'{msg}' if msg is not None else f'no permissions to see {path} on this server'
    main_section = f'''
<div class="container">
{html.escape(msg)}
</div>
'''
    response = make_html(
        title = '403 access denied',
        page = 'Fileshare',
        h1 = '403 access denied',
        meta = [],
        assets = [],
        cssclasses = ['page-error','page-error-403'],
        banners = [],
        sections = [main_section],
    )
    return response, 'text/html'
