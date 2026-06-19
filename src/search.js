/**
 * search.js
 *
 * Главный модуль поиска для учебного веб-словаря ишкашимского языка.
 * Работает с форматом участника 1:
 *   dictionary.entries[]
 *
 * Ищет по полям:
 *   - lemma
 *   - lemma_lat
 *   - lemma_cyr
 *   - variants
 *   - translations_ru
 *
 * Фильтрует по:
 *   - pos
 */

import { normalizeText } from './normalize.js';
import { ensureEntries, filterByPartOfSpeech } from './filters.js';

export const SEARCH_MODES = Object.freeze({
  ALL: 'all',
  ISHKASHIMI: 'ishkashimi',
  RUSSIAN: 'russian',
});

/**
 * Достаёт массив entries из объекта словаря.
 * Поддерживает формат участника 1: { meta: ..., entries: [...] }.
 *
 * @param {object|Array<object>} dictionary
 * @returns {Array<object>}
 */
export function getDictionaryEntries(dictionary) {
  if (Array.isArray(dictionary)) {
    return dictionary;
  }

  return ensureEntries(dictionary?.entries);
}

/**
 * Возвращает поля статьи, по которым ищем ишкашимское слово.
 *
 * @param {object} entry
 * @returns {Array<{field: string, value: string}>}
 */
export function getIshkashimiSearchFields(entry) {
  const fields = [];

  addValue(fields, 'lemma', entry?.lemma);
  addValue(fields, 'lemma_lat', entry?.lemma_lat);
  addValue(fields, 'lemma_cyr', entry?.lemma_cyr);

  for (const variant of ensureArray(entry?.variants)) {
    addValue(fields, 'variants', variant);
  }

  return fields;
}

/**
 * Возвращает русские поля статьи, по которым ищем перевод.
 *
 * @param {object} entry
 * @returns {Array<{field: string, value: string}>}
 */
export function getRussianSearchFields(entry) {
  const fields = [];

  for (const translation of ensureArray(entry?.translations_ru)) {
    addValue(fields, 'translations_ru', translation);
  }

  return fields;
}

/**
 * Главная функция поиска.
 *
 * @param {object|Array<object>} dictionary словарь целиком или массив entries
 * @param {object} options настройки поиска
 * @param {string} options.query запрос пользователя
 * @param {string} options.pos часть речи, например 'noun'; 'all' = без фильтра
 * @param {string} options.mode режим: 'all', 'ishkashimi', 'russian'
 * @param {boolean} options.returnAllOnEmptyQuery если true, пустой запрос вернёт все статьи после фильтра
 * @returns {object}
 */
export function searchDictionary(dictionary, options = {}) {
  const entries = getDictionaryEntries(dictionary);

  const originalQuery = options.query ?? '';
  const normalizedQuery = normalizeText(originalQuery);
  const pos = options.pos ?? 'all';
  const mode = options.mode ?? SEARCH_MODES.ALL;
  const returnAllOnEmptyQuery = options.returnAllOnEmptyQuery ?? true;

  const entriesAfterPosFilter = filterByPartOfSpeech(entries, pos);

  if (!normalizedQuery) {
    const results = returnAllOnEmptyQuery ? entriesAfterPosFilter : [];

    return {
      query: originalQuery,
      normalizedQuery,
      mode,
      pos,
      count: results.length,
      results,
      message: returnAllOnEmptyQuery
        ? 'Пустой запрос: возвращены все статьи после фильтра.'
        : 'Пустой запрос: результатов нет.',
    };
  }

  const results = [];

  for (const entry of entriesAfterPosFilter) {
    const matchInfo = getEntryMatchInfo(entry, normalizedQuery, mode);

    if (matchInfo.isMatch) {
      results.push({
        ...entry,
        _match: {
          fields: matchInfo.fields,
          values: matchInfo.values,
        },
      });
    }
  }

  return {
    query: originalQuery,
    normalizedQuery,
    mode,
    pos,
    count: results.length,
    results,
    message: results.length > 0
      ? `Найдено статей: ${results.length}`
      : 'Ничего не найдено.',
  };
}

/**
 * Проверяет, подходит ли одна словарная статья под запрос.
 * Возвращает не только true/false, но и информацию, где было совпадение.
 *
 * @param {object} entry
 * @param {string} normalizedQuery
 * @param {string} mode
 * @returns {{isMatch: boolean, fields: string[], values: string[]}}
 */
export function getEntryMatchInfo(entry, normalizedQuery, mode = SEARCH_MODES.ALL) {
  const fieldsToSearch = [];

  if (mode === SEARCH_MODES.ALL || mode === SEARCH_MODES.ISHKASHIMI) {
    fieldsToSearch.push(...getIshkashimiSearchFields(entry));
  }

  if (mode === SEARCH_MODES.ALL || mode === SEARCH_MODES.RUSSIAN) {
    fieldsToSearch.push(...getRussianSearchFields(entry));
  }

  const matchedFields = [];
  const matchedValues = [];

  for (const item of fieldsToSearch) {
    const normalizedValue = normalizeText(item.value);

    if (normalizedValue.includes(normalizedQuery)) {
      matchedFields.push(item.field);
      matchedValues.push(item.value);
    }
  }

  return {
    isMatch: matchedFields.length > 0,
    fields: unique(matchedFields),
    values: unique(matchedValues),
  };
}

function addValue(fields, field, value) {
  if (value === null || value === undefined || value === '') {
    return;
  }

  fields.push({ field, value: String(value) });
}

function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

function unique(values) {
  return Array.from(new Set(values));
}
