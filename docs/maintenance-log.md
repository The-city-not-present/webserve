# Maintenance log

> webserve (the self-written webserver) — structural maintenance notes.
> Entries here capture changes to the library's own shape and conventions, so
> they can be repeated when the library is embedded in other projects.
>
> Entries are ordered **newest first**.

## How to read an entry

Each entry is a section whose heading reads like a commit subject: it states the
**intent** of the change and **where** it happens. Inside, answer:

- **When** — date/time requested and implemented.
- **What & why** — the request and the reasoning behind the chosen approach.
- **Input** — a sample of the code/file **before** the change.
- **Output** — a sample of the code/file **after** the change.
- **Repeat** — a checklist to apply the same convention elsewhere.

---

## webserve: emit start/stop/request/error events instead of printing (configurable built-in logging)

- **Requested:** 2026-11-08
- **Implemented:** 2026-11-08
- **Where:** `src/webserver.py`, `src/helper_logger_funcs.py`, new `src/events.py`.

### What & why

webserve used to print every request line and error directly to the console via
a `Logger` that serialized writes through a queue + worker thread. To let a
caller own the logging (and keep webserve itself free of console side effects),
webserve now **emits structured events** and keeps its console printing behind a
`logging_enabled` switch (default `True`).

- `Webserver(config, is_threading=..., logging_enabled=...)` — `logging_enabled`
  defaults to `True`; the caller passes `False` when it attaches its own logger.
- `Webserver.events` is a `WebserveEvents`; subscribe `listener(event_name, payload)`.
- Events: `webserver_start`, `webserver_stop`, `request`, `error`.
- The built-in `Logger` gains `enabled=` and a
  `print_error_message(message, traceback_str)` so errors can be logged from
  pre-formatted strings.

Fail-loud errors are deliberately **excluded** from this change: the `as_chunks`
chunk-size parse error and the request-body drain notice stay as direct
`print(..., file=sys.stderr)`, so they are never silenced by `logging_enabled`.

### Input (before)

```python
# webserver.py — __init__ and log_request
self.logger = Logger(self.config)

def log_request(self, code="-", size="-"):
    try:
        timestamp = self.log_date_time_string()
        status = int(code)
        color = "\033[31m" if status >= 500 else ...
        server.logger.log_network_request(
            f"{self.address_string()} - - [{timestamp}] {color}[{status:03d}]{reset} \"{self.requestline}\""
        )
    except Exception:
        return super().log_request(self, code, size)
```

### Output (after)

```python
# webserver.py — __init__
self.logging_enabled = logging_enabled
self.events = WebserveEvents()
self.logger = Logger(self.config, enabled=logging_enabled)

def log_request(self, code="-", size="-"):
    try:
        timestamp = self.log_date_time_string()
        try:
            status = int(code)
        except (TypeError, ValueError):
            status = None
        server.emit_event('request', {
            'method': f'{self.command}',
            'path': urlparse(self.path).path,
            'status_code': status if status is not None else f'{code}',
            'timestamp': timestamp,
            'remote_address': self.address_string(),
            'request_line': self.requestline,
            'response_size': size,
        })
        if status is None:
            return super().log_request(code, size)
        server.logger.log_network_request(...)  # no-ops when logging_enabled=False
    except Exception:
        return super().log_request(code, size)
```

`src/events.py`:

```python
class WebserveEvents:
    def subscribe(self, listener): ...
    def emit(self, event_name, payload):
        for listener in list(self._listeners):
            try:
                listener(event_name, payload)
            except Exception as e:
                sys.stderr.write(f'webserve: event listener failed for {event_name}: {e}\n')
```

### Repeat

1. Wherever webserve prints to the console, also `emit_event(name, payload)` with
   only JSON-safe fields (never pass handler/server objects into a payload).
2. Gate the built-in `Logger` with an `enabled=` flag and route all its output
   through one `_put(record)` helper.
3. Keep genuinely fatal errors as direct `print(..., file=sys.stderr)` — they are
   not "regular logging" and must not be silenced.
