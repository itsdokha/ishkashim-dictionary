/**
 * normalize.js
 *
 * Модуль нормализации текста для учебного веб-словаря ишкашимского языка.
 * Нужен, чтобы поиск не зависел от регистра, лишних пробелов,
 * диакритики и некоторых вариантов написания символов.
 */

/**
 * Приводит любое значение к строке.
 * Если значение пустое, возвращает пустую строку.
 *
 * @param {unknown} value
 * @returns {string}
 */
export function toSafeString(value) {
  if (value === null || value === undefined) {
    return '';
  }

  return String(value);
}

/**
 * Нормализует текст для поиска.
 *
 * Пример:
 *   normalizeText(' Rēmuz ') -> 'remuz'
 *   normalizeText('REMUZ')   -> 'remuz'
 *
 * @param {unknown} value
 * @returns {string}
 */
export function normalizeText(value) {
  return toSafeString(value)
    .trim()
    .toLowerCase()
    // NFD раскладывает буквы с диакритикой на букву + отдельный знак.
    // Например ē -> e + знак долготы.
    .normalize('NFD')
    // Удаляем комбинируемые диакритические знаки.
    .replace(/[̀-ͯ]/g, '')
    // Приводим разные типографские апострофы к обычному.
    .replace(/[''`´ʹʻ]/g, "'")
    // Приводим разные дефисы и тире к обычному дефису.
    .replace(/[‐‑‒–—―]/g, '-')
    // Схлопываем несколько пробелов в один.
    .replace(/\s+/g, ' ');
}

/**
 * Нормализует массив значений.
 * Пустые значения убираются.
 *
 * @param {unknown[]} values
 * @returns {string[]}
 */
export function normalizeValues(values) {
  if (!Array.isArray(values)) {
    return [];
  }

  return values
    .map(normalizeText)
    .filter(Boolean);
}
