from app.utils.error_handler import ErrorHandler


def validate_request(request_schema, body):
    errors = request_schema.errors(body) or []
    if errors:
        msg = f'Bad request, fields: {errors}'
        ErrorHandler.bad_request(msg=msg)
