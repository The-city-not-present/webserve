
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse # for finding handler for the endpoint - we need to know path
import html # for sanitizing response on errors
# import re

from .globals import config
from .log import print_console, print_console_err, print_console_green



class HTTP404(Exception):
    """For HTTP 404"""

class HTTP403(Exception):
    """For HTTP 404"""



class WebResponse:
    def __init__(
        self,
        status_code: int,
        content_type: str,
        body: str,
        headers: list[tuple[str,str]],
        # cookies, # can be passed in headers
    ):
        self.status_code = status_code
        self.content_type = content_type
        self.body = body
        self.headers = headers



class Webserver:
    def __init__(self):
        self.endpoints = {}
        self.bind_host = config.bind_host
        self.port = config.port

    def assign_handlers(self,endpoints:dict={}):
        self.endpoints = {**self.endpoints,**endpoints}

    def setup(self,cfg):
        def set_bind_host(value):
            self.bind_host = value
        def set_port(value):
            self.port = value
        def set_script_name(value):
            config['script_name'] = value
        known = {
            'bind_host': set_bind_host,
            'port': set_port,
            'script_name': set_script_name,
        }
        for key, value in cfg.items():
            if key in known:
                handler = known.get(key,lambda v: _err(f'webserve: Can\t parse config: [{key}] = {repr(value)}'))
                handler(value)
            else:
                pass
                # raise Exception(f'Unrecognized config field: {key}')

    def run(self):
        try:
            self.port_num = int(self.port_num)
        except Exception as e:
            raise Exception(f'Webserve: Can\'t parse port_num param: {self.port_num}') from e
        server = HTTPServer((self.bind_host, self.port_num), self._get_handler(self.endpoints))
        print_console_green(f'Calling serve_forever() at {bind_host}:{port_num}')
        server.serve_forever()

    def _get_handler(self,endpoints):
        class Handler(BaseHTTPRequestHandler):
            def handle_request(self, send_body=True):
                try:

                    path = urlparse(self.path).path
                    renderer = self._get_matching_endpoint(path,endpoints)
                    assert callable(renderer), 'Whoops, renderer returned from get_matching_endpoint() must be callable'

                    response = renderer(self)
                    if not response.content_type:
                        response.content_type = 'text/html'

                    if not response.status_code:
                        response.status_code = 200

                    self.send_response(response.status_code)
                    for header_name, header_value in response.headers:
                        self.send_header(header_name,header_value)
                    self.send_header(f"Content-type", f"{response.content_type}; charset=utf-8")
                    self.end_headers()
                    if send_body:
                        self.wfile.write(response.body.encode("utf-8"))
                except (HTTP404,HTTP403) as e:
                    statuscode = 503
                    if isinstance(e,HTTP404):
                        statuscode = 404
                    if isinstance(e,HTTP403):
                        statuscode = 403
                    content_type = 'text/html' if not (self.headers.get("Accept",None) == "application/json") else 'application/json'
                    if not content_type:
                        content_type = 'text/html'
                    content = f'Can\t find / no access: HTTP {statuscode}'
                    renderer = endpoints.get(statuscode,None)
                    if renderer and send_body:
                        response = renderer(self, msg = e)
                        content = response.body

                    self.send_response(statuscode)
                    self.send_header(f"Content-type", f"{content_type}; charset=utf-8")
                    self.end_headers()
                    if send_body:
                        self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    print_console_err_fulltrace(e)
                    if send_body:
                        self.wfile.write(("<html><body>"+html.escape("Error processing request")+"</body></html>").encode())
                        # self.wfile.write(("<html><body>"+html.escape(str(e))+"</body></html>").encode())

            def do_GET(self):
                self.handle_request(send_body=True)

            def do_HEAD(self):
                self.handle_request(send_body=False)

        return Handler

    @staticmethod
    def _get_matching_endpoint(path,endpoints):
        def not_found(*args,**argv):
            raise HTTP404(f'{path} was not found on the server')

        def check_if_pattern_matches(path, pattern):
            if callable(pattern):
                if pattern(f'{path}'):
                    return f'{path}'
            elif isinstance(pattern, str):
                if f'{path}' == f'{pattern}':
                    return f'{path} ' # let's add a space to increase returned piece length, that is the priority for exact match
            elif isinstance(pattern, re.Pattern):
                matches = re.match(pattern,f'{path}')
                if matches:
                    return f'{matches[0]}'
            return None

        # longest matching
        best_match = None
        best_length = -1

        for pattern, renderer in endpoints.items():
            matching_str = check_if_pattern_matches(path,pattern)
            if matching_str is not None:
                if len(matching_str) > best_length:
                    best_match = renderer
                    best_length = len(matching_str)
        if best_match:
            return best_match

        return not_found
