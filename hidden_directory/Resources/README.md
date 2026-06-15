# Directory Listing + Automated Scraping

> **Тип уязвимости / Vulnerability Type:** Exposed Directory Listing  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Сервер не отключил листинг директорий — это значит что если зайти в папку где нет `index.html`, сервер покажет список всех файлов и папок внутри. В директории `/.hidden/` лежат сотни вложенных папок, в каждой — файл `README`. В одном из них флаг. Вручную проверить все нереально — нужен скрипт.

---

### Шаг 1 — Что такое directory listing и почему это проблема

Попробуй открыть в браузере:
```
http://localhost:8080/.hidden/
```

Вместо страницы сайта ты увидишь список папок — это и есть **directory listing**. Веб-сервер (Apache, Nginx) по умолчанию может показывать содержимое папки если в ней нет файла `index.html`.

**Почему это опасно?**

Это всё равно что оставить открытой дверь в серверную. Атакующий видит структуру файловой системы, названия файлов, может скачать всё что там лежит. В данном случае там лежат сотни папок с файлами `README` — и один из них содержит флаг (или в реальной жизни — чувствительные данные).

---

### Шаг 2 — Почему нельзя найти флаг вручную

Зайди в `/.hidden/` и посмотри сколько там папок. Их сотни, и они вложены друг в друга. В каждой папке файл `README` с текстом-заглушкой (`Nope`, `Tu`, `Non` и т.д.). Флаг — в одном единственном файле среди всех них.

Вручную кликать по каждой папке → открывать README → читать → идти дальше заняло бы часы. Единственный разумный путь — автоматизация.

---

### Шаг 3 — Установка зависимостей

```bash
python3 -m pip install requests bs4
```

**Что мы устанавливаем:**

- `requests` — библиотека для HTTP-запросов. Позволяет Python делать запросы к веб-серверу и получать HTML в ответ, как это делает браузер.
- `bs4` (BeautifulSoup4) — библиотека для парсинга HTML. Позволяет извлекать из HTML конкретные элементы — например, все ссылки `<a href="...">`.

---

### Шаг 4 — Запуск скрипта

```bash
python3 scrap.py
```

Скрипт `scrap.py` лежит в папке breach'а. Он автоматически обходит все директории и собирает содержимое каждого `README`.

**Как работает скрипт — логика:**

```
Начинаем с http://localhost:8080/.hidden/
    ↓
Получаем HTML страницы → находим все ссылки <a href="...">
    ↓
Для каждой ссылки:
    - Если это "../" → пропускаем (это ссылка на родительскую папку, идти туда не нужно)
    - Если это "README" → скачиваем содержимое, сохраняем в файл scrapped_data
    - Если это папка → заходим в неё и повторяем всё сначала (рекурсия)
```

**Что такое рекурсия в данном контексте?**

Функция вызывает сама себя для каждой новой папки. Это позволяет обойти дерево директорий любой глубины — не важно сколько уровней вложенности.

**Почему пропускаем `../`?**

Каждая страница с листингом содержит ссылку `../` — «подняться на уровень выше». Если не пропустить её, скрипт уйдёт обратно в родительскую директорию и зациклится.

---

### Шаг 5 — Найти флаг среди результатов

```bash
sort -u scrapped_data | grep -v "Nope\|Tu\|Non"
```

**Разбор команды:**

| Часть | Что делает |
|-------|-----------|
| `sort -u scrapped_data` | Читает файл, сортирует строки и убирает дубликаты (`-u` = unique) |
| `grep -v "Nope\|Tu\|Non"` | Убирает строки содержащие слова-заглушки (`-v` = инвертировать) |

Все файлы-заглушки содержат одно из трёх слов: `Nope`, `Tu`, `Non`. Флаг — это что-то другое. После фильтрации остаётся одна строка — это и есть флаг.

---

### Логика атаки — цепочка

```
Сервер показывает содержимое /.hidden/ (directory listing включён)
    ↓  внутри сотни вложенных папок с файлами README
Вручную не обойти → пишем/запускаем скрипт-краулер
    ↓  скрипт рекурсивно обходит все директории
    ↓  скачивает содержимое каждого README в scrapped_data
Фильтруем заглушки командой grep -v
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Directory listing включён | В Apache: добавить `Options -Indexes` в конфиг. В Nginx: убрать `autoindex on` |
| `/.hidden/` доступна через HTTP | Внутренние директории не должны находиться в веб-руте вообще |
| Чувствительные файлы в веб-доступной папке | Хранить за пределами веб-рута или закрыть авторизацией |

---
---

## 🇬🇧 English Version

### Overview — What Happened

The server has directory listing enabled — meaning if you navigate to a folder that has no `index.html`, the server displays a list of all files and subdirectories inside. The `/.hidden/` directory contains hundreds of nested subdirectories, each with a `README` file. One of them holds the flag. Checking them all manually is impossible — automation is required.

---

### Step 1 — What Is Directory Listing and Why Is It a Problem

Open in browser:
```
http://localhost:8080/.hidden/
```

Instead of a website page, you see a file listing — this is **directory listing**. Web servers (Apache, Nginx) can display folder contents by default when no `index.html` file is present.

**Why is this dangerous?**

It is like leaving the server room door open. An attacker can see the filesystem structure, file names, and download anything stored there. In this case, hundreds of folders with `README` files are exposed — and one contains the flag (or in a real scenario — sensitive data).

---

### Step 2 — Why the Flag Cannot Be Found Manually

Open `/.hidden/` and count the folders. There are hundreds, nested inside each other. Each folder has a `README` file with decoy text (`Nope`, `Tu`, `Non`, etc.). The flag is in one single file among all of them.

Clicking through every folder → opening README → reading → moving on would take hours. Automation is the only reasonable approach.

---

### Step 3 — Installing Dependencies

```bash
python3 -m pip install requests bs4
```

**What we are installing:**

- `requests` — HTTP library for Python. Lets Python make requests to the web server and receive HTML in response, just like a browser does.
- `bs4` (BeautifulSoup4) — HTML parsing library. Lets us extract specific elements from HTML — for example, all `<a href="...">` links on a page.

---

### Step 4 — Running the Script

```bash
python3 scrap.py
```

The `scrap.py` script is located in the breach folder. It automatically traverses all directories and collects the content of every `README` file.

**How the script works — logic:**

```
Start at http://localhost:8080/.hidden/
    ↓
Fetch page HTML → find all <a href="..."> links
    ↓
For each link:
    - If it is "../" → skip it (parent directory link, going there would loop back)
    - If it is "README" → download its content, append to scrapped_data file
    - If it is a folder → enter it and repeat everything from the top (recursion)
```

**What is recursion in this context?**

The function calls itself for each new subdirectory it encounters. This allows the script to traverse a directory tree of any depth — no matter how many levels of nesting exist.

**Why skip `../`?**

Every directory listing page contains a `../` link — "go up one level." If we don't skip it, the script would navigate back to the parent directory and loop forever.

---

### Step 5 — Finding the Flag in the Results

```bash
sort -u scrapped_data | grep -v "Nope\|Tu\|Non"
```

**Command breakdown:**

| Part | What it does |
|------|-------------|
| `sort -u scrapped_data` | Reads the file, sorts lines, removes duplicates (`-u` = unique) |
| `grep -v "Nope\|Tu\|Non"` | Removes lines containing the decoy words (`-v` = invert match) |

All decoy files contain one of three words: `Nope`, `Tu`, `Non`. The flag is something else entirely. After filtering, one line remains — that is the flag.

---

### Attack Chain Summary

```
Server exposes /.hidden/ contents (directory listing enabled)
    ↓  hundreds of nested folders with README files inside
Too many to check manually → run automated crawler script
    ↓  script recursively traverses all directories
    ↓  downloads every README content into scrapped_data
Filter out decoy strings with grep -v
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| Directory listing enabled | Apache: add `Options -Indexes` to config. Nginx: remove `autoindex on` |
| `/.hidden/` accessible via HTTP | Internal directories should not be inside the web root at all |
| Sensitive files in web-accessible folder | Store outside the web root or protect with proper authentication |

---
