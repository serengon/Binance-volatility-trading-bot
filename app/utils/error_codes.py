import enum


class ErrorCode(enum.Enum):
    BAD_REQUEST = (400, 'bad_request', 'Bad request.')
    UNAUTHORIZED = (401, 'unauthorized', 'Unauthorized.')
    FORBIDDEN = (403, 'forbidden', 'Forbidden.')
    NOT_FOUND = (404, 'not_found', 'Not Found.')
    NOT_ALLOWED = (405, 'not_allowed', 'Method Not Allowed.')
    INTERNAL_SERVER_ERROR = (500, 'server_error', 'Internal Server Error.')

    def __init__(self, code, error_type, msg):
        self.code = code
        self.error_type = error_type
        self.msg = msg
