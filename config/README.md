# Конфигурация StudTeams

Этот каталог содержит конфигурационные файлы для всех компонентов системы StudTeams.

## Структура конфигов

### Общие конфиги (коммитятся в Git)

- **`common.yaml`** - Общие настройки для всех компонентов
  - Настройки функциональности (включение reviews, кол-во спринтов и т.д.)
  - Параметры БД (без паролей)
  - Настройки логирования

- **`tgbot.yaml`** - Специфичные настройки для Telegram бота
  - Username бота
  - Пути к логам

- **`webapp.yaml`** - Специфичные настройки для веб-приложения
  - Host и port веб-сервера
  - Режим разработки/продакшен
  - Пути к логам

### Секретные конфиги (НЕ коммитятся в Git)

⚠️ **Эти файлы содержат секретные данные и добавлены в `.gitignore`**

- **`secrets.yaml`** - Общие секреты
  - Пароли к базам данных

- **`secrets-tgbot.yaml`** - Секреты для Telegram бота
  - Токен бота

- **`secrets-webapp.yaml`** - Секреты для веб-приложения (если нужны)

### Шаблоны (коммитятся в Git)

- **`*.yaml.template`** - Шаблоны для секретных файлов
  - Копируйте их и заполняйте своими данными

## Первоначальная настройка

1. Скопируйте шаблоны:
   ```bash
   cp config/secrets.yaml.template config/secrets.yaml
   cp config/secrets-tgbot.yaml.template config/secrets-tgbot.yaml
   ```

2. Отредактируйте файлы `secrets*.yaml`, заполнив реальные значения:
   ```yaml
   # secrets.yaml
   database:
     prod:
       user: your_mysql_user
       password: your_mysql_password
   
   # secrets-tgbot.yaml
   bot:
     token: "YOUR_BOT_TOKEN_HERE"
   ```

## Использование в коде

### Вариант 1: Для обратной совместимости (старый стиль)

```python
import config

# Используем глобальные переменные
print(config.BOT_TOKEN)
print(config.MYSQL_PROD)
print(config.ENABLE_REVIEWS)
```

### Вариант 2: Новый стиль с OmegaConf

```python
from config import get_config

# Для бота
cfg = get_config("tgbot")
token = cfg.get("bot.token")
db_host = cfg.get("database.prod.host")

# Для веб-приложения
cfg = get_config("webapp")
port = cfg.get("web.port", 8000)
```

## Послойная загрузка

Конфиги загружаются послойно, каждый следующий переопределяет предыдущий:

1. `common.yaml` - базовые настройки
2. `tgbot.yaml` / `webapp.yaml` - специфичные настройки компонента
3. `secrets.yaml` - общие секреты
4. `secrets-tgbot.yaml` / `secrets-webapp.yaml` - секреты компонента

Это позволяет:
- Держать общие настройки в одном месте
- Переопределять их для конкретных компонентов
- Отделять секреты от публичных настроек

## Безопасность

⚠️ **ВАЖНО:** 
- Никогда не коммитьте файлы `secrets*.yaml` в Git!
- Все секретные файлы уже добавлены в `.gitignore`
- Используйте шаблоны для документирования необходимых секретов
