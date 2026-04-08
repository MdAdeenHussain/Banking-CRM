"""Global error handling module.

Custom handlers keep the user experience consistent and provide one
place to connect logging/alerting in future phases.
"""

# =====================================
# SECTION: Imports
# =====================================
from flask import Flask, render_template


# =====================================
# SECTION: Error Handler Registration
# =====================================
def register_error_handlers(app: Flask) -> None:
    """Register HTTP error handlers for app-wide use."""

    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden access attempts."""
        _ = error
        return render_template("public/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle unknown routes."""
        _ = error
        return render_template("public/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle unexpected server errors."""
        _ = error
        return render_template("public/500.html"), 500
