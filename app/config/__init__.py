from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(env_name: str = "development"):
    return config_map.get(env_name, DevelopmentConfig)
