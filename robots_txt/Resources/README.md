# Exposed Credentials via robots.txt

> **Тип уязвимости / Vulnerability Type:** Sensitive File Exposure  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Эта задача демонстрирует классическую ошибку: разработчик пытался «спрятать» директорию от поисковых роботов, указав её в `robots.txt`. Но `robots.txt` — это **публичный файл**, доступный абсолютно всем. Вместо того чтобы скрыть путь, он его **анонсировал**.

---

### Шаг 1 — Чтение `robots.txt`

```bash
curl http://localhost:8080/robots.txt
```

**Почему именно `robots.txt`?**

`robots.txt` — стандартный файл в корне веб-сайта. Он содержит инструкции для поисковых роботов (Google, Bing и др.) о том, какие страницы **не нужно индексировать**. Директива `Disallow` означает «не заходи сюда».

Проблема в том, что `robots.txt` не является защитой. Это просто вежливая просьба к добросовестным роботам. Любой человек может открыть этот файл и увидеть список «запрещённых» путей — что само по себе является разведывательной информацией.

**Что мы увидели:**
```
User-agent: *
Disallow: /whatever/
```

Директория `/whatever/` сразу стала интересной целью — она скрыта намеренно, значит там что-то есть.

---

### Шаг 2 — Просмотр скрытой директории

```bash
curl http://localhost:8080/whatever/
curl http://localhost:8080/whatever/htpasswd
```

**Почему мы туда пошли?**

Если разработчик специально скрывает директорию — в ней что-то важное. Мы открыли её напрямую в браузере (или через `curl`) и обнаружили файл `htpasswd`.

**Что такое `htpasswd`?**

Это файл аутентификации веб-сервера Apache. В нём хранятся имена пользователей и хеши их паролей для защиты директорий через HTTP Basic Auth. Хранить такой файл в веб-доступной директории — грубая ошибка безопасности: он должен лежать **вне** корневой директории сайта.

**Содержимое файла:**
```
root:437394baff5aa33daa618be47b75cb49
```

Формат: `имя_пользователя:хеш_пароля`

---

### Шаг 3 — Взлом MD5-хеша

**Почему хеш можно взломать?**

Хеш `437394baff5aa33daa618be47b75cb49` — это **MD5**. MD5 является криптографически устаревшим алгоритмом по нескольким причинам:

1. **Нет соли (salt)** — один и тот же пароль всегда даёт одинаковый хеш. Это позволяет использовать **радужные таблицы** (rainbow tables) — заранее вычисленные базы данных соответствия хешей и паролей.
2. **MD5 очень быстрый** — современное оборудование проверяет миллиарды MD5-хешей в секунду, что делает брутфорс тривиальным.
3. **Популярные пароли уже взломаны** — существуют онлайн-базы (md5.gromweb.com, crackstation.net и др.), где хранятся миллиарды пар хеш→пароль.

**Метод взлома — reverse lookup:**

Идём на https://md5.gromweb.com, вводим хеш:
```
437394baff5aa33daa618be47b75cb49  →  qwerty123@
```

Пароль найден мгновенно, потому что `qwerty123@` — слабый, популярный пароль, который давно есть в таких базах.

---

### Шаг 4 — Вход в панель администратора

```
URL:      http://localhost:8080/admin/index.php
Username: root
Password: qwerty123@
```

**Почему именно `/admin/index.php`?**

Это типичный путь к административной панели в PHP-приложениях. В реальной атаке его тоже можно обнаружить через `robots.txt`, перебор директорий (directory brute-force), или просто знание стандартных путей.

После входа отображается флаг — задача решена.

---

### Логика атаки — цепочка

```
robots.txt (публичный файл)
    ↓  раскрывает
/whatever/ (скрытая директория)
    ↓  содержит
htpasswd (файл с учётными данными)
    ↓  хранит слабый MD5-хеш
437394baff5aa33daa618be47b75cb49
    ↓  мгновенно взламывается
qwerty123@
    ↓  даёт доступ к
/admin/index.php → FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| `robots.txt` раскрывает чувствительные пути | Никогда не указывай секретные директории в `robots.txt` |
| `htpasswd` лежит в веб-доступной директории | Храни файлы с учётными данными **вне** корня сайта (например, `/etc/apache2/.htpasswd`) |
| Используется MD5 без соли | Переходи на **bcrypt** или **Argon2** — современные алгоритмы хеширования паролей |
| Слабый пароль `qwerty123@` | Используй длинные случайные пароли (менеджер паролей) |

---
---

## 🇬🇧 English Version

### Overview — What Happened

This challenge demonstrates a classic developer mistake: trying to "hide" a directory from search crawlers by listing it in `robots.txt`. But `robots.txt` is a **public file**, accessible to everyone. Instead of concealing the path, it **advertised** it.

---

### Step 1 — Reading `robots.txt`

```bash
curl http://localhost:8080/robots.txt
```

**Why `robots.txt`?**

`robots.txt` is a standard file located at the root of a website. It contains instructions for search engine crawlers (Google, Bing, etc.) about which pages **should not be indexed**. The `Disallow` directive means "don't crawl this path."

The problem: `robots.txt` is **not a security mechanism**. It is a polite request to well-behaved crawlers. Any human (or attacker) can read this file and discover the list of "forbidden" paths — which is itself a reconnaissance goldmine.

**What we found:**
```
User-agent: *
Disallow: /whatever/
```

The `/whatever/` directory immediately became a target — if someone deliberately hid it, there must be something there.

---

### Step 2 — Browsing the Hidden Directory

```bash
curl http://localhost:8080/whatever/
curl http://localhost:8080/whatever/htpasswd
```

**Why did we go there?**

If a developer deliberately hides a directory, it likely contains something sensitive. We accessed it directly and found a file called `htpasswd`.

**What is `htpasswd`?**

It is an Apache web server authentication file. It stores usernames and hashed passwords used to protect directories via HTTP Basic Auth. Storing this file inside a web-accessible directory is a critical security mistake — it should be located **outside** the web root.

**File contents:**
```
root:437394baff5aa33daa618be47b75cb49
```

Format: `username:password_hash`

---

### Step 3 — Cracking the MD5 Hash

**Why is this hash crackable?**

The hash `437394baff5aa33daa618be47b75cb49` is **MD5**. MD5 is cryptographically obsolete for several reasons:

1. **No salt** — the same password always produces the same hash. This enables **rainbow table** attacks — precomputed databases mapping hashes back to plaintext passwords.
2. **MD5 is extremely fast** — modern hardware can compute billions of MD5 hashes per second, making brute-force trivial.
3. **Common passwords are already cracked** — online databases (md5.gromweb.com, crackstation.net, etc.) contain billions of hash→password pairs.

**Attack method — reverse lookup:**

Navigate to https://md5.gromweb.com and submit the hash:
```
437394baff5aa33daa618be47b75cb49  →  qwerty123@
```

The password is recovered instantly because `qwerty123@` is a weak, commonly used password that already exists in these databases.

---

### Step 4 — Logging into the Admin Panel

```
URL:      http://localhost:8080/admin/index.php
Username: root
Password: qwerty123@
```

**Why `/admin/index.php`?**

This is a typical admin panel path in PHP applications. In a real attack, it could also be discovered via `robots.txt`, directory brute-forcing, or knowledge of common conventions.

After logging in, the flag is displayed — challenge complete.

---

### Attack Chain Summary

```
robots.txt (public file)
    ↓  reveals
/whatever/ (hidden directory)
    ↓  contains
htpasswd (credential file)
    ↓  stores weak unsalted MD5 hash
437394baff5aa33daa618be47b75cb49
    ↓  cracked instantly via lookup
qwerty123@
    ↓  grants access to
/admin/index.php → FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| `robots.txt` exposes sensitive paths | Never list secret directories in `robots.txt` |
| `htpasswd` stored in web-accessible directory | Store credential files **outside** the web root (e.g. `/etc/apache2/.htpasswd`) |
| MD5 used without salt | Switch to **bcrypt** or **Argon2** — modern password hashing algorithms |
| Weak password `qwerty123@` | Use long, random passwords (use a password manager) |

---

