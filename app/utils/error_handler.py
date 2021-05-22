from flask import jsonify
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden
from werkzeug.exceptions import NotFound, MethodNotAllowed, InternalServerError

from app.utils.error_codes import ErrorCode


class GeneralException(BaseException):
    def __init__(self, error_code: ErrorCode, msg: str):
        self.error_code = error_code
        self.msg = msg
        if error_code is None:
            error_code = ErrorCode.INTERNAL_SERVER_ERROR
        self.kwargs = {
            'code': error_code.code,
            'description': error_code.msg,
            'message': msg
        }

    def __str__(self):
        return f'[error_type:{self.error_code.error_type}] [status_code:{self.error_code.code}][message:{self.msg}]'


class BadRequestException(GeneralException):
    def __init__(self, error_code=ErrorCode.BAD_REQUEST, msg=None):
        super().__init__(error_code, msg)


class UnauthorizedException(GeneralException):
    def __init__(self, error_code=ErrorCode.UNAUTHORIZED, msg=None):
        super().__init__(error_code, msg)


class ForbiddenException(GeneralException):
    def __init__(self, error_code=ErrorCode.FORBIDDEN, msg=None):
        super().__init__(error_code, msg)


class NotFoundException(GeneralException):
    def __init__(self, error_code=ErrorCode.NOT_FOUND, msg=None):
        super().__init__(error_code, msg)


class NotAllowedException(GeneralException):
    def __init__(self, error_code=ErrorCode.NOT_ALLOWED, msg=None):
        super().__init__(error_code, msg)


class InternalError(GeneralException):
    def __init__(self, error_code=ErrorCode.INTERNAL_SERVER_ERROR, msg=None):
        super().__init__(error_code, msg)


class ErrorHandler:
    @staticmethod
    def bad_request(error_code=ErrorCode.BAD_REQUEST, msg=None):
        raise BadRequestException(error_code, msg)

    @staticmethod
    def unauthorized(error_code=ErrorCode.UNAUTHORIZED, msg=None):
        raise UnauthorizedException(error_code, msg)

    @staticmethod
    def forbidden(error_code=ErrorCode.FORBIDDEN, msg=None):
        raise ForbiddenException(error_code, msg)

    @staticmethod
    def not_found(error_code=ErrorCode.NOT_FOUND, msg=None):
        raise NotFoundException(error_code, msg)

    @staticmethod
    def not_allowed(error_code=ErrorCode.NOT_ALLOWED, msg=None):
        raise NotAllowedException(error_code, msg)

    @staticmethod
    def internal_error(error_code=ErrorCode.INTERNAL_SERVER_ERROR, msg=None):
        raise InternalError(error_code, msg)

    @staticmethod
    def handle_error(e):
        res = jsonify(e.kwargs)
        res.status_code = e.kwargs['code']
        return res


def error_handler(error):
    code = error.code
    msg = error.description
    try:
        if code == 400:
            ErrorHandler.bad_request(msg=msg)
        elif code == 401:
            ErrorHandler.unauthorized(msg=msg)
        elif code == 403:
            ErrorHandler.forbidden(msg=msg)
        elif code == 404:
            ErrorHandler.not_found(msg=msg)
        elif code == 405:
            ErrorHandler.not_allowed(msg=msg)
        else:
            ErrorHandler.internal_error(msg=msg)
    except BaseException as e:
        return ErrorHandler.handle_error(e)


def register_error_handler(app):
    app.register_error_handler(BadRequest, error_handler)
    app.register_error_handler(Unauthorized, error_handler)
    app.register_error_handler(Forbidden, error_handler)
    app.register_error_handler(NotFound, error_handler)
    app.register_error_handler(MethodNotAllowed, error_handler)
    app.register_error_handler(InternalServerError, error_handler)