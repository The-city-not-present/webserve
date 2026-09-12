
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from urllib.parse import urlparse # for finding handler for the endpoint - we need to know path

from collections.abc import Callable # for type annotations
from socketserver import BaseRequestHandler # for type annotations

import uuid


from .common_defs import (
    WebserveInternalError,
    WebResponse,
    HTTP403,
    HTTP404,
)

from .helper_utility_funcs import (
    as_chunks,
)



from .helper_logger_funcs import Logger


from .helper_body_reader_proxy import (
    HTTPBodyLimitedReader,
    HTTPBodyChunkedReader,
    HTTPBodyEmptyReader,
    HTTPBodyMissingReader,
    FileLikeObject,
)

from .match_endpoints import get_matching_endpoint



ServerClass = Callable[
    [
        tuple[str | bytes | bytearray, int],
        type[BaseRequestHandler],
    ],
    HTTPServer | ThreadingHTTPServer,
]



class Webserver:
    """Usage:
if not config.get('http_host'):
    config['http_host'] = 'localhost'
if not config.get('http_port'):
    config['http_port'] = find_free_port(config['http_host'], start=PORT_START_WITH)
if not config.get('http_protocol'):
    config['http_protocol'] = 'http'
if not config.get('http_address'):
    config['http_address'] = (
        f'{config["http_protocol"]}://'
        f'{config["http_host"]}:{config["http_port"]}'
server = Webserver(config, is_threading=True|False) # a wrapper around python http.server - no flask or django
server.assign_handlers(endpoints)
server.run()

endpoints should be a dict:
- as key, use exact patterns (str), or re.compile regexs
- as values, use handler functions:
    that accept
      1. an instance of BaseHTTPRequestHandler enriched with request_body property (that suports .read() - can be used as file-like object)
      2. and a "config" object with global app config that you can have passed to Webserver constructor when creating server instance object
    and should return
      an instance of WebResponse (or compatible, per protocol) - with headers, status_code, body, and some flags
  
  Handler will get called on any http method - GET, POST, HEAD, PATCH, DELETE, PUT, FOO, BAR... Check .method attribute and return http 405 if it's not GET, or not what you support

  From endpoint handler, you can also raise HTTP403 or HTTP 404 - proper status code will be set.

  Or, you can do all outputs to the instance of BaseHTTPRequestHandler you received directly, and return WebResponse with is_done=True flag.
"""

    def __init__(self, config, is_threading: bool = True ):
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
            raise WebserveInternalError(f'Webserve: Can\'t parse port param: {self.port}') from e
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



        class HandlerRequestData:

            request_id: str | None = None
            file: FileLikeObject

            def __init__(self, net_request_handler: BaseHTTPRequestHandler):
                self._net_request_handler = net_request_handler
                self.request_id = None
                self.file = HTTPBodyMissingReader()

            def _create_request_body(self):
                transfer_encoding = self._net_request_handler.headers.get("Transfer-Encoding", "")
                if transfer_encoding.lower() == "chunked":
                    return HTTPBodyChunkedReader(self._net_request_handler.rfile)
                content_length = self._net_request_handler.headers.get("Content-Length")
                if content_length is not None:
                    return HTTPBodyLimitedReader(self._net_request_handler.rfile, int(content_length))
                return HTTPBodyEmptyReader()
            
            # unlink document if some error happened, or if we are done processing it
            def __del__(self):
                pass

            # methods required by python so that I can use "with"
            def __enter__(self):
                self.request_id = uuid.uuid4()
                self.file = self._create_request_body()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.file = HTTPBodyMissingReader()
                self.request_id = None
                return None


        
        class Handler(BaseHTTPRequestHandler):

            protocol_version = "HTTP/1.1"

            handler_id: str
            _request_body = None



            def __init__(self,*args,**argv):
                self.handler_id = uuid.uuid4()
                self._request = HandlerRequestData(self)
                super().__init__(*args,**argv)



            @property
            def request_body(self):
                return self._request.file



            def handle_request(self):

                def make_raise_err_404_not_found(path):
                    def err(*_args,**_argv):
                        raise HTTP404(f'Path not found: {path}')
                    return err
            
                method = self.command
                send_body = True if not (method=='HEAD') else False
                try:

                    path = urlparse(self.path).path
                    renderer = get_matching_endpoint(path,endpoints) or make_raise_err_404_not_found(path)
                    assert callable(renderer), 'Webserve: Whoops, renderer returned from get_matching_endpoint() must be callable'

                    with self._request:
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
                    content = f'{e}'.encode("utf-8")
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



            def log_request(self, code="-", size="-"):
                """http.server logging fn, updated so that status column is aligned in one column after timestamp,
so that it's easier to see 5xx codes; also have colors added.

That gives you a log where 500/503 etc. immediately jump out in red, while 4xx are yellow.

One caveat: log_message() is also used for things other than normal access logs, so if you
have custom handlers emitting messages through it, you'd want to handle those separately.
For ordinary http.server request logging, though, this works cleanly.
                """
                try:
                    timestamp = self.log_date_time_string()
                    status = int(code)

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
                        f'"{self.requestline}"'
                    )
                except Exception:
                    return super().log_request(self, code, size)



            def __getattr__(self, name):
                if name.startswith("do_"):
                    return self.handle_request
                raise AttributeError(name)



        return Handler
