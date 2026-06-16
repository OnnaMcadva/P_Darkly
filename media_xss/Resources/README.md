# XSS via `data:` URI

> **Тип уязвимости / Vulnerability Type:** Cross-Site Scripting (XSS) via `data:` URI  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Страница `?page=media` принимает параметр `src` и подставляет его напрямую в тег `<object>` или `<iframe>` без какой-либо проверки. Мы передаём туда не ссылку на видео, а `data:` URI с HTML-кодом закодированным в base64. Браузер декодирует его и выполняет как настоящую HTML-страницу — включая `<script>`. Флаг появляется после выполнения скрипта.

---

### Шаг 1 — Найти страницу media и параметр `src`

```bash
curl -s "http://127.0.0.1:8080" | grep "page="
```

В исходнике главной страницы находим ссылку:
```
?page=media&src=nsa
```

**Почему мы ищем `page=` в исходнике?**

Это разведка — смотрим какие страницы существуют на сайте. `grep "page="` фильтрует все ссылки которые используют параметр `page`. Так находим скрытые или неочевидные страницы.

**Почему `src=nsa` сразу интересен?**

Параметр `src` обычно означает источник — URL картинки, видео, фрейма. Если сервер принимает `src` от пользователя и подставляет его в тег — значит мы контролируем что будет загружено. `nsa` — это, вероятно, имя файла на сервере. Вопрос: а что будет если передать туда не `nsa`, а что-то другое?

---

### Шаг 2 — Что такое `data:` URI

Обычный `src` указывает на внешний ресурс:
```html
<iframe src="https://example.com/video.mp4"></iframe>
```

`data:` URI — это другое. Он позволяет встроить сами данные прямо в URL, без обращения к внешнему серверу:

```
data:[тип];[кодировка],[данные]
```

Например:
```
data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

Браузер читает это как: «загрузи HTML-страницу, данные которой закодированы в base64 и находятся прямо здесь». Декодирует, рендерит как HTML — и выполняет всё что там написано, включая JavaScript.

**Почему base64?**

Некоторые символы (`<`, `>`, `"`, пробелы) не могут напрямую стоять в URL — они будут неправильно интерпретированы. Base64 кодирует любые данные в безопасный набор символов (`A-Z`, `a-z`, `0-9`, `+`, `/`, `=`) который корректно передаётся в URL.

---

### Шаг 3 — Закодировать payload в base64

```bash
echo -n '<script>alert("42")</script>' | base64
# PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

**Что такое payload?**

Payload — это полезная нагрузка атаки, код который мы хотим выполнить. В данном случае `<script>alert("42")</script>` — простейший JavaScript который показывает всплывающее окно. В реальной XSS-атаке здесь мог бы быть код для кражи cookies, перенаправления на фишинговый сайт, или кейлоггер.

**Почему `alert("42")`?**

`alert()` — стандартный способ доказать что JavaScript выполнился. Если появилось окно — инъекция сработала. Число `42` — традиционная отсылка («ответ на главный вопрос жизни, вселенной и всего остального»), часто используется в CTF-заданиях.

**Почему `-n` у `echo`?**

Без `-n` добавляется `\n` в конец — и base64 получается другим. Флаг `-n` убирает этот символ.

---

### Шаг 4 — Выполнить инъекцию

Открываем в браузере:
```
http://127.0.0.1:8080/?page=media&src=data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

**Что происходит на сервере?**

Сервер берёт значение `src` и вставляет его примерно так:
```html
<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg=="></object>
```

или:
```html
<iframe src="data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg=="></iframe>
```

**Что происходит в браузере?**

Браузер видит `data:text/html;base64,...` и думает: «это встроенная HTML-страница». Декодирует base64, получает `<script>alert("42")</script>`, рендерит как HTML — скрипт выполняется. Появляется всплывающее окно, и вместе с ним — флаг.

---

### Что такое XSS и чем это опасно в реальной жизни

**XSS (Cross-Site Scripting)** — это уязвимость при которой атакующий может выполнить произвольный JavaScript в браузере другого пользователя в контексте атакуемого сайта.

В данном случае это **Self-XSS** — скрипт выполняется только у того кто открыл ссылку. Но если бы эта ссылка была отправлена жертве:

```
Привет! Посмотри это видео: http://bank.com/?page=media&src=data:text/html;base64,...
```

Жертва открывает ссылку на настоящий `bank.com` — и наш скрипт выполняется в контексте этого банка. Что можно сделать:

- **Украсть cookies сессии** → войти в аккаунт жертвы
- **Перехватить вводимые данные** → кейлоггер для паролей и номеров карт
- **Перенаправить на фишинговый сайт** → поддельная страница входа
- **Выполнить действия от имени жертвы** → перевод денег, смена email

---

### Логика атаки — цепочка

```
?page=media&src= принимает произвольный src без проверки
    ↓  находим параметр через grep исходника главной страницы
Кодируем <script>alert("42")</script> в base64
    ↓  формируем data: URI с нашим payload
Передаём в src= вместо ссылки на файл
    ↓  сервер вставляет в <object> или <iframe> без валидации
Браузер декодирует base64 и выполняет HTML/JavaScript
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| `src` принимает произвольные значения | Whitelist разрешённых значений — только `nsa`, `bbc`, и т.д. |
| `data:` URI не блокируется | Явно запретить схему `data:` для встроенного контента |
| Нет CSP-заголовка | Добавить `Content-Security-Policy: default-src 'self'` — запрещает inline-скрипты и `data:` URI |
| Пользовательский ввод в атрибут тега | Экранировать все специальные символы перед вставкой в HTML |

**Content-Security-Policy** — самый мощный инструмент против XSS. Заголовок говорит браузеру откуда разрешено загружать скрипты, стили, медиа. Если `data:` URI не в whitelist — браузер откажется его выполнять даже если он попал в HTML.

---
---

## 🇬🇧 English Version

### Overview — What Happened

The `?page=media` page accepts a `src` parameter and inserts it directly into an `<object>` or `<iframe>` tag without any validation. We pass not a video link, but a `data:` URI containing HTML encoded in base64. The browser decodes it and renders it as a real HTML page — including executing `<script>`. The flag appears after the script runs.

---

### Step 1 — Discover the Media Page and the `src` Parameter

```bash
curl -s "http://127.0.0.1:8080" | grep "page="
```

In the main page source we find a link:
```
?page=media&src=nsa
```

**Why search for `page=` in the source?**

This is reconnaissance — we look at what pages exist on the site. `grep "page="` filters all links that use the `page` parameter. This reveals hidden or non-obvious pages.

**Why is `src=nsa` immediately interesting?**

The `src` parameter usually means a source — a URL for an image, video, or frame. If the server accepts `src` from the user and inserts it into a tag — we control what gets loaded. `nsa` is probably a filename on the server. The question is: what happens if we pass something else instead of `nsa`?

---

### Step 2 — What Is a `data:` URI

A normal `src` points to an external resource:
```html
<iframe src="https://example.com/video.mp4"></iframe>
```

A `data:` URI is different. It allows embedding the actual data directly in the URL, without fetching from an external server:

```
data:[type];[encoding],[data]
```

For example:
```
data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

The browser reads this as: "load an HTML page whose content is base64-encoded and provided right here." It decodes it, renders it as HTML — and executes everything inside, including JavaScript.

**Why base64?**

Some characters (`<`, `>`, `"`, spaces) cannot appear directly in a URL — they would be misinterpreted. Base64 encodes any data into a safe character set (`A-Z`, `a-z`, `0-9`, `+`, `/`, `=`) that passes correctly through URLs.

---

### Step 3 — Encode the Payload in Base64

```bash
echo -n '<script>alert("42")</script>' | base64
# PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

**What is a payload?**

A payload is the attack's active content — the code we want to execute. In this case `<script>alert("42")</script>` is a simple JavaScript that shows a popup. In a real XSS attack this could be code to steal cookies, redirect to a phishing site, or run a keylogger.

**Why `alert("42")`?**

`alert()` is the standard way to prove JavaScript executed. If the popup appears — the injection worked. The number `42` is a traditional reference ("the answer to the ultimate question of life, the universe, and everything"), commonly used in CTF challenges.

**Why `-n` on `echo`?**

Without `-n`, a newline `\n` is appended — and the base64 output differs. The `-n` flag suppresses that character.

---

### Step 4 — Execute the Injection

Open in browser:
```
http://127.0.0.1:8080/?page=media&src=data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg==
```

**What happens on the server?**

The server takes the `src` value and inserts it roughly like this:
```html
<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg=="></object>
```

or:
```html
<iframe src="data:text/html;base64,PHNjcmlwdD5hbGVydCgiNDIiKTwvc2NyaXB0Pg=="></iframe>
```

**What happens in the browser?**

The browser sees `data:text/html;base64,...` and thinks: "this is an embedded HTML page." It decodes the base64, gets `<script>alert("42")</script>`, renders it as HTML — the script executes. A popup appears, and along with it — the flag.

---

### What Is XSS and Why It's Dangerous in Real Life

**XSS (Cross-Site Scripting)** is a vulnerability where an attacker can execute arbitrary JavaScript in another user's browser in the context of the targeted site.

In this case it is **Self-XSS** — the script only runs for whoever opens the link. But if this link were sent to a victim:

```
Hey! Check out this video: http://bank.com/?page=media&src=data:text/html;base64,...
```

The victim opens a link to a real `bank.com` — and our script runs in that bank's context. What's possible:

- **Steal session cookies** → log into the victim's account
- **Intercept typed data** → keylogger for passwords and card numbers
- **Redirect to a phishing site** → fake login page
- **Perform actions as the victim** → transfer money, change email

---

### Attack Chain Summary

```
?page=media&src= accepts arbitrary src without validation
    ↓  we find the parameter via grep on the main page source
We encode <script>alert("42")</script> in base64
    ↓  we build a data: URI with our payload
We pass it in src= instead of a file link
    ↓  server inserts it into <object> or <iframe> without validation
Browser decodes base64 and executes the HTML/JavaScript
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| `src` accepts arbitrary values | Whitelist allowed values — only `nsa`, `bbc`, etc. |
| `data:` URI is not blocked | Explicitly forbid the `data:` scheme for embedded content |
| No CSP header | Add `Content-Security-Policy: default-src 'self'` — blocks inline scripts and `data:` URIs |
| User input inserted into HTML attribute | Escape all special characters before inserting into HTML |

**Content-Security-Policy** is the most powerful tool against XSS. The header tells the browser which sources are allowed for scripts, styles, and media. If `data:` URI is not in the whitelist — the browser will refuse to execute it even if it ends up in the HTML.

---
