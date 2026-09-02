
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from urllib.parse import urlparse # for finding handler for the endpoint - we need to know path

from dataclasses import dataclass # for type annotations
from collections.abc import Iterator, Iterable, Callable # for type annotations
from socketserver import BaseRequestHandler # for type annotations
from typing import BinaryIO



from .helper_logger_funcs import Logger


from .match_endpoints import get_matching_endpoint


# CONFIG_DEFAULT_STDOUT_CHUNK_SIZE = 1024
CONFIG_DEFAULT_STDOUT_CHUNK_SIZE = 8192
# CONFIG_DEFAULT_STDOUT_CHUNK_SIZE = 128


ServerClass = Callable[
    [
        tuple[str | bytes | bytearray, int],
        type[BaseRequestHandler],
    ],
    HTTPServer | ThreadingHTTPServer,
]

def as_chunks(
    s: str | bytes | bytearray | BinaryIO | Iterable[bytes|bytearray] | None,
        options = None,
) -> Iterator[bytes]:
    options = options or {}
    if s is None:
        return
    if isinstance(s, str):
        yield s.encode('utf-8')
    elif isinstance(s, bytes):
        yield s
    elif isinstance(s, bytearray):
        yield bytes(s)
    elif hasattr(s, 'read'):
        chunk_size = options.get('stdout_chunk_size', CONFIG_DEFAULT_STDOUT_CHUNK_SIZE)
        while chunk := s.read(chunk_size):
            yield chunk
    elif isinstance(s, Iterable):
        yield from s
    else:
        raise TypeError(f'Unsupported type: {type(s).__name__}')



class HTTP404(Exception):
    """For HTTP 404"""

class HTTP403(Exception):
    """For HTTP 404"""

def raise_err_404_not_found(*_args,**_argv):
    raise HTTP404('404 not found')

@dataclass
class WebResponse:
    status_code: int
    content_type: str
    body: str | bytes | bytearray | BinaryIO | Iterable[bytes|bytearray]
    headers: list[tuple[str,str]]
    # cookies # can be passed in headers, no need for separate field
    is_binary: bool = False
    is_done: bool = False
    is_stream: bool = False
    options: dict | None = None



class Webserver:
    def __init__(self,config,is_threading=True):
        self.endpoints = {}
        self.config = config
        self.bind_host = config.get("http_host")
        self.port = config.get("http_port")
        self._is_threading_server = is_threading
        self.logger = Logger(self.config)

    def assign_handlers(self, endpoints: dict):
        self.endpoints = {**self.endpoints,**endpoints}

    def run(self):
        try:
            self.port = int(self.port)
        except Exception as e:
            raise Exception(f'Webserve: Can\'t parse port param: {self.port}') from e
        cls: ServerClass = HTTPServer
        if self._is_threading_server:
            cls = ThreadingHTTPServer
        server = cls((self.bind_host, self.port), self._get_handler(self.endpoints))
        if self._is_threading_server:
            server.daemon_threads = True
        self.logger.print_console_green(f'starting webserver at {self.bind_host}:{self.port}')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n\033[31mStopped (keyboard interrupt)\033[0m")
            # print("\033[0m", end="", flush=True)
        finally:
            server.server_close()
            # print("\033[0m", end="", flush=True)

    def _get_handler(self,endpoints: dict) -> type[BaseHTTPRequestHandler]:
        server = self
        class Handler(BaseHTTPRequestHandler):

            protocol_version = "HTTP/1.1"

            def handle_request(self):
                method = self.command
                send_body = True if not (method=='HEAD') else False
                try:

                    path = urlparse(self.path).path
                    renderer = get_matching_endpoint(path,endpoints) or raise_err_404_not_found
                    assert callable(renderer), 'Whoops, renderer returned from get_matching_endpoint() must be callable'

                    response: WebResponse = renderer(self, config=server.config)

                    if response.is_done:
                        # if all necessary headers and body were already sent - the renderer receives the handler instance and can send what is needed directly
                        return

                    if response.is_stream:
                        self.send_response(response.status_code)
                        for header_name, header_value in response.headers:
                            self.send_header(header_name, header_value)
                        if response.is_binary:
                            self.send_header(f"Content-type", f"{response.content_type}")
                        else:
                            self.send_header(f"Content-type", f"{response.content_type}; charset=utf-8")
                        self.end_headers()
                        for chunk in as_chunks(response.body,options=response.options):
                            size_hex = f'{len(chunk):X}'.encode('ascii')
                            self.wfile.write(size_hex + b'\r\n')
                            self.wfile.write(chunk if response.is_binary else chunk.encode('ascii'))
                            self.wfile.write(b'\r\n')
                            self.wfile.flush()
                        # End of chunked response
                        self.wfile.write(b'0\r\n\r\n')
                        self.wfile.flush()
                        return

                    if not response.content_type:
                        response.content_type = 'text/html'

                    if not response.status_code:
                        response.status_code = 200

                    if response.body is None:
                        response.body = b''
                    if not response.is_binary:
                        response.body = response.body.encode("utf-8")

                    self.send_response(response.status_code)
                    for header_name, header_value in response.headers:
                        self.send_header(header_name, header_value)
                    if response.is_binary:
                        self.send_header(f"Content-type", f"{response.content_type}")
                    else:
                        self.send_header(f"Content-type", f"{response.content_type}; charset=utf-8")
                    self.send_header('Content-length',str(len(response.body)))
                    self.end_headers()
                    if send_body:
                        self.wfile.write(response.body)

                except (HTTP404,HTTP403) as e:
                    statuscode = 503
                    if isinstance(e,HTTP404):
                        statuscode = 404
                    if isinstance(e,HTTP403):
                        statuscode = 403
                    content_type = 'text/html' if not (self.headers.get("Accept",None) == "application/json") else 'application/json'
                    if not content_type:
                        content_type = 'text/html'
                    content = f'Can\'t find / no access: HTTP {statuscode}'.encode("utf-8")
                    renderer: Callable | None = endpoints.get(statuscode,None)
                    if renderer and send_body:
                        response = renderer(self, config=server.config, msg = e)
                        content = response.body
                        if not response.is_binary:
                            content = content.encode("utf-8")
                            self.send_header(f"Content-type", f"{content_type}; charset=utf-8")
                    self.send_response(statuscode)
                    self.send_header('Content-length',str(len(content)))
                    self.end_headers()
                    if send_body:
                        self.wfile.write(content)
                except Exception as e:
                    self.send_response(503)
                    self.send_header(f"Content-type", "text/plain; charset=utf-8")
                    body = b''
                    if send_body:
                        try:
                            err = f'{e}'
                            # err_html = html.escape(err)
                            err_txt = err
                            try:
                                # # several more levels to capture stacktrace, format it, convert "red" colors to spans with color red... If anything fails, there is a fallback to simpler way to just show the message
                                # err_full = Logger.make_err_fulltrace_message(e)
                                # err_txt = f'{err_full}'
                                err_txt = f'{e}'
                                # # err_html = '<br />'.join(html.escape(err_full).splitlines())
                                # # COLOR_MARKERS = {
                                # #     '@STDOUT_COLOR_RED@': '<span class="err-color-red" style="color: #990000;">',
                                # #     '@STDOUT_COLOR_GREEN@': '<span class="err-color-green" style="color: #009900;">',
                                # #     '@STDOUT_COLOR_RESET@': '</span>',
                                # # }
                                # # color_markers_re = re.compile("|".join(map(re.escape, COLOR_MARKERS)))
                                # # err_html = color_markers_re.sub(lambda m: COLOR_MARKERS[m.group()], err_html)
                                # # try:
                                # #     err_html = sanitize_dom('err err-stacktrace-container',err_html) # wrap results one more time to make sure all tags are closed
                                # # except Exception as ee:
                                # #     server.logger.print_console_err_fulltrace(ee)
                                # #     pass
                            except Exception as ee:
                                server.logger.print_console_err_fulltrace(ee)
                                pass
                            # body = ("<html><body>"+err_html+"</body></html>").encode("utf-8")
                            body = f"{err_txt}".encode("utf-8")
                        except Exception as ee:
                            server.logger.print_console_err_fulltrace(ee)
                            # print fallback
                            # err_html = "error processing request"
                            err_txt = "error processing request"
                            body = f"{err_txt}".encode("utf-8")
                            # body = ("<html><body>"+err_html+"</body></html>").encode("utf-8")
                    self.send_header('Content-length',str(len(body)))
                    self.end_headers()
                    server.logger.print_console_err_fulltrace(e)
                    self.wfile.write(body)

            def log_message(self, format, *args):
                """http.server logging fn, updated so that status column is aligned in one column after timestamp,
so that it's easier to see 5xx codes; also have colors added.

That gives you a log where 500/503 etc. immediately jump out in red, while 4xx are yellow.

One caveat: log_message() is also used for things other than normal access logs, so if you
have custom handlers emitting messages through it, you'd want to handle those separately.
For ordinary http.server request logging, though, this works cleanly.
                """
                request = args[0]
                status = int(args[1])
                timestamp = self.log_date_time_string()

                if status >= 500:
                    color = "\033[31m"  # red
                elif status >= 400:
                    color = "\033[33m"  # yellow
                elif status >= 300:
                    color = "\033[36m"  # cyan
                else:
                    color = "\033[32m"  # green

                reset = "\033[0m"

                server.logger.log_network_request(
                    f"{self.address_string()} - - "
                    f"[{timestamp}] "
                    f"{color}[{status:03d}]{reset} "
                    f'"{request}"'
                )

            def __getattr__(self, name):
                if name.startswith("do_"):
                    return self.handle_request
                raise AttributeError(name)

        return Handler
