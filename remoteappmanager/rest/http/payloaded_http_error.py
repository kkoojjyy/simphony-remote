from tornado.httpclient import HTTPError


class PayloadedHTTPError(HTTPError):
    def __init__(self, code, payload, message=None, response=None):
        """Provides a HTTPError that contains a string payload to output
        as a response. If the payload is None, behaves like a regular
        HTTPError, producing no payload in the response.
        """
        super().__init__(code, message, response)

        if payload is not None and not isinstance(payload, str):
            raise ValueError("payload must be a string.")

        self.payload = payload
