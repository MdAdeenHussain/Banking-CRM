"""Run module for local Flask execution.

Usage:
    flask --app run.py run
or:
    python3 run.py
"""

# =====================================
# SECTION: Imports
# =====================================
import os

from app import create_app


# =====================================
# SECTION: Application Instance
# =====================================
app = create_app(os.getenv("APP_ENV", "development"))


# =====================================
# SECTION: Local Runner
# =====================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=app.config.get("DEBUG", False))
