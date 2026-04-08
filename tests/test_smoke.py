"""Basic smoke test to verify app factory bootstraps successfully."""

from app import create_app


def test_create_app_smoke() -> None:
    """Ensure Flask app instance can be created for testing config."""
    app = create_app("testing")
    assert app is not None
