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
    
    def has_header(self,name: str) -> bool:
        def is_empty(n):
            if n is None:
                return True
            elif isinstance(n,(int,float,bool,)):
                return False
            elif isinstance(n,str):
                return len(n.strip())>0
            else:
                return not not n
        def as_str(n):
            return '' if is_empty(n) else f'{n}'
        header_names_norm = [ as_str(h[0]).strip().lower() for h in (self.headers or []) ]
        name_norm = name.strip().lower()
        return name_norm in header_names_norm
    
    @classmethod
    def from_existing(cls, obj):
        return cls(**vars(obj))


