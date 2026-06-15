# Header Spoofing + Hidden Page in HTML Comment

> **Тип уязвимости / Vulnerability Type:** Information Disclosure via HTML Comments + HTTP Header Forgery  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Здесь две уязвимости работают вместе. Первая: разработчик спрятал секретную ссылку прямо в HTML-коде страницы в виде комментария — любой кто смотрит исходник её видит. Вторая: страница по этой ссылке «защищена» проверкой заголовков `Referer` и `User-Agent` — но эти заголовки клиент может поставить любые. Никакой реальной защиты нет.

---

### Шаг 1 — Найти скрытую ссылку в исходнике

Открываем исходный код главной страницы:

```bash
curl -s http://localhost:8080/ | grep -i "<!--"
```

Либо в браузере: `Ctrl+U` → ищем HTML-комментарий вида:

```html
<!-- Leeeets go !
You must cumming from : "https://www.nsa.gov/"
with the user agent : "ft_bornToSec"
These are not the droids you're looking for ;) -->
```

И где-то рядом — ссылка на скрытую страницу:

```
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
```

**Почему мы смотрим исходник?**

HTML-комментарии (`<!-- ... -->`) не отображаются на странице в браузере, но они есть в коде и видны всем. Это классическая ошибка: разработчики оставляют в комментариях заметки для себя — пути, подсказки, TODO — и забывают что это публично. Исходник страницы — первое место куда смотрит любой пентестер.

**Что такое этот длинный хеш в URL?**

`b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f` — выглядит как SHA-256. Это попытка сделать URL «непредсказуемым» — security through obscurity. Проблема в том, что ссылка всё равно лежит в исходнике открытым текстом.

---

### Шаг 2 — Понять защиту скрытой страницы

Комментарий прямо говорит нам условия доступа:

- Заголовок `Referer` должен быть `https://www.nsa.gov/`
- Заголовок `User-Agent` должен быть `ft_bornToSec`

**Что такое `Referer`?**

`Referer` — HTTP-заголовок который браузер автоматически отправляет, указывая с какой страницы пришёл пользователь. Например, если ты кликнула ссылку на google.com, браузер отправит `Referer: https://www.google.com/`. Сервер использует это чтобы понять откуда пришёл запрос.

**Что такое `User-Agent`?**

`User-Agent` — заголовок который идентифицирует клиент: браузер, его версию, операционную систему. Например: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...`. Сервер использует его чтобы понять с какого устройства/браузера пришёл запрос.

**Почему это не защита?**

Оба заголовка полностью контролируются клиентом. Браузер отправляет их автоматически, но любой HTTP-клиент (curl, Postman, Python requests) позволяет поставить туда что угодно. Сервер не может проверить правду ли говорит клиент — он просто читает что написано в заголовке.

---

### Шаг 3 — Отправить запрос с поддельными заголовками

```bash
curl -s \
  -H "Referer: https://www.nsa.gov/" \
  -H "User-Agent: ft_bornToSec" \
  "http://localhost:8080/?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f" \
  | grep -i flag
```

**Разбор команды:**

| Часть | Что делает |
|-------|-----------|
| `curl -s` | Запрос без лишнего вывода (`-s` = silent) |
| `-H "Referer: ..."` | Добавляет заголовок Referer с нужным значением |
| `-H "User-Agent: ..."` | Подменяет User-Agent на `ft_bornToSec` |
| `"http://...?page=..."` | URL скрытой страницы из комментария |
| `\| grep -i flag` | Фильтрует вывод — ищем только строку с флагом |

Сервер получает запрос, видит нужные заголовки, считает что всё легитимно — и отдаёт флаг.

---

### Логика атаки — цепочка

```
Исходник страницы содержит HTML-комментарий
    ↓  в комментарии — URL скрытой страницы и условия доступа
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
    ↓  страница проверяет Referer и User-Agent
Подделываем оба заголовка через curl -H
    ↓  сервер принимает поддельные заголовки как настоящие
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Секретный URL в HTML-комментарии | Никогда не оставлять чувствительные данные в комментариях — они публичны |
| Проверка `Referer` как защита | `Referer` клиент-контролируемый заголовок — не использовать для авторизации |
| Проверка `User-Agent` как защита | `User-Agent` тоже клиент-контролируемый — не использовать для авторизации |
| Security through obscurity (длинный хеш в URL) | Непредсказуемый URL не заменяет настоящую аутентификацию |

**Правило:** HTTP-заголовки которые клиент может выставить сам — не являются доказательством его личности или происхождения запроса.

---
---

## 🇬🇧 English Version

### Overview — What Happened

Two vulnerabilities work together here. First: the developer hid a secret link directly in the HTML source as a comment — anyone who views the source sees it immediately. Second: the page at that link is "protected" by checking the `Referer` and `User-Agent` headers — but these headers are fully client-controlled, so the protection is meaningless.

---

### Step 1 — Find the Hidden Link in the Page Source

Fetch the page source and look for HTML comments:

```bash
curl -s http://localhost:8080/ | grep -i "<!--"
```

Or in browser: `Ctrl+U` → search for an HTML comment like:

```html
<!-- Leeeets go !
You must cumming from : "https://www.nsa.gov/"
with the user agent : "ft_bornToSec"
These are not the droids you're looking for ;) -->
```

And nearby — a link to the hidden page:

```
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
```

**Why look at the page source?**

HTML comments (`<!-- ... -->`) are invisible in the rendered browser view, but they are present in the raw code and visible to everyone. Developers often leave notes, paths, and hints in comments and forget they are public. The page source is the first place any penetration tester looks.

**What is the long hash in the URL?**

`b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f` looks like SHA-256. It is an attempt to make the URL "unpredictable" — security through obscurity. The problem: the link is still sitting in the source code in plain text.

---

### Step 2 — Understand the Hidden Page's Protection

The comment tells us exactly what is required for access:

- Header `Referer` must be `https://www.nsa.gov/`
- Header `User-Agent` must be `ft_bornToSec`

**What is `Referer`?**

`Referer` is an HTTP header that the browser sends automatically to indicate which page the user came from. For example, clicking a link on google.com causes the browser to send `Referer: https://www.google.com/`. Servers use it to understand the origin of a request.

**What is `User-Agent`?**

`User-Agent` is a header that identifies the client: browser name, version, operating system. Example: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...`. Servers use it to understand what device or browser made the request.

**Why is this not a real protection?**

Both headers are entirely client-controlled. The browser sends them automatically, but any HTTP client (curl, Postman, Python requests) lets you set them to anything you want. The server has no way to verify whether the client is telling the truth — it simply reads whatever is written in the header.

---

### Step 3 — Send the Request with Spoofed Headers

```bash
curl -s \
  -H "Referer: https://www.nsa.gov/" \
  -H "User-Agent: ft_bornToSec" \
  "http://localhost:8080/?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f" \
  | grep -i flag
```

**Command breakdown:**

| Part | What it does |
|------|-------------|
| `curl -s` | Silent mode — no progress output |
| `-H "Referer: ..."` | Adds the Referer header with the required value |
| `-H "User-Agent: ..."` | Overrides User-Agent with `ft_bornToSec` |
| `"http://...?page=..."` | The hidden page URL from the comment |
| `\| grep -i flag` | Filters output — shows only the line containing the flag |

The server receives the request, sees the expected headers, considers the request legitimate — and returns the flag.

---

### Attack Chain Summary

```
Page source contains an HTML comment
    ↓  comment reveals hidden page URL and access conditions
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
    ↓  page checks Referer and User-Agent headers
We forge both headers via curl -H
    ↓  server accepts the forged headers as legitimate
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| Secret URL in an HTML comment | Never put sensitive data in comments — they are public |
| `Referer` check used as access control | `Referer` is client-controlled — never use for authorization |
| `User-Agent` check used as access control | `User-Agent` is also client-controlled — never use for authorization |
| Security through obscurity (long hash URL) | An unpredictable URL is not a substitute for real authentication |

**Rule:** HTTP headers that the client can set themselves are not proof of the client's identity or the origin of a request.

---
