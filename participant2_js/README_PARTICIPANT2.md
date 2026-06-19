# Участник 2 — поиск и логика словаря

Эта папка содержит JS-реализацию части участника 2 для учебного веб-словаря ишкашимского языка.

## Что сделано

Файлы:

```text
src/normalize.js
src/filters.js
src/search.js
scripts/test_search.js
package.json
```

## Как эти файлы используют данные участника 1

Участник 1 подготовил словарные данные в формате:

```text
data/dictionary.sample.json
data/dictionary.json
```

Основной массив словарных статей находится в:

```js
dictionary.entries
```

Поиск работает по полям:

```text
lemma
lemma_lat
lemma_cyr
variants
translations_ru
```

Фильтр работает по полю:

```text
pos
```

## Назначение файлов

### `src/normalize.js`

Нормализует текст перед сравнением:

- убирает лишние пробелы;
- приводит к нижнему регистру;
- убирает диакритику;
- приводит разные апострофы и дефисы к одному виду.

Пример:

```js
normalizeText(' Rēmuz ') // 'remuz'
```

### `src/filters.js`

Фильтрует статьи по части речи:

```js
filterByPartOfSpeech(entries, 'noun')
```

Если передать `all`, фильтр не применяется.

### `src/search.js`

Главный файл поиска.

Пример использования:

```js
import { searchDictionary } from './src/search.js';

const response = await fetch('./data/dictionary.json');
const dictionary = await response.json();

const result = searchDictionary(dictionary, {
  query: 'солнце',
  pos: 'all',
  mode: 'all'
});

console.log(result.count);
console.log(result.results);
```

## Как проверить

Скопируйте эти файлы в корень общего проекта так, чтобы структура была такой:

```text
project/
├── data/
│   ├── dictionary.sample.json
│   └── dictionary.json
├── src/
│   ├── normalize.js
│   ├── filters.js
│   └── search.js
├── scripts/
│   └── test_search.js
└── package.json
```

Проверка на sample-файле:

```bash
node scripts/test_search.js data/dictionary.sample.json
```

Проверка на полном словаре:

```bash
node scripts/test_search.js data/dictionary.json
```

Можно также запустить через npm:

```bash
npm run test:sample
npm run test:full
```

## Что проверяет `scripts/test_search.js`

- есть ли `dictionary.entries`;
- работает ли нормализация `Rēmuz` → `remuz`;
- не ломается ли фильтр `pos`;
- пустой запрос возвращает статьи;
- несуществующий запрос возвращает 0 результатов;
- поиск по ишкашимской форме работает;
- поиск по русскому переводу работает;
- фильтр по части речи не пропускает лишние статьи.

## Что сказать на защите

Моя часть проекта отвечает за поисковую логику словаря. Я реализовал отдельный модуль нормализации текста, чтобы поиск не зависел от регистра, пробелов и диакритики. Основная функция поиска проходит по словарным статьям из `dictionary.entries` и сравнивает запрос пользователя с ишкашимскими формами, вариантами написания и русскими переводами. Также добавлен фильтр по части речи через поле `pos`. Для проверки написан отдельный тестовый скрипт, который запускается на `dictionary.sample.json` или полном `dictionary.json`.
