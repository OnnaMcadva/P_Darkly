# Missing Server-Side Validation (Survey Form)

> **Тип уязвимости / Vulnerability Type:** Missing Server-Side Validation  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

На странице опроса есть выпадающий список с оценками от 1 до 10. Ограничение «максимум 10» существует только в HTML — в браузере. Сервер никак не проверяет что пришло значение в допустимом диапазоне. Меняем значение через DevTools или отправляем POST-запрос с числом 100 — сервер принимает и возвращает флаг.

---

### Что такое клиентская и серверная валидация

**Клиентская валидация** — это ограничения которые существуют только в браузере: HTML-атрибуты (`max`, `min`, `maxlength`), элементы `<select>` с фиксированными опциями, JavaScript-проверки. Они удобны для пользователя — дают мгновенную обратную связь без запроса к серверу. Но они не являются защитой, потому что пользователь полностью контролирует свой браузер и может изменить или обойти любое ограничение.

**Серверная валидация** — проверки которые выполняются на сервере, до того как данные обрабатываются или сохраняются. Их нельзя обойти через DevTools или curl — сервер сам решает принять данные или отклонить.

**Золотое правило:** клиентская валидация — для удобства. Серверная валидация — для безопасности. Одно без другого не работает.

---

### Шаг 1 — Найти форму опроса

Открываем в браузере:
```
http://localhost:8080/?page=survey
```

Видим форму с выпадающим списком оценок от 1 до 10. В HTML это выглядит примерно так:

```html
<select name="valeur">
  <option value="1">1</option>
  <option value="2">2</option>
  ...
  <option value="10">10</option>
</select>
```

**Почему форма с `<select>` сразу подозрительна?**

`<select>` ограничивает пользователя фиксированным набором значений — но только визуально. В DevTools любой `<option>` можно отредактировать, добавить новый, или вовсе отправить POST-запрос минуя форму. Если разработчик думает что `<select>` является защитой — это ошибка.

---

### Вариант А — Изменить значение через DevTools

1. Нажимаем **F12** → вкладка **Elements**
2. Находим тег `<option>` с максимальным значением:
```html
<option value="10">10</option>
```
3. Дважды кликаем на `value="10"` и меняем на `value="100"`:
```html
<option value="100">10</option>
```
4. Выбираем эту опцию в выпадающем списке и нажимаем Submit

**Что происходит технически?**

Мы изменили значение атрибута `value` прямо в DOM браузера. Текст опции (`10`) остался прежним — пользователь видит `10`. Но когда форма отправляется, браузер берёт именно атрибут `value` — и отправляет `100`. Сервер получает `valeur=100` и не проверяет допустим ли этот диапазон.

---

### Вариант Б — Отправить запрос напрямую через curl

```bash
curl -X POST "http://127.0.0.1:8080/?page=survey" \
     --data "sujet=2&valeur=100" \
     | grep -i flag
```

**Разбор команды:**

| Часть | Что делает |
|-------|-----------|
| `curl -X POST` | Отправляет POST-запрос как при нажатии Submit |
| `"http://...?page=survey"` | URL страницы с формой |
| `--data "sujet=2&valeur=100"` | Тело запроса: номер вопроса и значение оценки |
| `\| grep -i flag` | Ищем флаг в ответе |

**Почему curl вообще работает?**

Потому что браузер и curl делают одно и то же — отправляют HTTP POST-запрос с данными формы. Браузер добавляет интерфейс и ограничения — но сам запрос это просто текст. curl отправляет тот же текст напрямую, без всяких ограничений браузера.

**Зачем два варианта?**

Вариант А (DevTools) — нагляднее, виден в браузере. Вариант Б (curl) — быстрее, не нужно искать элемент в DOM. В реальном пентесте чаще используют curl или специальные инструменты (Burp Suite) чтобы перехватывать и изменять запросы на лету.

---

### Логика атаки — цепочка

```
Форма опроса ограничивает значения от 1 до 10 через <select>
    ↓  ограничение существует только в HTML браузера
Меняем value="10" на value="100" в DevTools
    ИЛИ отправляем POST напрямую с valeur=100 через curl
    ↓  сервер получает значение вне диапазона
Сервер не проверяет диапазон → возвращает флаг
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Валидация только на клиенте через `<select>` | Проверять диапазон значений на сервере до обработки |
| Сервер принимает любое число | Явно ограничить: `if ($value < 1 || $value > 10) { reject; }` |
| Доверие к клиентским данным | Все данные от клиента считать недоверенными по умолчанию |

**Пример серверной проверки на PHP:**
```php
$value = intval($_POST['valeur']);

if ($value < 1 || $value > 10) {
    die('Invalid value');
}

// только теперь обрабатываем
```

---
---

## 🇬🇧 English Version

### Overview — What Happened

The survey page has a dropdown with ratings from 1 to 10. The "maximum 10" restriction exists only in HTML — in the browser. The server never checks that the received value is within the allowed range. We change the value via DevTools or send a POST request with the number 100 — the server accepts it and returns the flag.

---

### What Is Client-Side vs Server-Side Validation

**Client-side validation** — restrictions that exist only in the browser: HTML attributes (`max`, `min`, `maxlength`), `<select>` elements with fixed options, JavaScript checks. They are convenient for the user — providing instant feedback without a server round-trip. But they are not a security measure, because the user has full control over their browser and can modify or bypass any restriction.

**Server-side validation** — checks that run on the server, before data is processed or stored. They cannot be bypassed via DevTools or curl — the server itself decides whether to accept or reject the data.

**Golden rule:** client-side validation is for convenience. Server-side validation is for security. One without the other doesn't work.

---

### Step 1 — Find the Survey Form

Open in browser:
```
http://localhost:8080/?page=survey
```

We see a form with a dropdown of ratings from 1 to 10. In HTML it looks roughly like this:

```html
<select name="valeur">
  <option value="1">1</option>
  <option value="2">2</option>
  ...
  <option value="10">10</option>
</select>
```

**Why is a `<select>` form immediately suspicious?**

`<select>` restricts the user to a fixed set of values — but only visually. In DevTools any `<option>` can be edited, a new one can be added, or a POST request can be sent bypassing the form entirely. If the developer thinks `<select>` is a security measure — that is a mistake.

---

### Option A — Modify the Value via DevTools

1. Press **F12** → **Elements** tab
2. Find the `<option>` tag with the maximum value:
```html
<option value="10">10</option>
```
3. Double-click on `value="10"` and change it to `value="100"`:
```html
<option value="100">10</option>
```
4. Select that option in the dropdown and click Submit

**What happens technically?**

We changed the `value` attribute directly in the browser's DOM. The option text (`10`) stays the same — the user sees `10`. But when the form is submitted, the browser takes the `value` attribute — and sends `100`. The server receives `valeur=100` and never checks whether that range is valid.

---

### Option B — Send the Request Directly via curl

```bash
curl -X POST "http://127.0.0.1:8080/?page=survey" \
     --data "sujet=2&valeur=100" \
     | grep -i flag
```

**Command breakdown:**

| Part | What it does |
|------|-------------|
| `curl -X POST` | Sends a POST request as if clicking Submit |
| `"http://...?page=survey"` | URL of the form page |
| `--data "sujet=2&valeur=100"` | Request body: question number and rating value |
| `\| grep -i flag` | Searches for the flag in the response |

**Why does curl work at all?**

Because the browser and curl do the same thing — they send an HTTP POST request with form data. The browser adds an interface and restrictions — but the request itself is just text. curl sends the same text directly, without any browser restrictions.

**Why two options?**

Option A (DevTools) — more visual, everything happens in the browser. Option B (curl) — faster, no need to locate the element in the DOM. In real penetration testing, curl or dedicated tools like Burp Suite are commonly used to intercept and modify requests on the fly.

---

### Attack Chain Summary

```
Survey form restricts values 1–10 via <select>
    ↓  restriction exists only in the browser's HTML
We change value="10" to value="100" in DevTools
    OR send POST directly with valeur=100 via curl
    ↓  server receives a value outside the allowed range
Server does not validate the range → returns the flag
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| Validation only on the client via `<select>` | Validate the value range on the server before processing |
| Server accepts any number | Explicitly restrict: `if ($value < 1 || $value > 10) { reject; }` |
| Trust in client-supplied data | Treat all data from the client as untrusted by default |

**Example server-side check in PHP:**
```php
$value = intval($_POST['valeur']);

if ($value < 1 || $value > 10) {
    die('Invalid value');
}

// only now process the data
```

---
