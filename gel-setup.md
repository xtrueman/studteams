# Настройка EdgeDB (Gel) для проекта StudTeams

## Установка EdgeDB

### На macOS:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
```

### На Linux:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
```

После установки перезапустите терминал или выполните:
```bash
source ~/.edgedb/env
```

## Инициализация проекта

1. **Перейдите в директорию проекта:**
   ```bash
   cd /path/to/studteams
   ```

2. **Инициализируйте EdgeDB проект:**
   ```bash
   edgedb project init
   ```
   - Выберите "Yes" для создания нового экземпляра
   - Подтвердите имя проекта (studteams)

3. **Создайте миграцию на основе схемы:**
   ```bash
   edgedb migration create
   ```
   - EdgeDB автоматически обнаружит схему в `dbschema/default.esdl`
   - Подтвердите создание миграции

4. **Примените миграцию:**
   ```bash
   edgedb migrate
   ```

## Проверка установки

**Проверьте статус проекта:**
```bash
edgedb project info
```

**Запустите UI для просмотра схемы:**
```bash
edgedb ui
```

**Подключитесь к базе данных:**
```bash
edgedb
```

## Основные команды для работы

- **Создание новой миграции после изменения схемы:**
  ```bash
  edgedb migration create
  edgedb migrate
  ```

- **Просмотр состояния миграций:**
  ```bash
  edgedb migration status
  ```

- **Запуск REPL для выполнения запросов:**
  ```bash
  edgedb
  ```

- **Выполнение запроса из командной строки:**
  ```bash
  edgedb query "SELECT Student { name, tg_id }"
  ```

## Структура файлов проекта

```
studteams/
├── edgedb.toml                    # Конфигурация проекта
├── dbschema/
│   ├── default.esdl              # Основная схема базы данных
│   └── migrations/
│       └── 00001.edgeql          # Первоначальная миграция
└── gel-setup.md                  # Данная инструкция
```

## Примеры запросов

**Добавление студента:**
```edgeql
INSERT Student {
    tg_id := 123456789,
    name := "Иван Иванов",
    group_num := "ИС-101"
};
```

**Создание команды:**
```edgeql
INSERT Team {
    team_name := "Команда А",
    product_name := "Мобильное приложение",
    invite_code := "ABC12345",
    admin := (SELECT Student FILTER .tg_id = 123456789)
};
```

**Просмотр всех команд с участниками:**
```edgeql
SELECT Team {
    team_name,
    product_name,
    admin: { name },
    members: {
        student: { name },
        role
    }
};
```