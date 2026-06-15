# Open Redirect

> **Тип уязвимости / Vulnerability Type:** Open Redirect  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

На сайте есть ссылки на социальные сети — Facebook, Twitter. Они реализованы через параметр `?site=` который передаётся в редирект без какой-либо проверки. Если передать туда что-то отличное от ожидаемых значений — сервер не знает что делать и вместо редиректа возвращает флаг. Это классическая уязвимость Open Redirect с дополнительным бонусом в виде флага за неожиданный ввод.

---

### Шаг 1 — Найти редирект-ссылки на странице

Смотрим на ссылки социальных сетей в нижней части сайта. В браузере наводим курсор на иконку Facebook или Twitter и смотрим в строку статуса (или просто кликаем правой кнопкой → «Копировать адрес ссылки»):

```
http://127.0.0.1:8080/index.php?page=redirect&site=facebook
http://127.0.0.1:8080/index.php?page=redirect&site=twitter
```

**Почему эти ссылки сразу интересны?**

Нормальная ссылка на Facebook выглядела бы так:
```
https://www.facebook.com/somepage
```

Но здесь ссылка идёт через собственный сервер приложения с параметром `?site=facebook`. Это означает что сервер сам решает куда перенаправить пользователя — на основе значения параметра. Такая архитектура называется **open redirect** и является потенциальной уязвимостью: если сервер не проверяет значение `?site=`, туда можно передать что угодно.

**Что такое редирект?**

HTTP-редирект — это ответ сервера с кодом `301` или `302` и заголовком `Location: <URL>`. Браузер получает его и автоматически переходит по указанному адресу. Пользователь видит что нажал одну ссылку, а оказался на другой странице.

---

### Шаг 2 — Подменить значение параметра

Меняем `site=facebook` на любое неожиданное значение:

```
http://127.0.0.1:8080/index.php?page=redirect&site=hello
```

Просто вставляем этот URL в адресную строку браузера и нажимаем Enter.

**Почему именно `hello` (или любое другое слово)?**

Сервер ожидает `facebook` или `twitter` — значения из своего внутреннего списка. Когда приходит что-то другое, логика обработки ломается: сервер не знает куда редиректить и вместо этого возвращает флаг (что является поведением специфичным для этого учебного задания).

**Почему это работает через браузер без терминала?**

Потому что мы просто меняем URL вручную. Никаких специальных заголовков или инструментов не нужно — достаточно отредактировать адресную строку.

---

### Шаг 3 — Получить флаг

После перехода по изменённому URL сервер возвращает страницу с флагом прямо в браузере.

---

### Чем опасен Open Redirect в реальной жизни

В этом задании флаг появляется при любом неожиданном значении — но в реальных приложениях open redirect используется иначе и гораздо опаснее:

**Фишинг:**
```
https://bank.com/redirect?site=https://evil.com/fake-login
```
Пользователь видит ссылку на настоящий банк, кликает — и попадает на поддельную страницу входа. Домен в начале URL выглядит легитимно, поэтому человек не замечает подмены.

**Обход OAuth:**
Некоторые OAuth-реализации используют параметр `redirect_uri`. Если он не валидируется — токены аутентификации могут утечь на сторонний сервер.

**Обход фильтров ссылок:**
Корпоративные фильтры и антиспам-системы могут пропускать ссылки на доверенные домены — и не замечать что внутри редирект на вредоносный сайт.

---

### Логика атаки — цепочка

```
Социальные ссылки реализованы через ?site= параметр
    ↓  параметр передаётся в редирект без проверки
Меняем site=facebook на site=hello в адресной строке
    ↓  сервер получает неожиданное значение
Сервер не знает куда редиректить → возвращает флаг
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| `?site=` принимает произвольные значения | Использовать whitelist — принимать только известные значения |
| URL редиректа контролируется клиентом | Хранить URLs на сервере, клиент передаёт только ключ |
| Нет валидации назначения | Проверять что итоговый URL принадлежит разрешённому домену |

**Правильная реализация:**
```php
// Сервер хранит mapping — клиент передаёт только ключ
$allowed = [
    'facebook' => 'https://www.facebook.com/ourpage',
    'twitter'  => 'https://twitter.com/ourpage',
];

$site = $_GET['site'];

if (!array_key_exists($site, $allowed)) {
    die('Invalid redirect destination');
}

header('Location: ' . $allowed[$site]);
```

Клиент передаёт `site=facebook` → сервер сам знает куда вести. Передать произвольный URL невозможно.

---
---

## 🇬🇧 English Version

### Overview — What Happened

The site has social network links — Facebook, Twitter. They are implemented via a `?site=` parameter that is passed to a redirect without any validation. Passing something other than the expected values causes the server to return the flag instead of performing the redirect. This is a classic Open Redirect vulnerability with a bonus flag for unexpected input.

---

### Step 1 — Find the Redirect Links on the Page

Look at the social network links at the bottom of the site. In the browser, hover over the Facebook or Twitter icon and check the status bar (or right-click → "Copy link address"):

```
http://127.0.0.1:8080/index.php?page=redirect&site=facebook
http://127.0.0.1:8080/index.php?page=redirect&site=twitter
```

**Why are these links immediately interesting?**

A normal Facebook link would look like:
```
https://www.facebook.com/somepage
```

But here the link goes through the application's own server with a `?site=facebook` parameter. This means the server decides where to redirect the user based on the parameter value. This architecture is called an **open redirect** and is a potential vulnerability: if the server doesn't validate `?site=`, anything can be passed there.

**What is a redirect?**

An HTTP redirect is a server response with status code `301` or `302` and a `Location: <URL>` header. The browser receives it and automatically navigates to the specified address. The user sees that they clicked one link and ended up on a different page.

---

### Step 2 — Replace the Parameter Value

Change `site=facebook` to any unexpected value:

```
http://127.0.0.1:8080/index.php?page=redirect&site=hello
```

Simply paste this URL into the browser address bar and press Enter.

**Why `hello` (or any other word)?**

The server expects `facebook` or `twitter` — values from its internal list. When something else arrives, the handling logic breaks: the server doesn't know where to redirect and instead returns the flag (which is the specific behavior built into this educational challenge).

**Why does this work in the browser without a terminal?**

Because we are simply editing the URL manually. No special headers or tools are needed — just modify the address bar.

---

### Step 3 — Get the Flag

After navigating to the modified URL, the server returns a page with the flag directly in the browser.

---

### Why Open Redirect Is Dangerous in Real Life

In this challenge the flag appears for any unexpected value — but in real applications, open redirect is exploited differently and far more dangerously:

**Phishing:**
```
https://bank.com/redirect?site=https://evil.com/fake-login
```
The user sees a link to a real bank, clicks it — and lands on a fake login page. The legitimate domain at the start of the URL looks trustworthy, so the user doesn't notice the substitution.

**OAuth bypass:**
Some OAuth implementations use a `redirect_uri` parameter. If it isn't validated, authentication tokens can leak to a third-party server.

**Bypassing link filters:**
Corporate filters and anti-spam systems may allow links to trusted domains — without noticing that they redirect to a malicious site.

---

### Attack Chain Summary

```
Social links are implemented via the ?site= parameter
    ↓  the parameter is passed to redirect without validation
We change site=facebook to site=hello in the address bar
    ↓  server receives an unexpected value
Server doesn't know where to redirect → returns the flag
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| `?site=` accepts arbitrary values | Use a whitelist — accept only known values |
| Redirect URL controlled by the client | Store URLs server-side; client passes only a key |
| No destination validation | Verify the final URL belongs to an allowed domain |

**Correct implementation:**
```php
// Server stores the mapping — client passes only the key
$allowed = [
    'facebook' => 'https://www.facebook.com/ourpage',
    'twitter'  => 'https://twitter.com/ourpage',
];

$site = $_GET['site'];

if (!array_key_exists($site, $allowed)) {
    die('Invalid redirect destination');
}

header('Location: ' . $allowed[$site]);
```

The client passes `site=facebook` → the server knows where to go. Passing an arbitrary URL is impossible.

---
