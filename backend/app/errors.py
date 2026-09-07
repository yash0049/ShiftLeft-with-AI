from werkzeug.exceptions import HTTPException


class ValidationError(Exception):
    """Raised when a request body fails field validation."""

    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        return {"error": "Validation failed", "details": exc.errors}, 400

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return {"error": exc.description}, exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.exception("Unhandled error")
        return {"error": "Internal server error"}, 500
