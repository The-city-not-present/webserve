import sys


class WebserveEvents:
    """Minimal, scoped event emitter for webserve lifecycle and request events.

    webserve reports what is happening (server start/stop, each request, request
    errors) through this emitter instead of printing to the console itself. The
    caller subscribes plain callables ``listener(event_name, payload)`` and
    implements the actual logging.

    Subscribe before ``Webserver.run()``; events are then emitted from
    request-handler threads, so a listener must be safe to call concurrently.
    A listener failure must never break request serving, so ``emit`` isolates
    each listener and reports the failure to stderr.
    """

    def __init__(self):
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)
        return listener

    def emit(self, event_name, payload):
        for listener in list(self._listeners):
            try:
                listener(event_name, payload)
            except Exception as e:
                sys.stderr.write(f'webserve: event listener failed for {event_name}: {e}\n')
