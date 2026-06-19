/**
 * filters.js
 *
 * Модуль фильтрации словарных статей.
 * Сейчас основной фильтр — по части речи, поле entry.pos.
 */

/**
 * Проверяет, является ли значение массивом словарных статей.
 * Если нет, возвращает пустой массив, чтобы код не падал.
 *
 * @param {unknown} entries
 * @returns {Array<object>}
 */
export function ensureEntries(entries) {
  return Array.isArray(entries) ? entries : [];
}

/**
 * Фильтрует статьи по части речи.
 *
 * pos = 'all', '', null или undefined означает: не фильтровать.
 *
 * @param {Array<object>} entries
 * @param {string} pos
 * @returns {Array<object>}
 */
export function filterByPartOfSpeech(entries, pos = 'all') {
  const safeEntries = ensureEntries(entries);

  if (!pos || pos === 'all') {
    return safeEntries;
  }

  return safeEntries.filter((entry) => entry?.pos === pos);
}

/**
 * Возвращает список частей речи, реально встречающихся в словаре.
 * Удобно для интерфейса участника 3: можно автоматически заполнить select.
 *
 * @param {Array<object>} entries
 * @returns {string[]}
 */
export function getAvailablePartsOfSpeech(entries) {
  const safeEntries = ensureEntries(entries);
  const posSet = new Set();

  for (const entry of safeEntries) {
    if (entry?.pos) {
      posSet.add(entry.pos);
    }
  }

  return Array.from(posSet).sort();
}
