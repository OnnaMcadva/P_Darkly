# Path Traversal (Directory Traversal)

> **Тип уязвимости / Vulnerability Type:** Path Traversal  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Приложение принимает имя страницы через параметр `?page=` и передаёт его напрямую в функцию чтения файла — без какой-либо проверки. Это позволяет выйти за пределы веб-директории, поднявшись вверх по файловой системе с помощью последовательностей `../`, и прочитать любой файл на сервере — включая системные файлы Linux.

---

### Шаг 1 — Как работает параметр `?page=`

Нормальное использование выглядит так:
```
http://127.0.0.1:8080/?page=signin
```

Сервер берёт значение `signin` и читает файл вида:
```
/var/www/html/pages/signin.php
```

Если разработчик написал что-то вроде:
```php
include($_GET['page']);
```
...то он передаёт пользовательский ввод напрямую в файловую функцию. Никакой проверки — никакой защиты.

**Почему `?page=` сразу подозрителен?**

Параметр который принимает «имя страницы» — классический признак file inclusion. Это первое что проверяют на path traversal: если сервер читает файлы по имени которое ты сам передаёшь — скорее всего можно передать что-то неожиданное.

---

### Шаг 2 — Что такое `../` и как это работает

В файловых системах Linux (и Windows) `../` означает «перейти на директорию выше»:

```
/var/www/html/pages/   — мы здесь
../                    — /var/www/html/
../../                 — /var/www/
../../../              — /var/
../../../../           — /
```

Если мы передадим в `?page=` строку `../../../../etc/passwd`, сервер построит путь:
```
/var/www/html/pages/../../../../etc/passwd
```

Что после нормализации (разворачивания `../`) превращается в:
```
/etc/passwd
```

Сервер читает и отдаёт нам системный файл.

**Почему `../` не блокируется?**

Потому что разработчик не добавил никакой проверки. В нормально написанном приложении значение `?page=` должно проходить через whitelist (список разрешённых имён) или проверку что итоговый путь находится внутри разрешённой директории. Здесь этого нет.

---

### Шаг 3 — Запрос файла `/etc/passwd`

Открываем в браузере:
```
http://127.0.0.1:8080/?page=../../../../../../../../etc/passwd
```

**Почему так много `../`?**

Мы не знаем точно как глубоко в файловой системе лежит директория приложения. Поэтому берём с запасом — 8 штук. Если мы поднялись выше корня `/` — ничего страшного, файловая система просто остановится на `/` и дальше не пойдёт. Путь `/etc/passwd` будет найден в любом случае.

**Что такое `/etc/passwd`?**

Это стандартный системный файл Linux. Содержит список всех пользователей системы: имя, UID, GID, домашнюю директорию, оболочку. Исторически там хранились и пароли (отсюда название), но сейчас пароли вынесены в `/etc/shadow`.

Пример содержимого:
```
root:x:0:0:root:/root:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

Этот файл читается без прав суперпользователя — поэтому он идеален для проверки path traversal.

**Флаг появляется прямо в ответе** — сервер вернул содержимое файла и флаг встроен туда.

---

### Шаг 4 — Что ещё можно было прочитать

| Файл | Что содержит |
|------|-------------|
| `/etc/passwd` | Список пользователей системы |
| `/etc/shadow` | Хеши паролей (нужны права root) |
| `/proc/self/environ` | Переменные окружения процесса веб-сервера — могут содержать токены, пути, пароли |
| `/proc/self/cmdline` | Командная строка с которой запущен процесс |
| `/var/www/html/index.php` | Исходный код самого приложения |

В реальной атаке через `/proc/self/environ` часто утекают переменные окружения с паролями к базам данных, API-ключами и т.д.

---

### Логика атаки — цепочка

```
?page= принимает произвольный ввод без проверки
    ↓  передаём ../../../../../etc/passwd вместо имени страницы
Сервер строит путь: /var/www/html/pages/../../../../etc/passwd
    ↓  файловая система нормализует путь → /etc/passwd
Сервер читает файл и возвращает содержимое
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Пользовательский ввод передаётся в файловую функцию напрямую | Никогда не передавать `$_GET` параметры в `include()`, `fopen()`, `file_get_contents()` |
| Нет проверки итогового пути | Использовать `realpath()` и проверять что путь начинается с разрешённой директории |
| Нет whitelist разрешённых страниц | Хранить список допустимых имён страниц и принимать только их |
| Процесс веб-сервера имеет широкие права | Запускать с минимальными правами — только чтение нужных директорий |

**Пример правильной проверки на PHP:**
```php
$allowed = ['home', 'signin', 'about'];
$page = $_GET['page'];

if (!in_array($page, $allowed)) {
    die('Page not found');
}

include('/var/www/html/pages/' . $page . '.php');
```

---
---

## 🇬🇧 English Version

### Overview — What Happened

The application accepts a page name through the `?page=` parameter and passes it directly to a file-reading function — without any validation. This allows escaping the web directory by climbing the filesystem using `../` sequences, and reading any file on the server — including Linux system files.

---

### Step 1 — How the `?page=` Parameter Works

Normal usage looks like this:
```
http://127.0.0.1:8080/?page=signin
```

The server takes the value `signin` and reads a file such as:
```
/var/www/html/pages/signin.php
```

If the developer wrote something like:
```php
include($_GET['page']);
```
...then they are passing user input directly into a filesystem function. No validation — no protection.

**Why is `?page=` immediately suspicious?**

A parameter that accepts a "page name" is a classic sign of file inclusion. This is the first thing to test for path traversal: if the server reads files by a name you supply yourself, you can likely supply something unexpected.

---

### Step 2 — What `../` Is and How It Works

In Linux (and Windows) filesystems, `../` means "go up one directory":

```
/var/www/html/pages/   — we start here
../                    — /var/www/html/
../../                 — /var/www/
../../../              — /var/
../../../../           — /
```

If we pass `../../../../etc/passwd` in `?page=`, the server builds the path:
```
/var/www/html/pages/../../../../etc/passwd
```

Which after normalization (resolving the `../` segments) becomes:
```
/etc/passwd
```

The server reads and returns the system file.

**Why isn't `../` blocked?**

Because the developer added no validation. In a properly written application, the `?page=` value should go through a whitelist of allowed names, or a check that the resolved path stays inside the permitted directory. Neither exists here.

---

### Step 3 — Requesting `/etc/passwd`

Open in browser:
```
http://127.0.0.1:8080/?page=../../../../../../../../etc/passwd
```

**Why so many `../`?**

We don't know exactly how deep in the filesystem the application directory sits. So we use plenty — 8 segments. If we go above the root `/` — no problem, the filesystem simply stops at `/` and won't go further. The path `/etc/passwd` will be reached regardless.

**What is `/etc/passwd`?**

It is a standard Linux system file. It contains a list of all system users: name, UID, GID, home directory, shell. Historically it also stored passwords (hence the name), but passwords are now stored in `/etc/shadow`.

Example content:
```
root:x:0:0:root:/root:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

This file is readable without superuser privileges — which makes it the ideal target for testing path traversal.

**The flag appears directly in the response** — the server returned the file contents and the flag is embedded within.

---

### Step 4 — Other Files That Could Be Read

| File | Contents |
|------|----------|
| `/etc/passwd` | System user list |
| `/etc/shadow` | Password hashes (requires root) |
| `/proc/self/environ` | Environment variables of the web server process — may contain tokens, paths, passwords |
| `/proc/self/cmdline` | Command line used to start the process |
| `/var/www/html/index.php` | Source code of the application itself |

In real attacks, `/proc/self/environ` often leaks environment variables containing database passwords, API keys, and other secrets.

---

### Attack Chain Summary

```
?page= accepts arbitrary input without validation
    ↓  we pass ../../../../../etc/passwd instead of a page name
Server builds path: /var/www/html/pages/../../../../etc/passwd
    ↓  filesystem normalizes the path → /etc/passwd
Server reads the file and returns its contents
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| User input passed directly to filesystem function | Never pass `$_GET` parameters into `include()`, `fopen()`, `file_get_contents()` |
| No validation of the resolved path | Use `realpath()` and verify the path starts with the allowed base directory |
| No whitelist of allowed page names | Maintain a list of permitted page names and accept only those |
| Web server process has broad filesystem permissions | Run with minimum required permissions — read access to needed directories only |

**Example of correct validation in PHP:**
```php
$allowed = ['home', 'signin', 'about'];
$page = $_GET['page'];

if (!in_array($page, $allowed)) {
    die('Page not found');
}

include('/var/www/html/pages/' . $page . '.php');
```

---
