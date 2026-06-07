
from dotenv import load_dotenv
import os
from datetime import datetime

from .globals import config
from .log import print_console, print_console_err, print_console_green


PORT_NUM = 8051
BIND_HOST = '0.0.0.0'
SCRIPT_NAME = 'webserve'

try:
    load_dotenv()
    PORT_NUM = os.getenv("PORT_NUM", "0")
    BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
    SCRIPT_NAME = os.getenv("SCRIPT_NAME", SCRIPT_NAME)
except Exception as e:
    print_console_err('Failed to load env vars')
    pass

_VERSION = None
try:
    from .GENERATED._VERSION import _VERSION
except ImportError:
    _VERSION = None

config['port'] = PORT_NUM
config['bind_host'] = BIND_HOST
config['script_name'] = SCRIPT_NAME
config['time_started'] = datetime.now() # we interpret it as it already started, as program loaded thew module  - I don't wait when "run_forever" is invoked
config['version'] = _VERSION
