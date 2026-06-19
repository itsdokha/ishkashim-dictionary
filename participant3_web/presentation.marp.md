---
marp: true
paginate: true
size: 16:9
title: Ишкашимский словарь
footer: Ишкашимский словарь · учебный проект 2026
style: |
  :root {
    --accent: #9c5a23;
    --accent2: #c2843f;
    --accent-soft: #f3e7d6;
    --ink: #2a241d;
    --ink-soft: #6f675b;
    --bg1: #fbf7f0;
    --bg2: #f4ead9;
    --ok: #4a7c4a;
  }
  section {
    background: linear-gradient(135deg, var(--bg1) 0%, var(--bg2) 100%);
    color: var(--ink);
    font-family: "Segoe UI", "Helvetica Neue", system-ui, sans-serif;
    font-size: 25px;
    padding: 60px 72px;
    border-top: 10px solid var(--accent);
  }
  h1 { color: var(--accent); font-size: 52px; margin: 0 0 10px; letter-spacing: -0.5px; }
  h2 {
    color: var(--accent); font-size: 36px; margin: 0 0 24px;
    padding-bottom: 12px; border-bottom: 3px solid var(--accent2);
  }
  ul, ol { line-height: 1.55; }
  li::marker { color: var(--accent2); }
  strong { color: var(--accent); }
  a { color: var(--accent2); }
  code {
    background: #2a241d; color: #f3e7d6; padding: 2px 8px;
    border-radius: 5px; font-size: 0.85em;
  }
  pre { background: #2a241d; border-radius: 12px; padding: 22px 26px; box-shadow: 0 6px 18px rgba(0,0,0,.18); }
  pre code { background: none; padding: 0; color: #f3e7d6; line-height: 1.5; }
  blockquote {
    color: var(--ink-soft); font-style: italic;
    border-left: 5px solid var(--accent2); background: rgba(255,255,255,.5);
    padding: 10px 20px; border-radius: 0 8px 8px 0;
  }
  table { font-size: 22px; border-collapse: collapse; width: 100%; box-shadow: 0 4px 14px rgba(0,0,0,.10); border-radius: 10px; overflow: hidden; }
  th { background: var(--accent); color: #fff; padding: 12px 16px; text-align: left; }
  td { padding: 10px 16px; background: rgba(255,255,255,.65); }
  tr:nth-child(even) td { background: rgba(255,255,255,.4); }
  footer { color: var(--ink-soft); font-size: 14px; }
  section::after { color: var(--ink-soft); font-weight: 600; }

  /* служебные элементы */
  .author {
    display: inline-block; background: var(--accent-soft); color: var(--accent);
    font-weight: 600; font-size: 21px; padding: 6px 16px; border-radius: 999px;
    margin-bottom: 18px;
  }
  .big { color: var(--accent); font-size: 120px; font-weight: 800; line-height: 1; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 36px; }
  .card { background: rgba(255,255,255,.7); border-radius: 14px; padding: 22px 26px; box-shadow: 0 4px 14px rgba(0,0,0,.08); }
  .card h3 { color: var(--accent); margin: 0 0 10px; font-size: 24px; }

  /* титул и финал */
  section.lead { text-align: center; justify-content: center; border-top: none; }
  section.lead::before { content: ""; }
  section.lead h1 { font-size: 64px; }
  section.lead .subtitle { color: var(--ink-soft); font-size: 28px; margin-top: 4px; }
  .team { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 46px; }
  .person { background: rgba(255,255,255,.75); border-radius: 16px; padding: 24px 18px; box-shadow: 0 6px 18px rgba(0,0,0,.10); }
  .person .role { color: var(--accent2); font-size: 18px; text-transform: uppercase; letter-spacing: 1px; }
  .person .name { color: var(--accent); font-size: 24px; font-weight: 700; margin-top: 6px; }
  .person .emoji { font-size: 40px; }
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# 📖 Ишкашимский словарь

<p class="subtitle">Удобный двуязычный веб-словарь малоресурсного языка</p>

<div class="team">
<div class="person"><div class="emoji">📚</div><div class="role">Данные и лингвистика</div><div class="name">Султонов Диер</div></div>
<div class="person"><div class="emoji">🔍</div><div class="role">Поиск и логика</div><div class="name">Михаил Петросян</div></div>
<div class="person"><div class="emoji">🖥️</div><div class="role">Интерфейс и сборка</div><div class="name">Гоибов Дадоджон</div></div>
</div>

---

## 🎯 Зачем этот проект? Кому полезен?

<div class="cols">
<div class="card">

**Проблема**

- Ишкашимский — **малоресурсный** памирский язык (ISO 639-3: `isk`).
- **Нет** общепринятой письменности.
- Лексика рассеяна по научным работам (Грирсон 1920, Пахалина 1959).

</div>
<div class="card">

**Кому полезно**

- студентам-лингвистам;
- исследователям памирских языков;
- носителям языка;
- всем интересующимся.

</div>
</div>

> Цель — собрать выверенную лексику в одном месте с быстрым и удобным поиском.

---

## ✨ Что получилось

<div class="cols">
<div>

Статический **сайт-словарь**, где пользователь:

- ищет слово на ишкашимском **или** русском;
- видит список с **подсветкой** совпадений;
- открывает **карточку**: перевод, варианты, примеры, этимология, комментарий, источники;
- фильтрует по **части речи**.

</div>
<div class="card" style="text-align:center">

<div class="big">159</div>

**словарных статей**

<small>план-минимум был 20 — перевыполнен ×8</small>

</div>
</div>

---

## 🏗️ Как устроено: архитектура

```
data/dictionary.json       →  данные            (Султонов Диер)
        ↓ fetch
participant2_js/search.js  →  поиск и фильтры    (Михаил Петросян)
        ↓ import
participant3_web/app.js    →  интерфейс и сборка (Гоибов Дадоджон)
        ↓
           готовый сайт-словарь в браузере
```

Стек: **чистые HTML / CSS / JavaScript** (ES-модули), без фреймворков и сборщиков.
Запуск — одной командой: `python3 -m http.server`.

---

## 📚 Задачи · Часть 1 — данные и лингвистика

<span class="author">👤 Султонов Диер</span>

- Согласовали единый **формат словарной статьи** — контракт для всей команды.
- Собрали **159 статей** из научных источников.
- Поля: лемма (латиница с диакритикой), кириллица, часть речи, переводы (рус./англ.), варианты, примеры, **этимология**, комментарии, источники.
- Данные генерируются скриптом и проверяются валидатором — **воспроизводимо**, не правится руками.

---

## 🔍 Задачи · Часть 2 — поиск и логика

<span class="author">👤 Михаил Петросян</span>

- Поиск **по ишкашимскому** (лемма, латиница, кириллица, варианты) и **по русскому** переводу.
- **Нормализация**: нижний регистр, снятие диакритики, `ё → е` — поиск «как набрали».
- **Фильтр** по части речи; поиск по подстроке.
- Корректная обработка **омонимов**: `wak` «один» и `wak` «там» — две разные статьи.
- Логика вынесена в отдельный модуль и **покрыта тестами**.

---

## 🖥️ Задачи · Часть 3 — интерфейс и сборка

<span class="author">👤 Гоибов Дадоджон</span>

- Веб-страница: строка поиска, режимы, фильтр, список, карточка слова.
- **Подключены** поиск участника 2 и данные участника 1 — без дублирования логики.
- Список частей речи и блок «О словаре» строятся **из данных**, не хардкодятся.
- **Адаптивная** вёрстка, подсветка совпадений, экранирование вывода.
- Оформлены **README** и презентация — продукт собран воедино.

---

## 🛟 Робастность: нестандартные случаи

| Ситуация | Что делает словарь |
|---|---|
| Пустой запрос | показывает весь словарь |
| Нет результатов | понятное сообщение + подсказка |
| Пустые примеры / этимология | блок не рисуется |
| Омонимы | показывает **все** статьи |
| Разный регистр / диакритика | нормализуются |
| Ошибка загрузки данных | инструкция про локальный сервер |

---

## ⚠️ Сложности и проблемы

<div class="cols">
<div class="card">

**Лингвистические**

- Источники старые, транскрипции расходятся — унифицировали вручную.
- Нет письменности → выбрали латиницу без диакритики как главный ключ + кириллицу и варианты.

</div>
<div class="card">

**Технические**

- `fetch` не работает из `file://` → объяснили в README про локальный сервер + понятная ошибка в UI.
- Стыковка трёх частей → заранее зафиксировали **контракт формата** данных.

</div>
</div>

---

## 🏁 Ограничения и итог

<div class="cols">
<div class="card">

**Рамки прототипа**

- нет морфологии (словоформы не приводятся к лемме);
- 159 статей базовой лексики;
- транскрипция упрощена.

</div>
<div class="card">

**Куда расти**

- морфологический поиск;
- больше статей;
- аудио произношения;
- экспорт словаря.

</div>
</div>

**Итог:** работающий, удобный и расширяемый веб-словарь малоресурсного языка — данные, поиск и интерфейс, собранные в единый продукт.

---

<!-- _class: lead -->
<!-- _footer: "" -->

# 🙏 Спасибо за внимание!
