"""
Модуль конфигурации StudTeams с использованием OmegaConf.

Поддерживает послойную загрузку конфигов:
- common.yaml - общие настройки
- tgbot.yaml / webapp.yaml - специфичные для компонентов
- secrets.yaml - общие секреты
- secrets-tgbot.yaml / secrets-webapp.yaml - специфичные секреты
"""

from pathlib import Path

from omegaconf import OmegaConf


class Config:
    """Класс для работы с конфигурацией приложения."""

    def __init__(self, component: str = "common"):
        """
        Инициализация конфигурации.

        Args:
            component: Компонент системы ('tgbot', 'webapp' или 'common')
        """
        self.component = component
        self.config_dir = Path(__file__).parent / "config"
        self._config = None
        self._load_configs()

    def _load_configs(self):
        """Загрузка конфигов послойно."""
        configs = []

        # 1. Загружаем общий конфиг
        common_path = self.config_dir / "common.yaml"
        if common_path.exists():
            configs.append(OmegaConf.load(common_path))

        # 2. Загружаем специфичный конфиг компонента
        if self.component != "common":
            component_path = self.config_dir / f"{self.component}.yaml"
            if component_path.exists():
                configs.append(OmegaConf.load(component_path))

        # 3. Загружаем общие секреты
        secrets_path = self.config_dir / "secrets.yaml"
        if secrets_path.exists():
            configs.append(OmegaConf.load(secrets_path))
        else:
            # Предупреждение о том, что secrets.yaml отсутствует (используются значения по умолчанию)
            pass

        # 4. Загружаем специфичные секреты компонента
        if self.component != "common":
            component_secrets_path = self.config_dir / f"secrets-{self.component}.yaml"
            if component_secrets_path.exists():
                configs.append(OmegaConf.load(component_secrets_path))

        # Объединяем все конфиги (последующие переопределяют предыдущие)
        self._config = OmegaConf.merge(*configs)

    def get(self, key: str, default=None):
        """
        Получить значение конфига по ключу.

        Args:
            key: Путь к значению через точку (например, 'database.prod.host')
            default: Значение по умолчанию

        Returns:
            Значение конфига или default
        """
        try:
            return OmegaConf.select(self._config, key, default=default)
        except Exception:
            return default

    def __getattr__(self, name):
        """Позволяет обращаться к конфигу через точку."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return getattr(self._config, name)

    def to_dict(self):
        """Преобразовать конфиг в словарь."""
        return OmegaConf.to_container(self._config, resolve=True)


# Глобальные экземпляры конфигов для разных компонентов
_tgbot_config = None
_webapp_config = None
_common_config = None


def get_config(component: str = "common") -> Config:
    """
    Получить конфиг для компонента.

    Args:
        component: Компонент системы ('tgbot', 'webapp' или 'common')

    Returns:
        Config: Объект конфигурации
    """
    global _tgbot_config, _webapp_config, _common_config

    if component == "tgbot":
        if _tgbot_config is None:
            _tgbot_config = Config("tgbot")
        return _tgbot_config
    elif component == "webapp":
        if _webapp_config is None:
            _webapp_config = Config("webapp")
        return _webapp_config
    else:
        if _common_config is None:
            _common_config = Config("common")
        return _common_config


# Для обратной совместимости создаем переменные в стиле старого config.py
def _init_legacy_vars():
    """Инициализация переменных для обратной совместимости."""
    cfg = get_config("tgbot")

    # Bot settings
    global BOT_USERNAME, BOT_TOKEN
    BOT_USERNAME = cfg.get("bot.username", "@SSAU_SoftDevMgmt_bot")
    BOT_TOKEN = cfg.get("bot.token", "")

    # Database settings
    global MYSQL_PROD, MYSQL_TEST
    MYSQL_PROD = {
        'host': cfg.get("database.prod.host", "localhost"),
        'user': cfg.get("database.prod.user", "studteams"),
        'password': cfg.get("database.prod.password", ""),
        'database': cfg.get("database.prod.database", "studteams"),
        'charset': cfg.get("database.prod.charset", "utf8mb4"),
        'collation': cfg.get("database.prod.collation", "utf8mb4_unicode_ci"),
        'autocommit': cfg.get("database.prod.autocommit", True),
        'consume_results': True,
        'auth_plugin': cfg.get("database.prod.auth_plugin", "mysql_native_password"),
    }

    MYSQL_TEST = {
        'host': cfg.get("database.test.host", "localhost"),
        'user': cfg.get("database.test.user", "studteams"),
        'password': cfg.get("database.test.password", ""),
        'database': cfg.get("database.test.database", "studteams_test"),
        'charset': cfg.get("database.test.charset", "utf8mb4"),
        'collation': cfg.get("database.test.collation", "utf8mb4_unicode_ci"),
        'autocommit': cfg.get("database.test.autocommit", True),
        'consume_results': True,
        'auth_plugin': cfg.get("database.test.auth_plugin", "mysql_native_password"),
    }

    # Features
    global ENABLE_REVIEWS, MAX_SPRINT_NUMBER, MIN_RATING, MAX_RATING
    ENABLE_REVIEWS = cfg.get("features.enable_reviews", True)
    MAX_SPRINT_NUMBER = cfg.get("features.max_sprint_number", 6)
    MIN_RATING = cfg.get("features.min_rating", 1)
    MAX_RATING = cfg.get("features.max_rating", 10)

    # Logging
    global LOG_FILE, LOG_LEVEL, LOG_ROTATION, LOG_RETENTION
    LOG_FILE = cfg.get("logging.file", "logs/studhelper-bot.log")
    LOG_LEVEL = cfg.get("logging.level", "INFO")
    LOG_ROTATION = cfg.get("logging.rotation", "10 MB")
    LOG_RETENTION = cfg.get("logging.retention", "1 month")


# Инициализируем переменные при импорте модуля
_init_legacy_vars()
