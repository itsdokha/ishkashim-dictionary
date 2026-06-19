/**
 * app.js — интерфейс учебного веб-словаря ишкашимского языка (часть участника 3).
 *
 * Что делает этот модуль:
 *   1. загружает данные словаря (участник 1) из data/dictionary.json;
 *   2. подключает готовую логику поиска (участник 2) из participant2_js/src/;
 *   3. рисует строку поиска, фильтры, список результатов и карточку слова;
 *   4. аккуратно обрабатывает краевые случаи (нет данных, нет результатов,
 *      пустые поля статьи, ошибка загрузки).
 *
 * Это ES-модуль: подключается из index.html как <script type="module">.
 * Пути относительные — index.html лежит в participant3_web/, поэтому до общих
 * папок проекта поднимаемся на два уровня (../../).
 */

import { searchDictionary, SEARCH_MODES } from '../../participant2_js/src/search.js';
import { getAvailablePartsOfSpeech } from '../../participant2_js/src/filters.js';

// Путь к данным относительно index.html (а не относительно этого файла:
// fetch разрешает путь от адреса HTML-страницы).
const DICTIONARY_URL = '../data/dictionary.json';

/**
 * Состояние приложения. Держим всё в одном объекте, чтобы было видно,
 * от чего зависит перерисовка.
 */
const state = {
  dictionary: null, // весь объект словаря { meta, entries }
  results: [], // текущий список найденных статей
  selectedId: null, // id выбранной статьи (для подсветки и карточки)
  query: '',
  mode: SEARCH_MODES.ALL,
  pos: 'all',
};

// Ссылки на элементы интерфейса (получаем один раз).
const els = {
  search: document.getElementById('search-input'),
  clear: document.getElementById('clear-button'),
  mode: document.getElementById('mode-select'),
  pos: document.getElementById('pos-select'),
  status: document.getElementById('status-line'),
  list: document.getElementById('results-list'),
  detail: document.getElementById('detail'),
  about: document.getElementById('about'),
};

/* ------------------------------------------------------------------ */
/*  Инициализация                                                      */
/* ------------------------------------------------------------------ */

/**
 * Точка входа: грузит словарь, настраивает интерфейс и показывает все слова.
 * Если загрузка падает — выводит понятное сообщение, а не «молчит».
 */
async function init() {
  try {
    state.dictionary = await loadDictionary(DICTIONARY_URL);
  } catch (error) {
    showFatalError(error);
    return;
  }

  populatePosFilter(state.dictionary);
  renderAbout(state.dictionary.meta);
  attachEventHandlers();

  // Стартовое состояние — показываем весь словарь (пустой запрос).
  runSearch();
}

/**
 * Загружает и проверяет JSON словаря.
 *
 * @param {string} url адрес файла словаря
 * @returns {Promise<{meta: object, entries: object[]}>}
 * @throws {Error} если файл недоступен или формат неожиданный
 */
async function loadDictionary(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Не удалось загрузить словарь (HTTP ${response.status}).`);
  }

  const data = await response.json();

  if (!data || !Array.isArray(data.entries)) {
    throw new Error('Файл словаря есть, но в нём нет массива entries.');
  }

  return data;
}

/* ------------------------------------------------------------------ */
/*  Фильтры и блок «О словаре»                                         */
/* ------------------------------------------------------------------ */

/**
 * Заполняет выпадающий список частей речи реально встречающимися значениями.
 * Названия берём из meta.pos_legend (не хардкодим).
 *
 * @param {{meta: object, entries: object[]}} dictionary
 */
function populatePosFilter(dictionary) {
  const legend = dictionary.meta?.pos_legend ?? {};
  const codes = getAvailablePartsOfSpeech(dictionary.entries);

  for (const code of codes) {
    const option = document.createElement('option');
    option.value = code;
    // Человекочитаемая помета, если есть в легенде, иначе сам код.
    const full = legend[code]?.full;
    const short = legend[code]?.short;
    option.textContent = full ? `${full} (${short})` : code;
    els.pos.appendChild(option);
  }
}

/**
 * Рисует справочный блок «О словаре» по данным meta.
 *
 * @param {object} meta служебная часть словаря
 */
function renderAbout(meta) {
  if (!meta) {
    return;
  }

  const sources = Array.isArray(meta.sources) ? meta.sources : [];
  const sourcesHtml = sources.length
    ? `<h3>Источники данных</h3><ul>${sources.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul>`
    : '';

  els.about.innerHTML = `
    <h2>О словаре</h2>
    <p>${escapeHtml(meta.description ?? '')}</p>
    <ul>
      <li>Язык: ${escapeHtml(meta.language ?? '')}${meta.iso639_3 ? ` (ISO&nbsp;639-3: ${escapeHtml(meta.iso639_3)})` : ''}</li>
      <li>Статей в словаре: ${state.dictionary.entries.length}</li>
      <li>Версия данных: ${escapeHtml(String(meta.version ?? '—'))}</li>
    </ul>
    ${meta.note ? `<p><em>${escapeHtml(meta.note)}</em></p>` : ''}
    ${sourcesHtml}
  `;
}

/* ------------------------------------------------------------------ */
/*  Обработчики событий                                                */
/* ------------------------------------------------------------------ */

/**
 * Навешивает обработчики на поле поиска, кнопку очистки и фильтры.
 * Ввод в поле дебаунсим, чтобы не дёргать поиск на каждую букву.
 */
function attachEventHandlers() {
  const debouncedSearch = debounce(() => {
    state.query = els.search.value;
    runSearch();
  }, 150);

  els.search.addEventListener('input', debouncedSearch);

  els.clear.addEventListener('click', () => {
    els.search.value = '';
    state.query = '';
    els.search.focus();
    runSearch();
  });

  els.mode.addEventListener('change', () => {
    state.mode = els.mode.value;
    runSearch();
  });

  els.pos.addEventListener('change', () => {
    state.pos = els.pos.value;
    runSearch();
  });
}

/* ------------------------------------------------------------------ */
/*  Поиск + отрисовка                                                  */
/* ------------------------------------------------------------------ */

/**
 * Запускает поиск участника 2 с текущим состоянием фильтров
 * и перерисовывает список и статус-строку.
 */
function runSearch() {
  const outcome = searchDictionary(state.dictionary, {
    query: state.query,
    mode: state.mode,
    pos: state.pos,
    returnAllOnEmptyQuery: true,
  });

  // Сортируем по латинской лемме — на порядок id опираться нельзя (см. data_format.md).
  state.results = [...outcome.results].sort((a, b) =>
    String(a.lemma_lat ?? '').localeCompare(String(b.lemma_lat ?? ''), 'en')
  );

  renderStatus(outcome);
  renderResults(state.results);

  // Если выбранная ранее статья пропала из выдачи — карточку сбрасываем.
  if (state.selectedId && !state.results.some((e) => e.id === state.selectedId)) {
    state.selectedId = null;
    renderPlaceholder();
  }
}

/**
 * Обновляет строку статуса (сколько найдено / подсказки).
 *
 * @param {object} outcome результат searchDictionary
 */
function renderStatus(outcome) {
  els.status.classList.remove('error');

  if (!state.query.trim()) {
    els.status.textContent = `Показаны все статьи: ${outcome.count}. Начните вводить слово.`;
    return;
  }

  els.status.textContent =
    outcome.count > 0
      ? `Найдено статей: ${outcome.count}`
      : `Ничего не найдено по запросу «${state.query.trim()}». Попробуйте другое слово или режим поиска.`;
}

/**
 * Рисует список результатов. Для пустого списка показывает дружелюбное сообщение.
 *
 * @param {object[]} entries отсортированный массив статей
 */
function renderResults(entries) {
  els.list.innerHTML = '';

  if (entries.length === 0) {
    const li = document.createElement('li');
    li.className = 'empty-message';
    li.textContent = 'Нет подходящих слов.';
    els.list.appendChild(li);
    return;
  }

  const fragment = document.createDocumentFragment();
  const normalizedQuery = state.query.trim();

  for (const entry of entries) {
    fragment.appendChild(buildResultItem(entry, normalizedQuery));
  }

  els.list.appendChild(fragment);
}

/**
 * Собирает один элемент списка результатов.
 *
 * @param {object} entry словарная статья
 * @param {string} query текущий запрос (для подсветки)
 * @returns {HTMLLIElement}
 */
function buildResultItem(entry, query) {
  const li = document.createElement('li');
  li.className = 'result-item';
  li.dataset.id = entry.id;
  if (entry.id === state.selectedId) {
    li.classList.add('active');
  }

  const translations = Array.isArray(entry.translations_ru)
    ? entry.translations_ru.join(', ')
    : '';

  li.innerHTML = `
    <div>
      <span class="result-lemma">${highlight(entry.lemma ?? '', query)}</span>
      <span class="result-pos">${escapeHtml(entry.pos_ru ?? '')}</span>
    </div>
    <div class="result-trans">${highlight(translations, query)}</div>
  `;

  li.addEventListener('click', () => selectEntry(entry.id));
  return li;
}

/**
 * Делает статью выбранной: подсвечивает в списке и рисует карточку.
 *
 * @param {string} id идентификатор статьи
 */
function selectEntry(id) {
  state.selectedId = id;

  // Перекрашиваем активный пункт без полной перерисовки списка.
  for (const item of els.list.querySelectorAll('.result-item')) {
    item.classList.toggle('active', item.dataset.id === id);
  }

  const entry = state.results.find((e) => e.id === id);
  if (entry) {
    renderDetail(entry);
  }
}

/**
 * Рисует подробную карточку слова.
 * Блоки с пустыми полями (примеры, этимология и т. п.) не рисуются.
 *
 * @param {object} entry словарная статья
 */
function renderDetail(entry) {
  const blocks = [];

  // Заголовок: лемма + помета + (тема справа).
  blocks.push(`
    <div class="detail-head">
      <h2 class="detail-lemma">${escapeHtml(entry.lemma ?? '')}</h2>
      <span class="detail-pos">${escapeHtml(entry.pos_full ?? entry.pos_ru ?? '')}</span>
      ${entry.domain ? `<span class="detail-domain">${escapeHtml(entry.domain)}</span>` : ''}
    </div>
  `);

  // Русские переводы — главное содержание.
  if (nonEmptyArray(entry.translations_ru)) {
    blocks.push(`
      <div class="detail-block">
        <h3>Перевод</h3>
        <div class="detail-translations">${escapeHtml(entry.translations_ru.join(', '))}</div>
      </div>
    `);
  }

  // Английские переводы — бонусом.
  if (nonEmptyArray(entry.translations_en)) {
    blocks.push(`
      <div class="detail-block">
        <h3>English</h3>
        <div class="detail-translations en">${escapeHtml(entry.translations_en.join(', '))}</div>
      </div>
    `);
  }

  // Варианты написания.
  if (nonEmptyArray(entry.variants)) {
    blocks.push(`
      <div class="detail-block">
        <h3>Варианты</h3>
        <div>${escapeHtml(entry.variants.join(', '))}</div>
      </div>
    `);
  }

  // Примеры употребления.
  if (nonEmptyArray(entry.examples)) {
    const items = entry.examples
      .map(
        (ex) => `
        <li>
          <div class="example-isk">${escapeHtml(ex.isk ?? '')}</div>
          <div class="example-ru">${escapeHtml(ex.ru ?? '')}</div>
        </li>`
      )
      .join('');
    blocks.push(`
      <div class="detail-block">
        <h3>Примеры</h3>
        <ul class="examples">${items}</ul>
      </div>
    `);
  }

  // Этимология — только если непустая строка.
  if (nonEmptyString(entry.etymology)) {
    blocks.push(`
      <div class="detail-block">
        <h3>Этимология</h3>
        <div>${escapeHtml(entry.etymology)}</div>
      </div>
    `);
  }

  // Лингвистический комментарий.
  if (nonEmptyString(entry.comment)) {
    blocks.push(`
      <div class="detail-block">
        <h3>Комментарий</h3>
        <div>${escapeHtml(entry.comment)}</div>
      </div>
    `);
  }

  // Источники — мелким шрифтом.
  if (nonEmptyArray(entry.sources)) {
    blocks.push(`<div class="detail-sources">Источники: ${escapeHtml(entry.sources.join(', '))}</div>`);
  }

  els.detail.innerHTML = blocks.join('');
}

/** Возвращает карточку в стартовое состояние-подсказку. */
function renderPlaceholder() {
  els.detail.innerHTML = '<p class="detail-placeholder">Выберите слово из списка слева.</p>';
}

/**
 * Показывает заметную ошибку, если словарь вообще не загрузился
 * (частая причина — открытие index.html как file:// без локального сервера).
 *
 * @param {Error} error
 */
function showFatalError(error) {
  els.status.classList.add('error');
  els.status.textContent = `Ошибка: ${error.message}`;
  els.list.innerHTML = '';
  els.detail.innerHTML = `
    <p class="detail-placeholder">
      Не удалось загрузить данные словаря.<br /><br />
      Скорее всего, страница открыта как файл (file://).<br />
      Запустите локальный сервер из корня проекта:<br />
      <code>python3 -m http.server</code><br />
      и откройте <code>http://localhost:8000/participant3_web/</code>
    </p>
  `;
}

/* ------------------------------------------------------------------ */
/*  Вспомогательные функции                                            */
/* ------------------------------------------------------------------ */

/**
 * Экранирует спецсимволы HTML, чтобы данные нельзя было «вставить» как разметку.
 *
 * @param {string} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Подсвечивает вхождения запроса в тексте тегом <mark>.
 * Сравнение нечувствительно к регистру; сам текст экранируется.
 *
 * @param {string} text исходный текст
 * @param {string} query запрос пользователя
 * @returns {string} безопасный HTML
 */
function highlight(text, query) {
  const safeText = escapeHtml(text);
  const trimmed = query.trim();

  if (!trimmed) {
    return safeText;
  }

  // Экранируем спецсимволы регулярного выражения в запросе.
  const pattern = escapeHtml(trimmed).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  if (!pattern) {
    return safeText;
  }

  try {
    return safeText.replace(new RegExp(pattern, 'gi'), (m) => `<mark>${m}</mark>`);
  } catch {
    // На всякий случай: если регэксп всё же не собрался — отдаём текст без подсветки.
    return safeText;
  }
}

/**
 * Простой дебаунс: откладывает вызов fn, пока не пройдёт wait мс без новых вызовов.
 *
 * @param {Function} fn
 * @param {number} wait миллисекунды
 * @returns {Function}
 */
function debounce(fn, wait) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

/** Проверяет, что значение — непустой массив. */
function nonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0;
}

/** Проверяет, что значение — непустая (после trim) строка. */
function nonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

// Запуск после полной загрузки DOM.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
