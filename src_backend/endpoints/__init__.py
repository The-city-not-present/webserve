

from .page_home import render as render_page_home
from .page_welcome import render as render_page_welcome
from .page_fail import render as render_page_fail
from .page_404 import render as render_page_404
from .page_403 import render as render_page_403
from .page_version import render as render_version

endpoints = {
    '/': render_page_home,
    '/welcome': render_page_welcome,
    '/fail': render_page_fail,
    '/version': render_version,
    403: render_page_403,
    404: render_page_404,
}
