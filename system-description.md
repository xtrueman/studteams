# ТЗ для проекта StudTeams.

Проект StudTeams предназначен для помощи преподавателю в отслеживании прогресса стеденческих команд и их участников при выполнении ими студенческих проектов (работа над проектами ведётся по методологиям Scrum и Kanban).
Система состоит из 2-х компонент:
1. Telegram-бот StudHelper, в котором студенты регистрируют свои команды, а участники команд по истечении каждого Scrum-спринта или Kanban-каденции отчитываются о проделанной лично ими работы в данном спринте. Также в самом конце работы над проектом студенты оценивают 
2. Web-сервис StudHelper.ru, написанный на Flask, в котором:
- участники команд, зарегистрировавшиеся в боте, перед поулчением зачёта отслеживают свои «долги» (нужно иметь определённое коичество отчётов о проделанной работе + в конце семестра дать оценки остальным членам команд)
- администратор (преподаватель) видит общий отчёт по всем командам и всем членам команд — у кого имеются «долги» и т.п.

Сейчас уже есть первая версия данного проекта, которую я хочу полностью передалать и переписать с нуля.

- Сейчас данные храняться в СУБД (MySQL), схема данных подробно описана в файле schema2.sql
- Инструкция по использованию ботом описана в studhelper_bot_manual.md

Я собираюсь переписать с нуля на python данный проект.

В качестве СУБД я собираюсь использовать EdgeDB (сейчас называеся "Gel": https://www.geldata.com/)

Что мне необходимо в первую очередь:
- Создать схему данных для EdgeDB (Gel), основанную на текущей модели данных, описанной в schema2.sql
- Создай все файлы, необходимые для создания и запуска СУБД на Gel, а также в отдельном файле (gel-setup.md) инструкцию как и в каком порядке создать СУБД на Gel, какие команды необходимо выполнить (на Linux или MacOS).