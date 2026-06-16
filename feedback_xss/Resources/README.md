# Stored / Reflected XSS via Feedback Form

> **Тип уязвимости / Vulnerability Type:** Stored / Reflected Cross-Site Scripting (XSS)  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Форма обратной связи ограничивает длину сообщения через атрибут `maxlength="50"` на HTML-элементе `<textarea>`. Это ограничение существует только в браузере — сервер принимает текст любой длины и не экранирует его перед отображением. Убираем ограничение через DevTools, вставляем HTML-тег с JavaScript — сервер сохраняет его как есть и браузер выполняет скрипт.

---

### Чем этот XSS отличается от Breach 11

В Breach 11 мы делали **Reflected XSS** через URL-параметр: вредоносный код передавался в URL и сразу выполнялся только у того кто открыл ссылку.

Здесь потенциально **Stored XSS** (хранимый): вредоносный код отправляется через форму, сохраняется на сервере, и выполняется у каждого кто открывает страницу с отзывами. Это значительно опаснее — атака срабатывает автоматически для всех пользователей без необходимости отправлять им специальную ссылку.

| | Reflected XSS | Stored XSS |
|--|--------------|------------|
| Где хранится payload | В URL | В базе данных / на сервере |
| Кто пострадает | Тот кто открыл ссылку | Все кто открывает страницу |
| Нужна ли ссылка жертве | Да | Нет |
| Опасность | Средняя | Высокая |

---

### Шаг 1 — Найти форму обратной связи

Открываем в браузере:
```
http://localhost:8080/index.php?page=feedback
```

Видим форму с полями Name и Message. В HTML поле сообщения выглядит так:

```html
<textarea name="mtxtMessage" id="mtxtMessage" maxlength="50" ...></textarea>
```

**Почему форма обратной связи — интересная цель?**

Формы где пользователь вводит текст и этот текст потом отображается на сайте — классические точки для XSS. Если сервер не экранирует введённые данные перед отображением, то вместо текста можно вставить HTML-теги которые браузер выполнит как код.

**Почему `maxlength="50"` сразу подозрителен?**

Это браузерное ограничение. Мы уже знаем из предыдущих breach'ей что любое ограничение только на клиенте можно обойти. `maxlength` — HTML-атрибут, он не позволяет ввести больше 50 символов через интерфейс браузера. Но нам нужно вставить payload длиннее 50 символов — значит первым делом убираем это ограничение.

---

### Шаг 2 — Убрать ограничение `maxlength`

1. Нажимаем **F12** → вкладка **Elements**
2. Находим `<textarea id="mtxtMessage" maxlength="50">`
3. Дважды кликаем на `maxlength="50"` и меняем на `maxlength="424242424"`

**Почему такое большое число?**

Чтобы точно не столкнуться с ограничением. `424242424` — просто большое число, можно поставить любое. После этого поле принимает текст любой длины.

**Почему не убрать атрибут вообще?**

Можно и так — без `maxlength` ограничения нет. Но изменить значение быстрее чем удалять атрибут.

---

### Шаг 3 — Составить payload

В поле Name вводим любое допустимое имя:
```
Will
```

В поле Message вставляем payload:
```html
<img src="image.jpg" onload="alert('42')" />a
```

**Почему именно такой payload а не `<script>alert()</script>`?**

Многие сайты фильтруют тег `<script>` — это первое что блокируют примитивные фильтры XSS. Но JavaScript можно выполнить через атрибуты событий других тегов. `onload` — обработчик события «элемент загружен». Он срабатывает когда браузер загружает изображение.

**Разбор payload:**

| Часть | Что делает |
|-------|-----------|
| `<img` | HTML-тег изображения |
| `src="image.jpg"` | Указываем источник — файл может не существовать, это не важно |
| `onload="alert('42')"` | JavaScript который выполнится когда изображение загрузится |
| `/>` | Закрываем тег |
| `a` | Символ после тега — иногда нужен чтобы форма приняла сообщение как непустое |

**Почему `onload` а не `onerror`?**

Оба варианта работают. `onload` срабатывает при успешной загрузке, `onerror` — при ошибке. Если `image.jpg` не существует — `onerror` был бы надёжнее. Но в данном случае сервер может отдавать этот файл, поэтому `onload`.

---

### Шаг 4 — Отправить форму

Нажимаем Submit. Браузер отправляет форму, сервер сохраняет данные — и возвращает страницу где наш payload рендерится как HTML. Браузер видит `<img onload="alert('42')">`, загружает изображение, выполняет `alert('42')` — появляется всплывающее окно и флаг.

**Что произошло на сервере?**

Сервер получил строку `<img src="image.jpg" onload="alert('42')" />a` и вставил её в HTML-страницу как есть, без экранирования. Если бы сервер экранировал спецсимволы, браузер увидел бы безобидный текст:
```
&lt;img src="image.jpg" onload="alert('42')" /&gt;a
```
И никакого скрипта не выполнилось бы.

---

### Логика атаки — цепочка

```
Форма обратной связи ограничивает длину через maxlength="50" в HTML
    ↓  убираем ограничение через DevTools → Elements
Вводим XSS payload: <img src="image.jpg" onload="alert('42')" />
    ↓  отправляем форму
Сервер сохраняет payload без экранирования
    ↓  отображает на странице как HTML
Браузер выполняет JavaScript из атрибута onload
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| `maxlength` только в HTML | Проверять длину на сервере тоже |
| Пользовательский текст вставляется в HTML без экранирования | Использовать `htmlspecialchars()` в PHP или эквивалент |
| Нет Content-Security-Policy | Добавить CSP-заголовок запрещающий inline-скрипты |

**Пример правильного экранирования на PHP:**
```php
// Уязвимо:
echo $_POST['mtxtMessage'];

// Безопасно:
echo htmlspecialchars($_POST['mtxtMessage'], ENT_QUOTES, 'UTF-8');
```

`htmlspecialchars()` превращает `<` в `&lt;`, `>` в `&gt;`, `"` в `&quot;`. Браузер отображает их как текст, но не выполняет как HTML.

---
---

## 🇬🇧 English Version

### Overview — What Happened

The feedback form restricts message length via the `maxlength="50"` attribute on the `<textarea>` HTML element. This restriction exists only in the browser — the server accepts text of any length and does not escape it before rendering. We remove the restriction via DevTools, insert an HTML tag containing JavaScript — the server stores it as-is and the browser executes the script.

---

### How This XSS Differs from Breach 11

In Breach 11 we performed **Reflected XSS** via a URL parameter: the malicious code was passed in the URL and executed only for whoever opened that link.

Here it is potentially **Stored XSS**: the malicious code is submitted through a form, stored on the server, and executes for everyone who opens the feedback page. This is significantly more dangerous — the attack fires automatically for all users without needing to send them a special link.

| | Reflected XSS | Stored XSS |
|--|--------------|------------|
| Where payload is stored | In the URL | In the database / on the server |
| Who is affected | Whoever opens the link | Everyone who opens the page |
| Does the victim need a link | Yes | No |
| Danger level | Medium | High |

---

### Step 1 — Find the Feedback Form

Open in browser:
```
http://localhost:8080/index.php?page=feedback
```

We see a form with Name and Message fields. In HTML the message field looks like:

```html
<textarea name="mtxtMessage" id="mtxtMessage" maxlength="50" ...></textarea>
```

**Why is the feedback form an interesting target?**

Forms where a user enters text that is later displayed on the site are classic XSS entry points. If the server doesn't escape user input before rendering it, HTML tags can be injected instead of text — and the browser will execute them as code.

**Why is `maxlength="50"` immediately suspicious?**

It is a browser-side restriction. From previous breaches we know that any client-only restriction can be bypassed. `maxlength` is an HTML attribute — it prevents typing more than 50 characters through the browser interface. But our payload is longer than 50 characters — so the first step is removing this restriction.

---

### Step 2 — Remove the `maxlength` Restriction

1. Press **F12** → **Elements** tab
2. Find `<textarea id="mtxtMessage" maxlength="50">`
3. Double-click on `maxlength="50"` and change it to `maxlength="424242424"`

**Why such a large number?**

To make absolutely sure we don't hit any limit. `424242424` is just a large number — any value works. After this the field accepts text of any length.

**Why not just remove the attribute entirely?**

That works too — without `maxlength` there is no restriction. But changing the value is faster than deleting the attribute.

---

### Step 3 — Build the Payload

In the Name field enter any valid name:
```
Will
```

In the Message field paste the payload:
```html
<img src="image.jpg" onload="alert('42')" />a
```

**Why this payload and not `<script>alert()</script>`?**

Many sites filter the `<script>` tag — it is the first thing primitive XSS filters block. But JavaScript can be executed through event handler attributes of other tags. `onload` is the event handler that fires when an element finishes loading. It triggers when the browser loads the image.

**Payload breakdown:**

| Part | What it does |
|------|-------------|
| `<img` | HTML image tag |
| `src="image.jpg"` | Specifies source — the file may not exist, that doesn't matter |
| `onload="alert('42')"` | JavaScript that executes when the image loads |
| `/>` | Closes the tag |
| `a` | Character after the tag — sometimes needed so the form accepts the message as non-empty |

**Why `onload` and not `onerror`?**

Both work. `onload` fires on successful load, `onerror` fires on failure. If `image.jpg` doesn't exist — `onerror` would be more reliable. But in this case the server may actually serve that file, so `onload` is used.

---

### Step 4 — Submit the Form

Click Submit. The browser sends the form, the server stores the data — and returns a page where our payload is rendered as HTML. The browser sees `<img onload="alert('42')">`, loads the image, executes `alert('42')` — the popup appears along with the flag.

**What happened on the server?**

The server received the string `<img src="image.jpg" onload="alert('42')" />a` and inserted it into the HTML page as-is, without escaping. If the server had escaped special characters, the browser would have seen harmless text:
```
&lt;img src="image.jpg" onload="alert('42')" /&gt;a
```
And no script would have executed.

---

### Attack Chain Summary

```
Feedback form restricts length via maxlength="50" in HTML
    ↓  we remove the restriction via DevTools → Elements
We enter XSS payload: <img src="image.jpg" onload="alert('42')" />
    ↓  we submit the form
Server stores the payload without escaping
    ↓  renders it on the page as raw HTML
Browser executes JavaScript from the onload attribute
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| `maxlength` only in HTML | Validate length on the server too |
| User text inserted into HTML without escaping | Use `htmlspecialchars()` in PHP or equivalent |
| No Content-Security-Policy | Add a CSP header that blocks inline scripts |

**Example of correct escaping in PHP:**
```php
// Vulnerable:
echo $_POST['mtxtMessage'];

// Safe:
echo htmlspecialchars($_POST['mtxtMessage'], ENT_QUOTES, 'UTF-8');
```

`htmlspecialchars()` converts `<` to `&lt;`, `>` to `&gt;`, `"` to `&quot;`. The browser displays them as text but does not execute them as HTML.

---
