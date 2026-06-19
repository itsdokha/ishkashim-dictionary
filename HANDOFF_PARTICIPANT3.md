# Передача работы — Участник 2 (поиск и логика)

Привет! Это моя часть проекта «Учебный веб-словарь ишкашимского языка».
Здесь поисковая логика, которую тебе нужно подключить к интерфейсу.

## Что готово к твоему приходу

```
ishkashim-dictionary/
├── data/
│   ├── dictionary.json          ← основной словарь (159 статей)
│   └── dictionary.sample.json   ← 20 статей для отладки интерфейса
├── docs/
│   ├── data_format.md           ← описание всех полей статьи
│   └── linguistic_description.md
├── participant2_js/
│   └── src/
│       ├── search.js            ← главный модуль поиска (подключаешь его)
│       ├── normalize.js         ← нормализация текста (используется внутри)
│       └── filters.js           ← фильтр по части речи (используется внутри)
└── HANDOFF.md                   ← передача от участника 1
```

---

## Как запустить проект локально

Открой `index.html` через локальный сервер, иначе `fetch` не сработает из-за CORS:

```bash
cd ~/Downloads/ishkashim-dictionary
python3 -m http.server
```

Затем открой в браузере: `http://localhost:8000`

---

## Как подключить поиск

`search.js` — ES-модуль. Подключай через `<script type="module">` или `import`:

```html
<script type="module">
  import { searchDictionary } from './participant2_js/src/search.js';

  const response = await fetch('./data/dictionary.json');
  const dictionary = await response.json();

  const result = searchDictionary(dictionary, { query: 'солнце' });
  console.log(result.count);    // число найденных статей
  console.log(result.results);  // массив статей
</script>
```

---

## API: функция `searchDictionary`

```js
searchDictionary(dictionary, options)
```

### Параметры `options`

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `query` | строка | `''` | Поисковый запрос. Регистр и диакритика не важны. |
| `pos` | строка | `'all'` | Фильтр по части речи. Код из поля `pos` (`noun`, `verb`, …) или `'all'`. |
| `mode` | строка | `'all'` | Режим поиска (см. ниже). |
| `returnAllOnEmptyQuery` | boolean | `true` | Если `true`, пустой запрос вернёт все статьи (удобно для показа полного списка при загрузке). |

### Режимы поиска (`mode`)

```js
import { SEARCH_MODES } from './participant2_js/src/search.js';

SEARCH_MODES.ALL        // 'all'        — ищет везде (по умолчанию)
SEARCH_MODES.ISHKASHIMI // 'ishkashimi' — только по ишкашимским формам
SEARCH_MODES.RUSSIAN    // 'russian'    — только по русским переводам
```

### Что возвращает

```js
{
  query: 'Солнце',           // оригинальный запрос пользователя
  normalizedQuery: 'солнце', // нормализованный (нижний регистр, без диакритики)
  pos: 'all',
  mode: 'all',
  count: 1,                  // число найденных статей
  results: [ /* статьи */ ], // массив, может быть пустым
  message: 'Найдено статей: 1'
}
```

Каждая статья в `results` — это обычный объект из `dictionary.entries`, плюс служебное поле `_match` (можно игнорировать):

```js
{
  id: 'isk_0046',
  lemma: 'rēmuz',
  ...
  _match: { fields: ['lemma', 'lemma_lat'], values: ['rēmuz', 'remuz'] }
}
```

---

## Строим список частей речи для выпадающего фильтра

Не хардкодь список — бери прямо из данных:

```js
import { getAvailablePartsOfSpeech } from './participant2_js/src/filters.js';

const response = await fetch('./data/dictionary.json');
const dictionary = await response.json();
const posList = getAvailablePartsOfSpeech(dictionary.entries);
// ['adj', 'adv', 'conj', 'noun', 'num', 'part', 'postp', 'pron', 'prep', 'verb', ...]
```

Человекочитаемые названия для пометок берёшь из поля `pos_ru` статьи, или из `dictionary.meta.pos_legend`.

---

## Что показывать в карточке статьи

| Поле | Что делать |
|---|---|
| `lemma` | Крупный заголовок статьи (научная транскрипция с диакритикой) |
| `pos_ru` | Помета рядом с заголовком (`сущ.`, `гл.`, …) |
| `translations_ru` | Главное содержание карточки. Показывай через запятую. |
| `variants` | Строка «Варианты: …». Может быть пустым массивом — не рисуй блок. |
| `examples` | Список примеров: каждый объект `{ isk, ru }`. Может быть пустым. |
| `etymology` | Показывай, если непустая строка. |
| `comment` | Показывай, если непустая строка. |
| `sources` | Мелкий шрифт, через запятую. |
| `translations_en` | Необязательно. Можно показать как бонус. |
| `domain` | Необязательно. Можно использовать для группировки по темам. |

Поле `id` используй как ключ в списках (React `key`, якорь `#isk_0046`, и т.п.).
**Не опирайся на порядок `id` как на порядок показа** — сортируй по `lemma_lat`.

---

## Важные краевые случаи для интерфейса

- `examples` может быть **пустым массивом** — не рисуй блок «Примеры», если `examples.length === 0`.
- `etymology` и `comment` могут быть **пустой строкой** — аналогично.
- Поиск по `wak` вернёт **два разных слова**: `wak` «один» (числ.) и `wak` «там» (нареч.). Это омонимы, не баг — показывай обе карточки.
- Пустой запрос по умолчанию возвращает **все статьи** — удобно для начального состояния страницы.

---

## Как проверить, что поиск работает

Из папки `participant2_js/`:

```bash
npm run test:sample   # 20 статей
npm run test:full     # 159 статей
```

Или вручную — запроси что-нибудь в консоли браузера после загрузки страницы.

---

— Участник 2
