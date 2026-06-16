# SQL Injection via UNION

> **Тип уязвимости / Vulnerability Type:** SQL Injection (UNION-based)  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Поле поиска участников на странице `?page=member` передаёт введённый текст напрямую в SQL-запрос без какой-либо обработки. Это позволяет вписать туда не имя пользователя, а фрагмент SQL-кода — и сервер выполнит его как часть настоящего запроса к базе данных. Через технику `UNION SELECT` мы извлекаем данные из любой таблицы в базе, находим хеш пароля, взламываем его и получаем флаг.

---

### Что такое SQL-инъекция

Приложение формирует SQL-запрос примерно так:

```sql
SELECT first_name, last_name FROM users WHERE id = '$input';
```

Если `$input` — это то что ввёл пользователь, и оно вставляется без экранирования, то вместо обычного значения можно вставить SQL-код. Например, если ввести:

```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

Запрос превращается в:

```sql
SELECT first_name, last_name FROM users WHERE id = '1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables';
```

Сервер выполняет его целиком — включая нашу вставку.

**Почему `AND 1=1`?**

Это условие всегда истинно. Оно нужно чтобы первая часть запроса (поиск по `id=1`) отработала корректно и вернула строку — тогда к её результату добавится результат нашего `UNION SELECT`. Без этого запрос мог бы вернуть ноль строк и `UNION` не сработал бы.

---

### Шаг 1 — Получить список всех таблиц

Вводим в поле поиска:
```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

**Что такое `information_schema`?**

Это системная база данных которая есть в каждой MySQL/MariaDB. Она содержит метаданные: список всех баз данных, таблиц, колонок, прав доступа. Это первое место куда смотрят при SQL-инъекции — она даёт карту всей базы данных.

**Что такое `UNION SELECT`?**

`UNION` объединяет результаты двух `SELECT`-запросов в один вывод. Условие: оба запроса должны возвращать одинаковое количество колонок. Оригинальный запрос возвращает две колонки (`first_name`, `last_name`) — поэтому мы тоже пишем `SELECT 1, table_name` (две колонки: константа `1` и имя таблицы).

В ответе увидим список всех таблиц в базе данных. Среди них — таблица `users`.

---

### Шаг 2 — Получить список колонок

Вводим:
```
1 AND 1=1 UNION SELECT table_name, column_name FROM information_schema.columns
```

**Почему этот шаг нужен?**

Мы знаем что есть таблица `users`, но не знаем как называются её колонки. Стандартные колонки (`id`, `username`, `password`) могут называться иначе. Через `information_schema.columns` получаем полный список: таблица → колонка.

Среди результатов находим таблицу `users` с колонками `Commentaire` и `countersign`. Нестандартные названия — именно поэтому без этого шага мы бы не угадали.

---

### Шаг 3 — Вытащить данные из таблицы `users`

Вводим:
```
1 AND 1=1 UNION SELECT Commentaire, countersign FROM users
```

В ответе видим строку:

- `Commentaire` — подсказка (намёк на то что делать с хешем)
- `countersign` — `5ff9d0165b4f92b14994e5c685cdce28`

Это MD5-хеш. Нам нужно его взломать.

---

### Шаг 4 — Взломать MD5-хеш

Идём на любой MD5 reverse lookup (например md5.gromweb.com) и вводим хеш:

```
5ff9d0165b4f92b14994e5c685cdce28  →  FortyTwo
```

**Почему MD5 снова взламывается?**

Та же причина что и в Breach 0: MD5 без соли, популярное слово, уже есть в радужных таблицах. `FortyTwo` — отсылка к «Автостопом по Галактике» (ответ на главный вопрос жизни, вселенной и всего остального).

---

### Шаг 5 — Получить финальный флаг

Подсказка в `Commentaire` говорит привести результат к нижнему регистру и захешировать SHA-256:

```bash
echo -n "fortytwo" | openssl dgst -sha256
```

**Почему `fortytwo` а не `FortyTwo`?**

Потому что подсказка явно указывает: привести к нижнему регистру перед хешированием. `FortyTwo` и `fortytwo` дают разные SHA-256 хеши — регистр важен.

**Почему `-n` у `echo`?**

Без `-n` команда добавляет `\n` в конец строки — и хешируется `"fortytwo\n"` вместо `"fortytwo"`. Результат будет другим.

**Почему SHA-256 а не MD5?**

Это условие задания — подсказка в `Commentaire` указывает именно на SHA-256. В реальной жизни это могло бы быть частью протокола: MD5 для хранения промежуточного пароля, SHA-256 для финального токена.

Результат SHA-256 и есть флаг.

---

### Логика атаки — цепочка

```
Поле поиска уязвимо к SQL-инъекции
    ↓  через UNION SELECT получаем список таблиц из information_schema
Находим таблицу users с колонками Commentaire и countersign
    ↓  через UNION SELECT дампим содержимое таблицы
Получаем MD5-хеш: 5ff9d0165b4f92b14994e5c685cdce28
    ↓  взламываем через reverse lookup
FortyTwo → приводим к нижнему регистру → fortytwo
    ↓  хешируем SHA-256
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Пользовательский ввод вставляется в SQL напрямую | Использовать **prepared statements** (параметризованные запросы) |
| Доступ к `information_schema` | Ограничить права DB-пользователя — только нужные таблицы |
| Нет валидации ввода | Whitelist допустимых значений — например, только цифры для поля `id` |

**Prepared statement на PHP:**
```php
// Уязвимо:
$query = "SELECT first_name, last_name FROM users WHERE id = '$input'";

// Безопасно:
$stmt = $pdo->prepare("SELECT first_name, last_name FROM users WHERE id = ?");
$stmt->execute([$input]);
```

При использовании prepared statements пользовательский ввод никогда не интерпретируется как SQL-код — он передаётся как данные отдельно от запроса.

---
---

## 🇬🇧 English Version

### Overview — What Happened

The member search field on `?page=member` passes user input directly into a SQL query without any sanitization. This allows injecting SQL code instead of a username — and the server will execute it as part of the real database query. Using a `UNION SELECT` technique, we extract data from any table in the database, find a password hash, crack it, and obtain the flag.

---

### What Is SQL Injection

The application builds a SQL query roughly like this:

```sql
SELECT first_name, last_name FROM users WHERE id = '$input';
```

If `$input` is whatever the user typed and is inserted without escaping, we can inject SQL code instead of a normal value. For example, entering:

```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

Turns the query into:

```sql
SELECT first_name, last_name FROM users WHERE id = '1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables';
```

The server executes the entire thing — including our injected portion.

**Why `AND 1=1`?**

This condition is always true. It ensures the first part of the query (searching by `id=1`) returns a row — so our `UNION SELECT` result gets appended to it. Without this, the query might return zero rows and the `UNION` would produce nothing.

---

### Step 1 — Enumerate All Tables

Enter in the search field:
```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

**What is `information_schema`?**

It is a system database present in every MySQL/MariaDB instance. It contains metadata: a list of all databases, tables, columns, and access privileges. This is the first place to look during SQL injection — it provides a complete map of the entire database.

**What is `UNION SELECT`?**

`UNION` combines the results of two `SELECT` queries into a single output. Requirement: both queries must return the same number of columns. The original query returns two columns (`first_name`, `last_name`) — so we write `SELECT 1, table_name` (two columns: the constant `1` and the table name).

The response will contain a list of all tables in the database. Among them — the `users` table.

---

### Step 2 — Enumerate All Columns

Enter:
```
1 AND 1=1 UNION SELECT table_name, column_name FROM information_schema.columns
```

**Why is this step necessary?**

We know the `users` table exists, but we don't know its column names. Standard columns (`id`, `username`, `password`) might be named differently. Through `information_schema.columns` we get the full list: table → column.

Among the results we find the `users` table with columns `Commentaire` and `countersign`. Non-standard names — which is exactly why we couldn't have guessed them without this step.

---

### Step 3 — Dump Data from the `users` Table

Enter:
```
1 AND 1=1 UNION SELECT Commentaire, countersign FROM users
```

The response contains a row with:

- `Commentaire` — a hint (telling us what to do with the hash)
- `countersign` — `5ff9d0165b4f92b14994e5c685cdce28`

This is an MD5 hash. We need to crack it.

---

### Step 4 — Crack the MD5 Hash

Go to any MD5 reverse lookup (e.g. md5.gromweb.com) and submit the hash:

```
5ff9d0165b4f92b14994e5c685cdce28  →  FortyTwo
```

**Why does MD5 crack again?**

Same reason as Breach 0: unsalted MD5, a recognizable word, already present in rainbow tables. `FortyTwo` is a reference to *The Hitchhiker's Guide to the Galaxy* (the answer to the ultimate question of life, the universe, and everything).

---

### Step 5 — Obtain the Final Flag

The hint in `Commentaire` says to convert to lowercase and hash with SHA-256:

```bash
echo -n "fortytwo" | openssl dgst -sha256
```

**Why `fortytwo` and not `FortyTwo`?**

Because the hint explicitly says to convert to lowercase before hashing. `FortyTwo` and `fortytwo` produce different SHA-256 hashes — case matters.

**Why `-n` on `echo`?**

Without `-n`, `echo` appends a newline `\n` to the output — so `"fortytwo\n"` gets hashed instead of `"fortytwo"`. The result would be wrong.

**Why SHA-256 and not MD5?**

The task requires it — the hint in `Commentaire` points specifically to SHA-256. In real life this could be part of a protocol: MD5 for storing an intermediate password, SHA-256 for the final token.

The SHA-256 result is the flag.

---

### Attack Chain Summary

```
Search field is vulnerable to SQL injection
    ↓  UNION SELECT extracts table list from information_schema
We find table users with columns Commentaire and countersign
    ↓  UNION SELECT dumps the table contents
We get MD5 hash: 5ff9d0165b4f92b14994e5c685cdce28
    ↓  crack via reverse lookup
FortyTwo → convert to lowercase → fortytwo
    ↓  hash with SHA-256
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| User input inserted directly into SQL | Use **prepared statements** (parameterized queries) |
| Access to `information_schema` | Restrict DB user privileges — only the required tables |
| No input validation | Whitelist allowed values — e.g. digits only for an `id` field |

**Prepared statement in PHP:**
```php
// Vulnerable:
$query = "SELECT first_name, last_name FROM users WHERE id = '$input'";

// Safe:
$stmt = $pdo->prepare("SELECT first_name, last_name FROM users WHERE id = ?");
$stmt->execute([$input]);
```

With prepared statements, user input is never interpreted as SQL code — it is passed as data separately from the query.

---
