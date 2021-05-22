import logging as log
import traceback
from functools import wraps

from flask import current_app, Response, request

from app.utils.error_handler import ErrorHandler, GeneralException, InternalError


def subscribe(bp, route, methods):
    def decorator(f):
        @bp.route(route, methods=methods)
        @wraps(f)
        def wrapper(*args, **kwargs):
            log_info(f, request)
            res = Response()
            with current_app.app_context():
                try:
                    res = f(*args, **kwargs)
                except GeneralException as e:
                    tb = traceback.format_exc()
                    log_error(f, request, "GeneralException", e, tb)
                    res = ErrorHandler.handle_error(e)
                except Exception as e:
                    tb = traceback.format_exc()
                    log_error(f, request, "Exception", e, tb)
                    res = ErrorHandler.handle_error(InternalError(msg=str(e)))
                finally:
                    return res

        return wrapper

    return decorator


def log_info(f, r):
    module = ".".join(f.__module__.split(".")[-2:])
    info_msg = "[module:{}] [method:{}] [func:{}]"
    log.info(info_msg.format(module, r.method, f.__name__))


def log_error(f, r, type, e, tb):
    err_msg = "[mod:{}] [method:{}] [func:{}] [event:ERROR] [type:{}] {}\n{}"
    module = ".".join(f.__module__.split(".")[-2:])
    log.error(err_msg.format(module, r.method, f.__name__, type, e, tb))
