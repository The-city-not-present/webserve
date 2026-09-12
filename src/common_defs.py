from typing import BinaryIO
from collections.abc import Iterable, Callable # for type annotations
from dataclasses import dataclass # for type annotations



class WebserveInternalError(Exception):
    """For errors"""



class HTTP404(Exception):
    """For HTTP 404"""

class HTTP403(Exception):
    """For HTTP 404"""



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



