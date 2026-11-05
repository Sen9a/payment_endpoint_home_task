"""Registers consistent {"error": {"code", "message"}} error handling.

Two layers are covered:
- the underlying Flask app, for exceptions raised inside operation handlers
- the Connexion ASGI ExceptionMiddleware, for request validation and routing
  errors raised before/around the Flask app (they would otherwise be
  rendered as application/problem+json)
"""
import json
from http import HTTPStatus

from connexion.exceptions import ProblemException
from connexion.lifecycle import ConnexionResponse
from sqlalchemy.exc import SQLAlchemyError

from payment_api.constants import ErrorCode, ErrorMessage, STATUS_TO_CODE
from payment_api.database.db import db_session
from payment_api.exceptions import APIException


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_errorhandlers(connexion_app, flask_app) -> None:
    """It's convenient to raise exceptions and have that set the HTTP response
    rather than craft a response for each error.
    """

    # --- Flask-side handlers (exceptions raised inside operation handlers) ---

    @flask_app.errorhandler(APIException)
    def api_exception_handler(err: APIException):
        flask_app.logger.warning(repr(err))
        db_session.rollback()
        return err.to_json(), err.status_code

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

    # --- Connexion middleware handlers (validation / routing) ---

    def problem_handler(_request, exc: ProblemException) -> ConnexionResponse:
        code = STATUS_TO_CODE.get(exc.status, ErrorCode.INTERNAL_ERROR)
        message = exc.detail or exc.title or HTTPStatus(exc.status).phrase
        if exc.status >= 500:
            flask_app.logger.error(repr(exc))
            code, message = ErrorCode.INTERNAL_ERROR, ErrorMessage.INTERNAL_ERROR
        else:
            flask_app.logger.warning(repr(exc))
        return ConnexionResponse(
            status_code=exc.status,
            mimetype='application/json',
            body=json.dumps(_error_body(code, message)),
        )

    connexion_app.add_error_handler(ProblemException, problem_handler)

    def api_exception_middleware_handler(_request, exc: APIException) -> ConnexionResponse:
        flask_app.logger.warning(repr(exc))
        return ConnexionResponse(
            status_code=exc.status_code,
            mimetype='application/json',
            body=json.dumps(exc.to_json()),
        )

    connexion_app.add_error_handler(APIException, api_exception_middleware_handler)
