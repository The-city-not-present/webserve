
import argparse
import traceback, sys
from dotenv import load_dotenv
import os
from datetime import datetime
# src/webserve.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import html




if __name__ == '__main__':
    # run as a program
    from endpoints import endpoints
    from endpoints.common_types import HTTP404, HTTP403
elif '.' in __name__:
    # package
    from .endpoints import endpoints
    from .endpoints.common_types import HTTP404, HTTP403
else:
    # included with no parent package
    from endpoints import endpoints
    from endpoints.common_types import HTTP404, HTTP403






# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"







load_dotenv()
PORT_NUM = os.getenv("PORT_NUM", "")



def get_handler(endpoints):
    class Handler(BaseHTTPRequestHandler):
        def handle_request(self, send_body=True):
            try:

                path = urlparse(self.path).path
                renderer = endpoints.get(path,None)

                if not renderer:
                    raise HTTP404('Not found')

                content, content_type = renderer(self.path, self)
                if not content_type:
                    content_type = 'text/html'

                self.send_response(200)
                self.send_header(f"Content-type", f"{content_type}; charset=utf-8")
                self.end_headers()
                if send_body:
                    self.wfile.write(content.encode("utf-8"))
            except (HTTP404,HTTP403) as e:
                statuscode = 503
                if isinstance(e,HTTP404):
                    statuscode = 404
                if isinstance(e,HTTP403):
                    statuscode = 403
                content_type = 'text/html' if not (self.headers.get("Accept") == "application/json") else 'application/json'
                if not content_type:
                    content_type = 'text/html'
                content = f'Can\t find / no access: HTTP {statuscode}'
                renderer = endpoints.get(statuscode,None)
                if renderer and send_body:
                    content, _ = renderer(e, self)

                self.send_response(200)
                self.send_header(f"Content-type", f"{content_type}; charset=utf-8")
                self.end_headers()
                if send_body:
                    self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print('',file=sys.stderr)
                print('Stack trace:',file=sys.stderr)
                print('',file=sys.stderr)
                traceback.print_exception(e,limit=20)
                print('',file=sys.stderr)
                print('',file=sys.stderr)
                print('',file=sys.stderr)
                print('Error:',file=sys.stderr)
                print('',file=sys.stderr)
                print(f'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}',file=sys.stderr)
                print('',file=sys.stderr)
                if send_body:
                    self.wfile.write(("<html><body>"+html.escape("Error processing request")+"</body></html>").encode())
                    # self.wfile.write(("<html><body>"+html.escape(str(e))+"</body></html>").encode())

        def do_GET(self):
            self.handle_request(send_body=True)

        def do_HEAD(self):
            self.handle_request(send_body=False)

    return Handler


def run(address='0.0.0.0',port_num=PORT_NUM,endpoints=None):
    if endpoints is None:
        endpoints = {}
    try:
        port_num = int(port_num)
    except Exception as e:
        raise Exception(f'Can\'t parse port_num param: {port_num}') from e
    server = HTTPServer((address, port_num), get_handler(endpoints))
    print('Calling serve_forever()!')
    server.serve_forever()





def entry_point(*argcs,**kwargs):
    try:
        time_start = datetime.now()
        script_name = 'webserve'

        parser = argparse.ArgumentParser(
            description="Webserve",
            prog='webserve --program webserve'
        )
        parser.add_argument(
            '--port',
            help='port number',
            type=int,
            required=False
        )
        # args = None
        # args_rest = None
        # if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
        #     args, args_rest = parser.parse_known_args()
        # else:
        args = None
        try:
            args = parser.parse_args(*argcs,**kwargs)
        except SystemExit as e:
            print(f'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}',file=sys.stderr)
            raise e

        port_num = PORT_NUM
        if args.port:
            port_num = args.port
            try:
                port_num = int(port_num)
            except Exception as e:
                raise Exception(f'Can\'t parse port_num param: {port_num}') from e

        result = run(
            address='0.0.0.0',
            port_num = port_num,
            endpoints = endpoints,
        )

        time_finish = datetime.now()
        print('{script_name}: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start,script_name=script_name))
    except Exception as e:
        # the program is designed to be user-friendly
        # that's why we reformat error messages a little bit
        # stack trace is still printed (I even made it longer to 20 steps!)
        # but the error message itself is separated and printed as the last message again

        # for example, I don't write "print('File Not Found!');exit(1);", I just write "raise FileNotFoundErro()"
        print('',file=sys.stderr)
        print('Stack trace:',file=sys.stderr)
        print('',file=sys.stderr)
        traceback.print_exception(e,limit=20)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print('Error:',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        exit(1)

if __name__ == '__main__':
    entry_point()
