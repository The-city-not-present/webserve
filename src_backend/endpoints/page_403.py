
import html

from .lib.htmltmpl.src import make_html #, wrap_div


def render(path, request):
    path = f'{path}'
    main_section = f'''
<div class="container">
{html.escape(path)}
</div>
    '''
    response = make_html(
        title = '403 access denied',
        page = '403 access denied',
        h1 = '403 access denied',
        meta = [],
        assets = [],
        cssclasses = ['page-error','page-error-403'],
        banners = [],
        sections = [main_section],
    )
    return response, 'text/html'
