

from .page_home import render as render_page_home
from .page_welcome import render as render_page_welcome

endpoints = {
    '/': render_page_home,
    '/welcome': render_page_welcome,
}
