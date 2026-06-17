# SQL Injection via UNION (Image Search)

> **Тип уязвимости / Vulnerability Type:** SQL Injection (UNION-based)  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Это та же уязвимость что и SQL-инъекция через `UNION SELECT` — но на другой странице и в другой таблице. Поле поиска изображений на `?page=searchimg` так же уязвимо: пользовательский ввод вставляется в SQL-запрос напрямую. В базе есть отдельная таблица `list_images` с закодированными данными в колонке `comment`. Техника та же, цель другая.

---

### Почему мы идём на `?page=searchimg`

Мы знаем что делать с SQL-инъекцией. Естественный следующий шаг — проверить другие поля ввода на том же сайте. Каждая форма, каждое поле поиска, каждый параметр в URL — потенциальная точка входа.

`?page=searchimg` — отдельная страница поиска по изображениям. У неё своя форма, свой SQL-запрос на бэкенде — и, как выясняется, та же уязвимость. Разработчик защитил (или не защитил) каждый endpoint независимо, и этот тоже остался без защиты.

**Важный принцип:** одна уязвимость в одном месте не означает что другие места защищены. Нужно проверять каждый endpoint отдельно.

---

### Шаг 1 — Получить список всех таблиц

Вводим в поле поиска изображений:
```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

Логика та же что в Breach 8: `UNION SELECT` добавляет наш запрос к оригинальному, `information_schema.tables` даёт список всех таблиц в базе.

Среди результатов видим таблицу `list_images` — она не была видна раньше потому что мы смотрели на неё через контекст поиска участников. Сейчас мы в другом контексте — и находим другую таблицу.

---

### Шаг 2 — Получить список колонок

Вводим:
```
1 AND 1=1 UNION SELECT table_name, column_name FROM information_schema.columns
```

Находим таблицу `list_images` с колонками `title` и `comment`.

**Почему колонки называются не `id`, `url`, `description`?**

Разработчик выбрал нестандартные имена. Именно поэтому мы не пропускаем шаг энумерации колонок даже когда знаем имя таблицы — без него мы бы не знали что запрашивать.

---

### Шаг 3 — Вытащить данные из `list_images`

Вводим:
```
1 AND 1=1 UNION SELECT title, comment FROM list_images
```

В ответе видим строку:

- `title` — подсказка что делать с хешем
- `comment` — `1928e8083cf461a51303633093573c46`

Это MD5-хеш.

**Чем этот дамп отличается от Breach 8?**

В Breach 8 мы дампили таблицу `users` с колонками `Commentaire` и `countersign`. Здесь — таблица `list_images` с колонками `title` и `comment`. Разные таблицы, разные колонки, одна техника. Именно поэтому шаг энумерации (шаги 1 и 2) нельзя пропускать — структура базы каждый раз разная.

---

### Шаг 4 — Взломать MD5-хеш

Идём на любой MD5 reverse lookup (например md5.gromweb.com):

```
1928e8083cf461a51303633093573c46  →  albatroz
```

`albatroz` — альбатрос по-португальски. Слово достаточно специфичное, но оно есть в словарях и радужных таблицах — MD5 без соли взламывается.

---

### Шаг 5 — Получить финальный флаг

Подсказка в `title` говорит хешировать результат через SHA-256 в нижнем регистре:

```bash
echo -n "albatroz" | openssl dgst -sha256
```

`albatroz` уже в нижнем регистре — дополнительных преобразований не нужно. Результат SHA-256 — это флаг.

**Почему снова SHA-256?**

Это паттерн задания: MD5-хеш в базе → взломать → SHA-256 результата = флаг. Такой же паттерн был в Breach 8. Разработчики Darkly намеренно сделали похожую структуру чтобы закрепить технику.

---

### Чем этот breach отличается от Breach 8

| | Breach 8 | Breach 9 |
|--|----------|----------|
| Страница | `?page=member` | `?page=searchimg` |
| Целевая таблица | `users` | `list_images` |
| Колонки с данными | `Commentaire`, `countersign` | `title`, `comment` |
| MD5 результат | `FortyTwo` | `albatroz` |
| Финальный шаг | `echo -n "fortytwo"` | `echo -n "albatroz"` |
| Техника | UNION SELECT | UNION SELECT |

Техника идентична — меняются только точка входа и целевые данные. Это демонстрирует что одна уязвимая архитектура (конкатенация SQL) делает уязвимыми все endpoints которые её используют.

---

### Логика атаки — цепочка

```
?page=searchimg содержит поле поиска уязвимое к SQL-инъекции
    ↓  UNION SELECT получаем список таблиц из information_schema
Находим таблицу list_images с колонками title и comment
    ↓  UNION SELECT дампим содержимое таблицы
Получаем MD5-хеш: 1928e8083cf461a51303633093573c46
    ↓  взламываем через reverse lookup
albatroz → хешируем SHA-256
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Пользовательский ввод вставляется в SQL напрямую | Использовать **prepared statements** на всех endpoints без исключения |
| Разные endpoints с одинаковой уязвимостью | Единый стандарт безопасности для всех форм — не проверять каждый по отдельности |
| Доступ к `information_schema` | Ограничить права DB-пользователя только необходимыми таблицами |

**Ключевой вывод:** если в кодовой базе есть одно место с конкатенацией SQL — скорее всего таких мест несколько. Исправлять нужно архитектурно — переходить на prepared statements везде, а не латать по одному endpoint.

---
---

## 🇬🇧 English Version

### Overview — What Happened

This is the same vulnerability as Breach 8 — SQL injection via `UNION SELECT` — but on a different page and targeting a different table. The image search field on `?page=searchimg` is equally vulnerable: user input is inserted directly into a SQL query. The database contains a separate `list_images` table with encoded data in the `comment` column. Same technique, different target.

---

### Why We Go to `?page=searchimg`

After Breach 8 we know what to do with SQL injection. The natural next step is to check other input fields on the same site. Every form, every search field, every URL parameter is a potential entry point.

`?page=searchimg` is a separate image search page. It has its own form, its own backend SQL query — and, as it turns out, the same vulnerability. The developer protected (or failed to protect) each endpoint independently, and this one was left unprotected too.

**Key principle:** one vulnerability in one place does not mean other places are secure. Every endpoint must be tested independently.

---

### Step 1 — Enumerate All Tables

Enter in the image search field:
```
1 AND 1=1 UNION SELECT 1, table_name FROM information_schema.tables
```

Same logic as Breach 8: `UNION SELECT` appends our query to the original one, `information_schema.tables` gives us the list of all tables in the database.

Among the results we see the `list_images` table — it was there before too, but now we're approaching from a different context and focusing on a different target.

---

### Step 2 — Enumerate Columns

Enter:
```
1 AND 1=1 UNION SELECT table_name, column_name FROM information_schema.columns
```

We find the `list_images` table with columns `title` and `comment`.

**Why aren't the columns named `id`, `url`, `description`?**

The developer chose non-standard names. This is exactly why we never skip the column enumeration step even when we already know the table name — without it we wouldn't know what to query.

---

### Step 3 — Dump Data from `list_images`

Enter:
```
1 AND 1=1 UNION SELECT title, comment FROM list_images
```

The response contains a row with:

- `title` — a hint about what to do with the hash
- `comment` — `1928e8083cf461a51303633093573c46`

This is an MD5 hash.

**How does this dump differ from Breach 8?**

In Breach 8 we dumped the `users` table with columns `Commentaire` and `countersign`. Here — the `list_images` table with columns `title` and `comment`. Different tables, different columns, same technique. This is exactly why the enumeration steps (steps 1 and 2) cannot be skipped — the database structure is different every time.

---

### Step 4 — Crack the MD5 Hash

Go to any MD5 reverse lookup (e.g. md5.gromweb.com):

```
1928e8083cf461a51303633093573c46  →  albatroz
```

`albatroz` is Portuguese for albatross. Specific enough to seem obscure, but it exists in dictionaries and rainbow tables — unsalted MD5 cracks.

---

### Step 5 — Obtain the Final Flag

The hint in `title` says to hash the result with SHA-256 in lowercase:

```bash
echo -n "albatroz" | openssl dgst -sha256
```

`albatroz` is already lowercase — no additional transformation needed. The SHA-256 result is the flag.

**Why SHA-256 again?**

This is the challenge's pattern: MD5 hash in the database → crack it → SHA-256 of the result = flag. The same pattern appeared in Breach 8. The Darkly developers intentionally used a similar structure to reinforce the technique.

---

### How This Breach Differs from Breach 8

| | Breach 8 | Breach 9 |
|--|----------|----------|
| Page | `?page=member` | `?page=searchimg` |
| Target table | `users` | `list_images` |
| Data columns | `Commentaire`, `countersign` | `title`, `comment` |
| MD5 result | `FortyTwo` | `albatroz` |
| Final step | `echo -n "fortytwo"` | `echo -n "albatroz"` |
| Technique | UNION SELECT | UNION SELECT |

The technique is identical — only the entry point and target data differ. This demonstrates that one vulnerable architecture (SQL concatenation) makes every endpoint that uses it equally vulnerable.

---

### Attack Chain Summary

```
?page=searchimg contains a search field vulnerable to SQL injection
    ↓  UNION SELECT retrieves table list from information_schema
We find table list_images with columns title and comment
    ↓  UNION SELECT dumps the table contents
We get MD5 hash: 1928e8083cf461a51303633093573c46
    ↓  crack via reverse lookup
albatroz → hash with SHA-256
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| User input inserted directly into SQL | Use **prepared statements** on every endpoint without exception |
| Multiple endpoints sharing the same vulnerability | Enforce a single security standard for all forms — don't audit each one separately |
| Access to `information_schema` | Restrict DB user privileges to only the required tables |

**Key takeaway:** if a codebase has one place with SQL concatenation — there are likely more. The fix must be architectural — switch to prepared statements everywhere, not patch one endpoint at a time.

---
