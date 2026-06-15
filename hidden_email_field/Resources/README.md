# Client-Side Input Tampering (Hidden Form Field)

> **Тип уязвимости / Vulnerability Type:** Client-Side Input Tampering  
> **Уровень сложности / Difficulty:** Beginner  
> **Платформа / Platform:** Darkly (учебный проект / educational lab)

---

## 🇷🇺 Русская версия

### Что произошло — общая картина

Форма восстановления пароля содержит скрытое поле `<input type="hidden">` с захардкоженным email-адресом. Разработчик предполагал что пользователь не увидит это поле — но оно прекрасно видно в DevTools. Сервер принимает значение этого поля как есть, без какой-либо проверки. Меняем значение на любой email → отправляем форму → получаем флаг.

---

### Шаг 1 — Найти страницу восстановления пароля

Открываем в браузере:
```
http://localhost:8080/?page=signin
```

Нажимаем **"I forgot my password"**. Открывается форма восстановления пароля.

**Почему мы сюда пошли?**

Формы восстановления пароля — классическое место для уязвимостей. Разработчики часто реализуют их наспех и закладывают туда логику на стороне клиента, которой там быть не должно. Это одно из первых мест куда смотрит пентестер.

---

### Шаг 2 — Найти скрытое поле в DevTools

Нажимаем **F12** → вкладка **Elements**.

Ищем в HTML-коде формы тег вида:
```html
<input type="hidden" name="mail" value="webmaster@borntosec.com" />
```

**Что такое `<input type="hidden">`?**

Это HTML-элемент формы который не отображается на странице визуально, но участвует в отправке формы. Когда пользователь нажимает Submit, браузер отправляет на сервер все поля формы — в том числе скрытые. Разработчики используют их для передачи данных которые «не нужны пользователю» — например, ID сессии, токены, email.

**Почему это не защита?**

`type="hidden"` скрывает поле визуально, но не скрывает его от DevTools. Любой пользователь может открыть инспектор элементов и увидеть, изменить или удалить это поле. Слово «hidden» здесь означает только «не отображать на странице» — не более.

**Почему мы вообще смотрим в Elements?**

Когда видим форму — всегда смотрим её исходник. Скрытые поля, захардкоженные значения, комментарии в HTML — всё это видно только в DevTools и часто раскрывает логику работы приложения.

---

### Шаг 3 — Изменить значение поля

В DevTools дважды кликаем на значение атрибута `value`:
```
value="webmaster@borntosec.com"
```

Меняем на любой email, например:
```
value="attacker@example.com"
```

Нажимаем Enter — значение сохранено прямо в DOM браузера.

**Что такое DOM?**

DOM (Document Object Model) — это живое представление HTML-страницы в памяти браузера. DevTools позволяет редактировать DOM напрямую. Изменения применяются мгновенно и браузер воспринимает их как настоящий HTML — именно поэтому при отправке формы уйдёт уже изменённое значение.

**Почему именно email меняем?**

Сервер, судя по всему, использует email из этого поля чтобы определить кому сбросить пароль. Если мы меняем email — мы говорим серверу «отправь сброс вот на этот адрес». Сервер доверяет клиенту и выполняет запрос.

---

### Шаг 4 — Отправить форму

Нажимаем кнопку **Submit** на странице.

Браузер отправляет форму с изменённым значением поля `mail`. Сервер получает запрос, видит email, выполняет логику восстановления пароля — и возвращает флаг в ответе.

**Почему сервер принял поддельное значение?**

Потому что сервер не проверяет откуда пришло значение поля `mail` и соответствует ли оно реальному пользователю. Он просто берёт что пришло в POST-запросе и использует. Это нарушение базового принципа: **никогда не доверяй данным от клиента**.

---

### Логика атаки — цепочка

```
Форма восстановления пароля содержит <input type="hidden" name="mail">
    ↓  поле скрыто визуально, но видно в DevTools → Elements
Меняем value на любой email через двойной клик в DevTools
    ↓  браузер принимает изменение в DOM
Нажимаем Submit
    ↓  браузер отправляет форму с нашим email вместо оригинального
Сервер принимает значение без проверки
    ↓
FLAG
```

---

### Как исправить

| Проблема | Решение |
|----------|---------|
| Email захардкожен в скрытом поле на клиенте | Email должен храниться в серверной сессии, не в форме |
| Сервер принимает email из формы без проверки | Сервер должен сам знать email пользователя по его сессии/токену |
| Логика восстановления пароля на стороне клиента | Вся логика — только на сервере, клиент не должен передавать «кому сбросить» |

**Правильная архитектура восстановления пароля:**
```
1. Пользователь вводит свой email в форму (сам, вручную)
2. Сервер проверяет: существует ли такой email в базе
3. Если да — генерирует одноразовый токен и отправляет ссылку на этот email
4. Клиент не передаёт никаких «скрытых» данных — сервер всё решает сам
```

---
---

## 🇬🇧 English Version

### Overview — What Happened

The password recovery form contains a hidden `<input type="hidden">` field with a hardcoded email address. The developer assumed users wouldn't see this field — but it is perfectly visible in DevTools. The server accepts the value of this field as-is, without any verification. We change the value to any email, submit the form, and get the flag.

---

### Step 1 — Navigate to the Password Recovery Page

Open in browser:
```
http://localhost:8080/?page=signin
```

Click **"I forgot my password"**. The password recovery form opens.

**Why look here?**

Password recovery forms are a classic location for vulnerabilities. Developers often implement them hastily and embed client-side logic that should not be there. This is one of the first places a penetration tester examines.

---

### Step 2 — Find the Hidden Field in DevTools

Press **F12** → **Elements** tab.

Look in the form's HTML for a tag like:
```html
<input type="hidden" name="mail" value="webmaster@borntosec.com" />
```

**What is `<input type="hidden">`?**

It is an HTML form element that is not displayed visually on the page, but is included when the form is submitted. When the user clicks Submit, the browser sends all form fields to the server — including hidden ones. Developers use them to pass data the "user doesn't need to see" — session IDs, tokens, emails, etc.

**Why is this not a security measure?**

`type="hidden"` hides the field visually, but not from DevTools. Any user can open the element inspector and see, modify, or delete this field. The word "hidden" here means only "don't display on the page" — nothing more.

**Why do we look at Elements?**

When we see a form, we always inspect its source. Hidden fields, hardcoded values, HTML comments — all of this is visible only in DevTools and often reveals how the application works internally.

---

### Step 3 — Modify the Field Value

In DevTools, double-click the `value` attribute:
```
value="webmaster@borntosec.com"
```

Change it to any email, for example:
```
value="attacker@example.com"
```

Press Enter — the value is saved directly in the browser's DOM.

**What is the DOM?**

The DOM (Document Object Model) is the live representation of the HTML page in the browser's memory. DevTools allows direct editing of the DOM. Changes take effect immediately and the browser treats them as real HTML — which is why the modified value will be sent when the form is submitted.

**Why change the email specifically?**

The server apparently uses the email from this field to determine who should receive the password reset. By changing the email, we tell the server "send the reset to this address." The server trusts the client and complies.

---

### Step 4 — Submit the Form

Click the **Submit** button on the page.

The browser submits the form with the modified `mail` field value. The server receives the request, reads the email, executes the password recovery logic — and returns the flag in the response.

**Why did the server accept the forged value?**

Because the server does not verify where the `mail` field value came from or whether it corresponds to a real user. It simply takes whatever arrived in the POST request and uses it. This violates a fundamental security principle: **never trust data from the client**.

---

### Attack Chain Summary

```
Password recovery form contains <input type="hidden" name="mail">
    ↓  field is visually hidden but visible in DevTools → Elements
Double-click the value attribute in DevTools and change the email
    ↓  browser accepts the change into the DOM
Click Submit
    ↓  browser sends the form with our email instead of the original
Server accepts the value without verification
    ↓
FLAG
```

---

### How to Fix

| Problem | Fix |
|---------|-----|
| Email hardcoded in a client-side hidden field | Email must be stored in the server-side session, not in the form |
| Server accepts email from form without validation | Server should already know the user's email from their session/token |
| Password recovery logic driven by client-supplied data | All logic must be server-side; the client should not send "who to reset" |

**Correct password recovery architecture:**
```
1. User types their own email into a form field manually
2. Server checks: does this email exist in the database?
3. If yes — generates a one-time token and sends a reset link to that email
4. Client passes no "hidden" data — the server decides everything itself
```

---
