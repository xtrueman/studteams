# Настройка SSL сертификатов с Let's Encrypt

Это руководство описывает настройку SSL сертификатов для StudTeams с использованием certbot (Let's Encrypt).

## Предварительные требования

1. Домен должен указывать на ваш сервер (DNS A-запись настроена)
2. Порты 80 и 443 должны быть открыты в файрволе
3. Nginx должен быть установлен и запущен

## Установка Certbot

### Через pip (рекомендуется для совместимости с проектом)

```bash
# Установка certbot в virtualenv проекта
cd /srv/studteams
source venv/bin/activate
pip install certbot certbot-nginx

# Или глобально через pip
sudo pip3 install certbot certbot-nginx
```

### Через пакетный менеджер (альтернатива)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

## Получение сертификата

### Способ 1: Автоматическая настройка через certbot-nginx (рекомендуется)

Certbot автоматически настроит nginx конфигурацию:

```bash
sudo certbot --nginx -d studteams.example.com
```

При первом запуске certbot попросит:
1. Email для уведомлений (важно для напоминаний об истечении сертификата)
2. Согласие с условиями использования
3. Опционально: согласие на рассылку новостей от EFF

### Способ 2: Ручная настройка с webroot

Если вы хотите управлять nginx конфигурацией вручную:

```bash
# Создаём директорию для ACME challenge
sudo mkdir -p /var/www/certbot

# Получаем сертификат
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d studteams.example.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email
```

Затем обновите пути к сертификатам в nginx конфигурации:
- Замените `studteams.example.com` на ваш реальный домен
- Перезагрузите nginx: `sudo systemctl reload nginx`

## Автоматическое обновление сертификатов

### Проверка автообновления

Certbot автоматически создаёт задание для обновления сертификатов. Проверьте его:

```bash
# Systemd timer (современные системы)
sudo systemctl list-timers | grep certbot

# Или cron job (старые системы)
sudo crontab -l | grep certbot
```

### Тестирование обновления

Проверьте, что автообновление работает (без реального обновления):

```bash
sudo certbot renew --dry-run
```

### Ручное обновление

Если нужно обновить сертификаты вручную:

```bash
sudo certbot renew
```

### Настройка хука для перезагрузки nginx

Создайте скрипт для автоматической перезагрузки nginx после обновления:

```bash
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy

sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

## Проверка конфигурации

### После получения сертификата

1. Проверьте nginx конфигурацию:
   ```bash
   sudo nginx -t
   ```

2. Перезагрузите nginx:
   ```bash
   sudo systemctl reload nginx
   ```

3. Проверьте HTTPS в браузере:
   ```
   https://studteams.example.com
   ```

4. Проверьте SSL рейтинг:
   ```
   https://www.ssllabs.com/ssltest/analyze.html?d=studteams.example.com
   ```

## Структура файлов Let's Encrypt

```
/etc/letsencrypt/
├── live/
│   └── studteams.example.com/
│       ├── fullchain.pem -> ../../archive/.../fullchain1.pem
│       ├── privkey.pem -> ../../archive/.../privkey1.pem
│       ├── cert.pem -> ../../archive/.../cert1.pem
│       └── chain.pem -> ../../archive/.../chain1.pem
├── archive/
│   └── studteams.example.com/
│       ├── fullchain1.pem
│       ├── privkey1.pem
│       └── ...
├── renewal/
│   └── studteams.example.com.conf
├── options-ssl-nginx.conf
└── ssl-dhparams.pem
```

## Управление сертификатами

### Список сертификатов

```bash
sudo certbot certificates
```

### Отзыв сертификата

```bash
sudo certbot revoke --cert-path /etc/letsencrypt/live/studteams.example.com/cert.pem
```

### Удаление сертификата

```bash
sudo certbot delete --cert-name studteams.example.com
```

## Troubleshooting

### Проблема: Порт 80 не доступен

Убедитесь, что nginx запущен и порт 80 открыт:
```bash
sudo systemctl status nginx
sudo netstat -tlnp | grep :80
sudo ufw status  # для Ubuntu
sudo firewall-cmd --list-all  # для CentOS
```

### Проблема: DNS не настроен

Проверьте, что домен указывает на ваш сервер:
```bash
dig studteams.example.com
nslookup studteams.example.com
```

### Проблема: Certbot не может записать в webroot

Проверьте права доступа:
```bash
sudo ls -la /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

### Проблема: Сертификат не обновляется автоматически

Проверьте логи:
```bash
sudo journalctl -u certbot.timer
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

## Срок действия сертификата

- Сертификаты Let's Encrypt действительны **90 дней**
- Certbot автоматически обновляет их за **30 дней** до истечения
- Вы получите email уведомление за **20 дней** до истечения (если автообновление не работает)

## Безопасность

### Рекомендации

1. ✅ Используйте HSTS (уже включен в nginx конфиге)
2. ✅ Используйте только TLS 1.2+ (уже настроено через options-ssl-nginx.conf)
3. ✅ Регулярно обновляйте certbot: `pip install --upgrade certbot certbot-nginx`
4. ✅ Мониторьте истечение сертификатов

### Проверка безопасности

```bash
# Проверка версии TLS
openssl s_client -connect studteams.example.com:443 -tls1_2

# Проверка сертификата
openssl s_client -connect studteams.example.com:443 -showcerts
```

## Дополнительные домены

Чтобы добавить дополнительные домены (например, www):

```bash
sudo certbot --nginx -d studteams.example.com -d www.studteams.example.com
```

Или для существующего сертификата:

```bash
sudo certbot --nginx --expand -d studteams.example.com -d www.studteams.example.com
```
