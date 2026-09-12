

from typing import Protocol
import sys # for error reporting


class ErrorReadInterrupt(Exception):
    """When not read full message"""



# FileLikeObject = NewType("FileLikeObject", Any)
class FileLikeObject(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...



# self.close_connection = True
#     self.send_error(413, "Request Entity Too Large")



class HTTPBodyLimitedReader:
    def __init__(self, rfile: FileLikeObject, content_length: int):
        self.rfile: FileLikeObject = rfile
        self.remaining = content_length

    def read(self, size=-1) -> bytes|bytearray:
        if self.remaining == 0:
            return b''

        if size < 0 or size > self.remaining:
            size = self.remaining

        data = self.rfile.read(size)
        self.remaining -= len(data)
        return data

    def _drain_remaining(self):
        # I am not simply calling .read(), that would also read remaining bytes - to not have it stored in memory, if remaining bytes are gigabytes
        # Reject it, but consume the body
        while self.remaining:
            chunk = self.rfile.read(min(64 * 1024, self.remaining))
            if not chunk:
                break
            self.remaining -= len(chunk)

    def __del__(self):
        # this approach has multiple concerns, owever, I believe they are not actual for my purposes
        # I know better is to close connection, but I don't feel confident doing it here, cause I am not controlling the parent request handler object here
        # also, calling i/o in __del__ can cause slow down on shutdown/keyboard interrupt, and similar, not a good pattern
        # also, volnurable for DDOS
        try:
            self._drain_remaining()
        except Exception as e:
            # let's not crash - not sure what happened, connection closed, or whatever - let's put a notice to console
            print(f'Error: Webserve: request abandoned, trying to read remaing bytes till the end of request body: {e}',file=sys.stderr)



class HTTPBodyEmptyReader:
    def __init__(self):
        pass

    def read(self, size=-1) -> bytes|bytearray:
        return b''



class HTTPBodyMissingReader:
    def __init__(self):
        pass

    def read(self, size=-1) -> bytes|bytearray:
        raise Exception('can\'t call read() on network request: reqeust is not active at the moment')



class HTTPBodyChunkedReader:
    def __init__(self, rfile: FileLikeObject):
        self.rfile: FileLikeObject = rfile
        self.remaining = 0
        self.finished = False

    def _readline(self):
        line = self.rfile.readline()
        if not line:
            raise ConnectionError('Unexpected EOF while reading chunk header')
        return line

    def _next_chunk(self):
        line = self._readline()

        # Ignore chunk extensions for now:
        # '5;foo=bar' -> '5'
        size_text = line.split(b';', 1)[0].strip()

        try:
            size = int(size_text, 16)
        except ValueError:
            raise ValueError(f'Invalid chunk size: {size_text!r}')

        if size == 0:
            self.finished = True

            # Consume trailers until the empty line.
            while True:
                line = self._readline()
                if line in (b'\r\n', b'\n'):
                    break

            return

        self.remaining = size

    def read(self, size=-1) -> bytes|bytearray:
        if self.finished:
            return b''

        result = bytearray()

        while size < 0 or len(result) < size:
            if self.remaining == 0:
                self._next_chunk()

                if self.finished:
                    break

            to_read = self.remaining

            if size >= 0:
                to_read = min(to_read, size - len(result))

            data = self.rfile.read(to_read)

            if len(data) != to_read:
                raise ConnectionError('Unexpected EOF inside chunk')

            result.extend(data)
            self.remaining -= len(data)

            if self.remaining == 0:
                # Every chunk is followed by CRLF.
                ending = self.rfile.read(2)
                if ending != b'\r\n':
                    raise ValueError('Invalid chunk ending')

        return bytes(result)

    def _drain_remaining(self):
        # I am not simply calling .read(), that would also read remaining bytes - to not have it stored in memory, if remaining bytes are gigabytes
        # Reject it, but consume the body
        if self.finished:
            return b''

        while True:
            if self.remaining == 0:
                self._next_chunk()

                if self.finished:
                    break

            to_read = self.remaining

            data = self.rfile.read(to_read)

            if len(data) != to_read:
                raise ConnectionError('Unexpected EOF inside chunk')

            self.remaining -= len(data)

            if self.remaining == 0:
                # Every chunk is followed by CRLF.
                ending = self.rfile.read(2)
                if ending != b'\r\n':
                    raise ValueError('Invalid chunk ending')

    def __del__(self):
        # this approach has multiple concerns, owever, I believe they are not actual for my purposes
        # I know better is to close connection, but I don't feel confident doing it here, cause I am not controlling the parent request handler object here
        # also, calling i/o in __del__ can cause slow down on shutdown/keyboard interrupt, and similar, not a good pattern
        # also, volnurable for DDOS
        try:
            self._drain_remaining()
        except Exception as e:
            # let's not crash - not sure what happened, connection closed, or whatever - let's put a notice to console
            print(f'Error: Webserve: request abandoned, trying to read remaing bytes till the end of request body: {e}',file=sys.stderr)

