
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
        title = '404 not found',
        page = '404 not found',
        h1 = '404 not found',
        meta = [],
        assets = [],
        cssclasses = ['page-error','page-error-404'],
        banners = [],
        sections = [main_section],
    )
    return response, 'text/html'
