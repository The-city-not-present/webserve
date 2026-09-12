
# from bs4 import BeautifulSoup
# import re
from collections.abc import Iterator, Iterable # for type annotations
from typing import BinaryIO


from .common_defs import (
    WebserveInternalError,
)



from .config import CONFIG_DEFAULT_STDOUT_CHUNK_SIZE


# def sanitize_dom(classname, txt) -> str:
#     def sanitize_classname(s):
#         def err(i):
#             raise Exception(f'Not valid class name: {i}')
#         s = f'{s}'.split()
#         return ' '.join([part if re.match(r'^\s*\w[\w\-]*\w\s*$',part) else err(part) for part in s])
#
#
#     soup = BeautifulSoup("<div></div>", "html.parser")
#     div = soup.div
#
#     fragment = BeautifulSoup(txt, "html.parser")
#
#     # IMPORTANT: iterate over a copy
#     for child in list(fragment.contents):
#         div.append(child)
#
#     div["class"] = sanitize_classname(classname).split()
#
#     return str(div)


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
        raise WebserveInternalError(f'Webserve: writing data to network request body as stream: can\'t recognize data type, unsupported type: {type(s).__name__}')

