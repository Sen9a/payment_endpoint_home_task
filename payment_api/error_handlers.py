"""Registers consistent {"error": {"code", "message"}} error handling.

It's convenient to raise exceptions and have that set the HTTP response
rather than craft a response for each error.
"""
from http import HTTPStatus

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from payment_api.constants import ErrorCode, ErrorMessage
from payment_api.database.db import db_session
from payment_api.exceptions import APIException


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_errorhandlers(flask_app) -> None:

    @flask_app.errorhandler(APIException)
    def api_exception_handler(err: APIException):
        flask_app.logger.warning(repr(err))
        db_session.rollback()
        return err.to_json(), err.status_code

    @flask_app.errorhandler(HTTPException)
    def http_exception_handler(err: HTTPException):
        # routing errors (404/405) raised by Flask/Werkzeug itself
        return _error_body(err.name.upper().replace(' ', '_'), err.description), err.code

    @flask_app.errorhandler(SQLAlchemyError)
    def db_error_handler(err: SQLAlchemyError):
        flask_app.logger.exception(repr(err))
        db_session.rollback()
        return _error_body(ErrorCode.DB_ERROR, ErrorMessage.DB_ERROR), HTTPStatus.INTERNAL_SERVER_ERROR.value

    @flask_app.errorhandler(Exception)
    def unhandled_exception_handler(err: Exception):
        flask_app.logger.exception(repr(err))
        db_session.rollback()
        # Never leak internal details
        return _error_body(ErrorCode.INTERNAL_ERROR, ErrorMessage.INTERNAL_ERROR), \
            HTTPStatus.INTERNAL_SERVER_ERROR.value
