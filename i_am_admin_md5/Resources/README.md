# Cookie Forgery (MD5)

> **Тип уязвимости / Vulnerability Type:** Insecure Authentication via Client-Side Cookie  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Эта задача демонстрирует фундаментальную ошибку в архитектуре аутентификации: сервер доверяет данным, которые пришли от клиента, без какой-либо проверки их подлинности. Приложение хранит в cookie информацию о том, является ли пользователь администратором — и принимает её на веру. Поскольку пользователь полностью контролирует свои cookies, он может написать туда что угодно.

---

### Что такое cookie и почему это важно?

**Cookie** — это небольшой фрагмент данных, который сервер отправляет браузеру, а браузер автоматически возвращает обратно при каждом следующем запросе. Cookies используются для хранения состояния сессии, настроек, идентификаторов пользователя и т.д.

**Ключевой момент:** браузер (или любой HTTP-клиент, например `curl`) может изменить значение cookie перед отправкой на сервер. Если сервер не проверяет подлинность cookie — он получит поддельное значение и примет его как настоящее.

Именно поэтому cookies **нельзя использовать для хранения чувствительных данных без криптографической подписи**.

---

### Шаг 1 — Обнаружение cookie

```bash
curl -I http://localhost:8080/
```

Флаг `-I` означает «получить только заголовки ответа» (HEAD-запрос). Среди заголовков видим:

```
Set-Cookie: I_am_admin=68934a3e9455fa72420237eb05902327
```

**Почему мы смотрим именно на cookies?**

Название cookie `I_am_admin` уже само по себе говорит о многом — это явный признак того, что приложение хранит информацию о роли пользователя на стороне клиента. Это сразу подозрительно: сервер не должен спрашивать клиента «ты администратор?» — он должен знать это сам.

Значение `68934a3e9455fa72420237eb05902327` — явно хеш (32 символа, только hex). Следующий вопрос: хеш чего?

---

### Шаг 2 — Расшифровка текущего значения

Хеш `68934a3e9455fa72420237eb05902327` — это MD5 от строки `false`.

**Как мы это поняли?**

Логика простая: cookie называется `I_am_admin`, а значит принимает булевы значения. Самые очевидные варианты — `true` и `false`. Проверяем через reverse lookup (md5.gromweb.com или crackstation.net):

```
68934a3e9455fa72420237eb05902327  →  false
```

Итак, сервер выдал нам cookie `I_am_admin=MD5("false")`, что означает «этот пользователь НЕ администратор».

**Вывод об архитектуре:** сервер принимает значение этой cookie и, вероятно, делает что-то вроде:
```python
if md5(cookie["I_am_admin"]) == md5("true"):
    show_admin_panel()
```
или даже проще — просто сравнивает хеши напрямую. В любом случае, нам нужно подделать cookie с MD5 от `true`.

---

### Шаг 3 — Генерация поддельного значения

Вычисляем MD5 от строки `true`:

```bash
echo -n "true" | md5sum
# b326b5062b2f0e69046810717534cb09
```

**Почему `-n` у `echo`?**

Без флага `-n` команда `echo` добавляет символ новой строки `\n` в конец строки. Тогда хешируется `"true\n"` вместо `"true"` — и хеш будет другим. Флаг `-n` подавляет этот перенос строки.

**Почему MD5 здесь не защищает?**

MD5 — это **хеш-функция**, а не механизм аутентификации. Она детерминирована: один и тот же входной текст всегда даёт один и тот же хеш. Зная, что сервер хешировал слово `true`, мы можем вычислить тот же хеш самостоятельно и подставить его. Никакого секретного ключа нет — защиты нет.

---

### Шаг 4 — Отправка поддельного cookie

**Через curl:**
```bash
curl -s http://localhost:8080/ --cookie "I_am_admin=b326b5062b2f0e69046810717534cb09" | grep -i flag
```

**Через браузер:**
1. Открыть DevTools (F12)
2. Вкладка `Application` → `Cookies` → `http://localhost:8080`
3. Найти cookie `I_am_admin`
4. Изменить значение на `b326b5062b2f0e69046810717534cb09`
5. Обновить страницу

Сервер получает запрос с cookie `I_am_admin=b326b5062b2f0e69046810717534cb09`, видит «MD5 от true», считает пользователя администратором и отображает флаг.

---

### Логика атаки — цепочка

```
Ответ сервера содержит Set-Cookie: I_am_admin=68934a3e9455fa72420237eb05902327
    ↓  распознаём как MD5
68934a3e9455fa72420237eb05902327  →  MD5("false")
    ↓  понимаем логику: I_am_admin = MD5("true" или "false")
Вычисляем MD5("true") = b326b5062b2f0e69046810717534cb09
    ↓  подменяем cookie в запросе
Сервер принимает поддельную cookie как подлинную
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Роль пользователя хранится в cookie на клиенте | Хранить состояние аутентификации **на сервере** (серверная сессия) |
| Cookie без криптографической подписи | Использовать подписанные токены (например, JWT с HMAC-SHA256) |
| MD5 используется для «защиты» значения | MD5 не является механизмом защиты — использовать HMAC или современное шифрование |
| Сервер доверяет клиентским данным | Золотое правило безопасности: **никогда не доверяй клиенту** |

**Правильная архитектура:**
```
Клиент хранит: session_id=случайная_непредсказуемая_строка
Сервер хранит: { session_id → { user_id, role, expiry } }
```
При таком подходе клиент не знает своей роли и не может её изменить — всё решает сервер по session_id.

---
---

## 🇬🇧 English Version

### Overview — What Happened

This challenge exposes a fundamental flaw in authentication architecture: the server trusts data that came from the client without verifying its authenticity. The application stores whether the user is an admin in a cookie — and takes it at face value. Since the user has full control over their own cookies, they can write anything they want into them.

---

### What Is a Cookie and Why Does It Matter?

A **cookie** is a small piece of data that the server sends to the browser, which the browser automatically includes in every subsequent request. Cookies are used to store session state, preferences, user identifiers, etc.

**Key point:** the browser (or any HTTP client such as `curl`) can modify a cookie's value before sending it to the server. If the server does not verify the cookie's authenticity, it will receive a forged value and treat it as legitimate.

This is why cookies **must never be used to store sensitive data without a cryptographic signature**.

---

### Step 1 — Discovering the Cookie

```bash
curl -I http://localhost:8080/
```

The `-I` flag requests only the response headers (HTTP HEAD). Among them we see:

```
Set-Cookie: I_am_admin=68934a3e9455fa72420237eb05902327
```

**Why look at cookies specifically?**

The cookie name `I_am_admin` is immediately suspicious — it is a clear sign that the application is storing the user's role on the client side. A server should never ask the client "are you an admin?" — it should already know. The value `68934a3e9455fa72420237eb05902327` looks like a hash (32 hex characters). The next question is: a hash of what?

---

### Step 2 — Decrypting the Current Value

The hash `68934a3e9455fa72420237eb05902327` is the MD5 of the string `false`.

**How did we figure this out?**

The logic is straightforward: the cookie is named `I_am_admin`, so it likely holds a boolean value. The obvious candidates are `true` and `false`. A quick reverse lookup (md5.gromweb.com or crackstation.net) confirms:

```
68934a3e9455fa72420237eb05902327  →  false
```

So the server issued us a cookie `I_am_admin=MD5("false")`, meaning "this user is NOT an admin."

**Architectural insight:** the server likely does something like:
```python
if cookie["I_am_admin"] == md5("true"):
    show_admin_panel()
```
In any case, we need to forge a cookie containing the MD5 of `true`.

---

### Step 3 — Generating the Forged Value

Compute MD5 of the string `true`:

```bash
echo -n "true" | md5sum
# b326b5062b2f0e69046810717534cb09
```

**Why the `-n` flag on `echo`?**

Without `-n`, `echo` appends a newline character `\n` to the output. This means the hash would be computed over `"true\n"` instead of `"true"`, producing a different result. The `-n` flag suppresses the trailing newline.

**Why doesn't MD5 provide protection here?**

MD5 is a **hash function**, not an authentication mechanism. It is deterministic: the same input always produces the same output. Knowing the server hashes the word `true`, we can compute the exact same hash ourselves and substitute it. There is no secret key — therefore there is no security.

---

### Step 4 — Sending the Forged Cookie

**Via curl:**
```bash
curl -s http://localhost:8080/ --cookie "I_am_admin=b326b5062b2f0e69046810717534cb09" | grep -i flag
```

**Via browser:**
1. Open DevTools (F12)
2. Go to `Application` tab → `Cookies` → `http://localhost:8080`
3. Find the `I_am_admin` cookie
4. Change its value to `b326b5062b2f0e69046810717534cb09`
5. Reload the page

The server receives a request with `I_am_admin=b326b5062b2f0e69046810717534cb09`, recognizes it as "MD5 of true", considers the user an admin, and displays the flag.

---

### Attack Chain Summary

```
Server response contains Set-Cookie: I_am_admin=68934a3e9455fa72420237eb05902327
    ↓  we recognize it as MD5
68934a3e9455fa72420237eb05902327  →  MD5("false")
    ↓  we understand the logic: I_am_admin = MD5("true" or "false")
Compute MD5("true") = b326b5062b2f0e69046810717534cb09
    ↓  substitute the cookie in the request
Server accepts the forged cookie as legitimate
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| User role stored in a client-side cookie | Store authentication state **server-side** (server session) |
| Cookie has no cryptographic signature | Use signed tokens (e.g. JWT with HMAC-SHA256) |
| MD5 used to "protect" the value | MD5 is not a protection mechanism — use HMAC or modern encryption |
| Server trusts client-supplied data | Golden rule of security: **never trust the client** |

**Correct architecture:**
```
Client stores:  session_id=random_unpredictable_string
Server stores:  { session_id → { user_id, role, expiry } }
```
With this approach the client has no knowledge of their own role and cannot modify it — the server decides everything based on the session ID.

---
