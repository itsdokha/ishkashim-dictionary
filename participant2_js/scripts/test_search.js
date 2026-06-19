/**
 * scripts/test_search.js
 *
 * Проверка JS-логики участника 2.
 * Запускать из корня проекта:
 *
 *   node scripts/test_search.js data/dictionary.sample.json
 *
 * или на полном словаре:
 *
 *   node scripts/test_search.js data/dictionary.json
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

import { normalizeText } from '../src/normalize.js';
import { filterByPartOfSpeech, getAvailablePartsOfSpeech } from '../src/filters.js';
import { searchDictionary, SEARCH_MODES } from '../src/search.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

const dictionaryPathFromCli = process.argv[2];
const dictionaryPath = dictionaryPathFromCli
  ? path.resolve(process.cwd(), dictionaryPathFromCli)
  : path.resolve(projectRoot, 'data/dictionary.sample.json');

function readDictionary(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(
      `Файл словаря не найден: ${filePath}\n` +
      'Передайте путь явно, например: node scripts/test_search.js data/dictionary.sample.json'
    );
  }

  const raw = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(raw);
}

function runTest(name, testFunction) {
  try {
    testFunction();
    console.log(`✓ ${name}`);
  } catch (error) {
    console.error(`✗ ${name}`);
    console.error(error.message);
    process.exitCode = 1;
  }
}

const dictionary = readDictionary(dictionaryPath);
const entries = Array.isArray(dictionary) ? dictionary : dictionary.entries;

console.log(`Проверяем словарь: ${dictionaryPath}`);
console.log(`Количество статей: ${entries.length}`);
console.log('');

runTest('dictionary содержит массив entries', () => {
  assert.ok(Array.isArray(entries), 'Ожидался массив dictionary.entries');
  assert.ok(entries.length > 0, 'В словаре должна быть хотя бы одна статья');
});

runTest('normalizeText убирает регистр, пробелы и диакритику', () => {
  assert.equal(normalizeText(' Rēmuz '), 'remuz');
  assert.equal(normalizeText('REMUZ'), 'remuz');
  assert.equal(normalizeText('  много   пробелов  '), 'много пробелов');
});

runTest('filterByPartOfSpeech не ломается на all', () => {
  const result = filterByPartOfSpeech(entries, 'all');
  assert.equal(result.length, entries.length);
});

runTest('getAvailablePartsOfSpeech возвращает список частей речи', () => {
  const partsOfSpeech = getAvailablePartsOfSpeech(entries);
  assert.ok(Array.isArray(partsOfSpeech));
});

runTest('пустой запрос возвращает статьи после фильтра', () => {
  const result = searchDictionary(dictionary, { query: '' });
  assert.equal(result.count, entries.length);
});

runTest('несуществующий запрос возвращает 0 результатов', () => {
  const result = searchDictionary(dictionary, { query: 'zzzzzz_not_existing_query_12345' });
  assert.equal(result.count, 0);
});

runTest('поиск по первой статье через lemma или lemma_lat находит результат', () => {
  const firstEntry = entries[0];
  const query = firstEntry.lemma_lat || firstEntry.lemma || firstEntry.lemma_cyr;

  assert.ok(query, 'У первой статьи нет lemma/lemma_lat/lemma_cyr');

  const result = searchDictionary(dictionary, {
    query,
    mode: SEARCH_MODES.ISHKASHIMI,
  });

  assert.ok(result.count >= 1, `По запросу ${query} должен быть хотя бы один результат`);
});

runTest('поиск по русскому переводу работает, если у первой статьи есть translations_ru', () => {
  const entryWithRussianTranslation = entries.find(
    (entry) => Array.isArray(entry.translations_ru) && entry.translations_ru.length > 0
  );

  if (!entryWithRussianTranslation) {
    console.log('  пропущено: нет статей с translations_ru');
    return;
  }

  const query = entryWithRussianTranslation.translations_ru[0];

  const result = searchDictionary(dictionary, {
    query,
    mode: SEARCH_MODES.RUSSIAN,
  });

  assert.ok(result.count >= 1, `По русскому запросу ${query} должен быть результат`);
});

runTest('фильтр pos не возвращает статьи с другой частью речи', () => {
  const entryWithPos = entries.find((entry) => entry.pos);

  if (!entryWithPos) {
    console.log('  пропущено: нет статей с pos');
    return;
  }

  const result = searchDictionary(dictionary, {
    query: '',
    pos: entryWithPos.pos,
  });

  assert.ok(result.count >= 1);
  assert.ok(
    result.results.every((entry) => entry.pos === entryWithPos.pos),
    'Все результаты должны иметь выбранную часть речи'
  );
});

runTest('поиск в верхнем регистре находит результат', () => {
  const entryWithTranslation = entries.find(
    (entry) => Array.isArray(entry.translations_ru) && entry.translations_ru.length > 0
  );

  if (!entryWithTranslation) {
    console.log('  пропущено: нет статей с translations_ru');
    return;
  }

  const upperQuery = entryWithTranslation.translations_ru[0].toUpperCase();
  const result = searchDictionary(dictionary, { query: upperQuery, mode: SEARCH_MODES.RUSSIAN });

  assert.ok(result.count >= 1, `Поиск в верхнем регистре "${upperQuery}" должен находить результат`);
});

runTest('поиск без диакритики находит слова с диакритикой', () => {
  const entryWithDiacritics = entries.find(
    (entry) => entry.lemma && normalizeText(entry.lemma) !== entry.lemma
  );

  if (!entryWithDiacritics) {
    console.log('  пропущено: нет статей с диакритикой в lemma');
    return;
  }

  const queryWithoutDiacritics = normalizeText(entryWithDiacritics.lemma);
  const result = searchDictionary(dictionary, {
    query: queryWithoutDiacritics,
    mode: SEARCH_MODES.ISHKASHIMI,
  });

  assert.ok(
    result.count >= 1,
    `Поиск без диакритики "${queryWithoutDiacritics}" должен находить "${entryWithDiacritics.lemma}"`
  );
});

runTest('поиск по variants находит статью', () => {
  const entryWithVariants = entries.find(
    (entry) => Array.isArray(entry.variants) && entry.variants.length > 0
  );

  if (!entryWithVariants) {
    console.log('  пропущено: нет статей с variants');
    return;
  }

  const variant = entryWithVariants.variants[0];
  const result = searchDictionary(dictionary, { query: variant, mode: SEARCH_MODES.ISHKASHIMI });

  assert.ok(result.count >= 1, `Поиск по варианту "${variant}" должен находить результат`);
  assert.ok(
    result.results.some((entry) => entry.id === entryWithVariants.id),
    `Среди результатов должна быть статья с id "${entryWithVariants.id}"`
  );
});

runTest('омонимы: поиск возвращает все статьи с одинаковой формой', () => {
  const lemmaLatCounts = {};
  for (const entry of entries) {
    if (entry.lemma_lat) {
      lemmaLatCounts[entry.lemma_lat] = (lemmaLatCounts[entry.lemma_lat] || 0) + 1;
    }
  }

  const homonymLemma = Object.keys(lemmaLatCounts).find((l) => lemmaLatCounts[l] > 1);

  if (!homonymLemma) {
    console.log('  пропущено: омонимов в данном файле не найдено');
    return;
  }

  const result = searchDictionary(dictionary, {
    query: homonymLemma,
    mode: SEARCH_MODES.ISHKASHIMI,
  });

  assert.ok(
    result.count >= lemmaLatCounts[homonymLemma],
    `Поиск по "${homonymLemma}" должен вернуть все ${lemmaLatCounts[homonymLemma]} омонима`
  );
});

console.log('');
if (process.exitCode) {
  console.log('Есть ошибки в проверках.');
} else {
  console.log('Все проверки пройдены успешно.');
}
