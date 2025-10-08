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


# Создаём единый объект конфига с доступом ко всем секциям
class _ConfigProxy:
    """Прокси-класс для удобного доступа к разным секциям конфига."""

    def __init__(self):
        self._common = None
        self._tgbot = None
        self._webapp = None

    @property
    def common(self):
        """Общие настройки."""
        if self._common is None:
            self._common = get_config("common")
        return self._common

    @property
    def tgbot(self):
        """Настройки телеграм-бота."""
        if self._tgbot is None:
            self._tgbot = get_config("tgbot")
        return self._tgbot

    @property
    def webapp(self):
        """Настройки веб-приложения."""
        if self._webapp is None:
            self._webapp = get_config("webapp")
        return self._webapp

    # Для удобства делаем алиасы на основные секции tgbot
    @property
    def bot(self):
        """Алиас для tgbot.bot."""
        return self.tgbot.bot

    @property
    def database(self):
        """Алиас для tgbot.database."""
        return self.tgbot.database

    @property
    def features(self):
        """Алиас для tgbot.features."""
        return self.tgbot.features

    @property
    def logging(self):
        """Алиас для tgbot.logging."""
        return self.tgbot.logging


# Единый объект конфига
config = _ConfigProxy()
