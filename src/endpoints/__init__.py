

from .page_home import render as render_page_home
from .page_welcome import render as render_page_welcome
from .page_fail import render as render_page_fail

endpoints = {
    '/': render_page_home,
    '/welcome': render_page_welcome,
    '/fail': render_page_fail,
}
