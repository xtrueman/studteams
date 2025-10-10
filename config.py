"""
Модуль конфигурации StudTeams с использованием OmegaConf.

Поддерживает послойную загрузку конфигов:
- common.yaml - общие настройки
- tgbot.yaml / webapp.yaml - специфичные для компонентов
- secrets.yaml - общие секреты
- secrets-tgbot.yaml / secrets-webapp.yaml - специфичные секреты

Все ключи объединяются в общем корне без лишней иерархии.
"""

from pathlib import Path

from omegaconf import OmegaConf


class Config:
    """Класс для работы с конфигурацией приложения."""

    def __init__(self, component: str = "tgbot"):
        """
        Инициализация конфигурации.

        Args:
            component: Компонент системы ('tgbot' или 'webapp')
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

        # 2. Загружаем специфичный конфиг компонента (перезаписывает common)
        component_path = self.config_dir / f"{self.component}.yaml"
        if component_path.exists():
            configs.append(OmegaConf.load(component_path))

        # 3. Загружаем общие секреты
        secrets_path = self.config_dir / "secrets.yaml"
        if secrets_path.exists():
            configs.append(OmegaConf.load(secrets_path))

        # 4. Загружаем специфичные секреты компонента (перезаписывают общие секреты)
        component_secrets_path = self.config_dir / f"secrets-{self.component}.yaml"
        if component_secrets_path.exists():
            configs.append(OmegaConf.load(component_secrets_path))

        # Объединяем все конфиги (последующие перезаписывают предыдущие)
        self._config = OmegaConf.merge(*configs) if configs else OmegaConf.create()

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
            # OmegaConf.select может принимать None если конфиг не загружен
            if self._config is None:
                return default
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


def get_config(component: str = "tgbot") -> Config:
    """
    Получить конфиг для компонента.

    Args:
        component: Компонент системы ('tgbot' или 'webapp')

    Returns:
        Config: Объект конфигурации
    """
    global _tgbot_config, _webapp_config

    if component == "tgbot":
        if _tgbot_config is None:
            _tgbot_config = Config("tgbot")
        return _tgbot_config
    elif component == "webapp":
        if _webapp_config is None:
            _webapp_config = Config("webapp")
        return _webapp_config
    else:
        # По умолчанию tgbot
        if _tgbot_config is None:
            _tgbot_config = Config("tgbot")
        return _tgbot_config


# Единый объект конфига (по умолчанию для tgbot)
config = get_config("tgbot")
