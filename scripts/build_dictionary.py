# -*- coding: utf-8 -*-
"""
build_dictionary.py
===================

Сборщик данных учебного веб-словаря ишкашимского языка.

Этот скрипт — единственный источник правды для данных словаря.
Он содержит выверенные словарные статьи и порождает три файла:

    data/dictionary.json         — основной машинный формат (используют участники 2 и 3)
    data/dictionary.csv          — человекочитаемый экспорт (для просмотра в Excel)
    data/dictionary.sample.json  — тестовый набор из 20 статей (для ранней отладки)

Источники данных:
    • G. A. Grierson. Ishkashmi, Zebaki and Yazghulami. London, 1920.
      (формы, этимологии, примеры из ишкашимской сказки)
    • Т. Н. Пахалина. Ишкашимский язык. М.: Изд-во АН СССР, 1959.
      (русские значения, современные формы, диалектные варианты)

Запуск:
    python3 scripts/build_dictionary.py

Скрипт не требует сторонних библиотек (только стандартная библиотека Python 3).
"""

import csv
import json
import os
import sys

# --------------------------------------------------------------------------- #
#  Справочник частей речи: канонический код -> (краткая помета, полное имя)    #
#  Участник 2 фильтрует по полю "pos" (стабильный код),                        #
#  участник 3 показывает пользователю "pos_ru".                               #
# --------------------------------------------------------------------------- #
POS = {
    "noun":   ("сущ.",    "существительное"),
    "verb":   ("гл.",     "глагол"),
    "adj":    ("прил.",   "прилагательное"),
    "adv":    ("нареч.",  "наречие"),
    "num":    ("числ.",   "числительное"),
    "pron":   ("мест.",   "местоимение"),
    "prep":   ("предл.",  "предлог"),
    "postp":  ("послел.", "послелог"),
    "conj":   ("союз",    "союз"),
    "part":   ("част.",   "частица"),
    "interj": ("межд.",   "междометие"),
}

# --------------------------------------------------------------------------- #
#  Транслитерация заголовка в упрощённую латиницу (для поиска с клавиатуры)    #
#  и в приблизительную кириллицу (для русскоязычного пользователя).           #
#  Кириллица — НЕ стандартная орфография, а вспомогательная запись для поиска. #
#  Порядок важен: диграфы и составные знаки идут раньше одиночных.             #
# --------------------------------------------------------------------------- #
_TO_ASCII = [
    ("ts", "ts"), ("dz", "dz"),
    ("χ̇", "kh"), ("γ̇", "gh"), ("x̌", "kh"), ("š̟", "sh"),
    ("ā", "a"), ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u"),
    ("å", "a"), ("ǎ", "a"), ("ъ", "e"), ("ə", "e"), ("ů", "u"), ("ü", "u"),
    ("χ", "kh"), ("x", "kh"), ("γ", "gh"),
    ("ṣ̌", "sh"), ("š", "sh"), ("ž", "zh"),
    ("θ", "th"), ("δ", "dh"),
    ("ǰ", "j"), ("c", "ch"), ("ʒ", "dz"),
    ("ḍ", "d"), ("ṭ", "t"), ("ʔ", ""),
]

_TO_CYR = [
    ("ts", "ц"), ("dz", "дз"),
    ("χ̇", "х"), ("γ̇", "г"), ("x̌", "х"), ("š̟", "ш"),
    ("ā", "а"), ("ē", "е"), ("ī", "и"), ("ō", "о"), ("ū", "у"),
    ("å", "о"), ("ǎ", "а"), ("ъ", "ы"), ("ə", "ы"), ("ů", "ю"), ("ü", "ю"),
    ("χ", "х"), ("x", "х"), ("γ", "г"),
    ("ṣ̌", "ш"), ("š", "ш"), ("ž", "ж"),
    ("θ", "с"), ("δ", "д"),
    ("ǰ", "дж"), ("c", "ч"), ("ʒ", "дз"),
    ("ḍ", "д"), ("ṭ", "т"), ("ʔ", ""),
    ("a", "а"), ("b", "б"), ("d", "д"), ("e", "е"), ("f", "ф"),
    ("g", "г"), ("h", "х"), ("i", "и"), ("j", "дж"), ("k", "к"),
    ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"),
    ("q", "к"), ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"),
    ("v", "в"), ("w", "в"), ("y", "й"), ("z", "з"),
]


def _apply(pairs, text):
    out = text
    for src, dst in pairs:
        out = out.replace(src, dst)
    return out


def to_ascii(lemma):
    """Упрощённая ASCII-латиница без диакритики (удобно набирать на клавиатуре)."""
    return _apply(_TO_ASCII, lemma.lower())


def to_cyrillic(lemma):
    """Приблизительная практическая кириллица (вспомогательная запись для поиска)."""
    return _apply(_TO_CYR, lemma.lower())


# --------------------------------------------------------------------------- #
#  СЛОВАРНЫЕ СТАТЬИ                                                            #
#                                                                             #
#  Каждая статья — словарь с полями:                                          #
#     lemma     — заголовочная форма (латинская транскрипция, по Грирсону)    #
#     pos       — код части речи (см. POS)                                     #
#     domain    — тематическая группа (для группировки в интерфейсе)          #
#     ru        — список русских переводов                                    #
#     en        — список английских переводов (по Грирсону)                    #
#     variants  — список вариантов написания (диалекты, иные транскрипции)    #
#     examples  — список пар [ишкашимский пример, русский перевод]            #
#     ety       — этимология / происхождение                                  #
#     comment   — лингвистический комментарий, диалектные формы, пометы       #
#     sources   — источники                                                   #
#                                                                             #
#  Поля id, lemma_lat, lemma_cyr, pos_ru, pos_full добавляются автоматически. #
# --------------------------------------------------------------------------- #

G = "Grierson 1920"
P = "Пахалина 1959"

ENTRIES = [

    # =================== ЛЮДИ / СЕМЬЯ ===================
    {"lemma": "ādam", "pos": "noun", "domain": "люди",
     "ru": ["человек"], "en": ["man", "person"], "variants": [],
     "examples": [["Wak ādam frī, wak šak.", "Один человек добрый, другой злой."]],
     "ety": "Из араб.-перс. ādam.", "comment": "Заимствование (через таджикский).", "sources": [G, P]},

    {"lemma": "tāt", "pos": "noun", "domain": "люди",
     "ru": ["отец"], "en": ["father"], "variants": ["tot", "tā"],
     "examples": [["Tu-t tāt, az zus.", "Ты — (мой) отец, я — (твой) сын."]],
     "ety": "Общеиранское «детское» слово; ср. тадж. дада.",
     "comment": "Пахалина: to(t); забак., сангл. tā(t). Конечный согласный часто отпадает.", "sources": [G, P]},

    {"lemma": "nan", "pos": "noun", "domain": "люди",
     "ru": ["мать"], "en": ["mother"], "variants": ["non"],
     "examples": [["Az-im dilgīr-i χi tāt, nan, vru šudúk.", "Я соскучился по своему отцу, матери, брату."]],
     "ety": "Общеиранское «детское» слово.", "comment": "Ваханск. nān.", "sources": [G, P]},

    {"lemma": "vrūd", "pos": "noun", "domain": "люди",
     "ru": ["брат"], "en": ["brother"], "variants": ["vru", "warūd"],
     "examples": [],
     "ety": "Авест. brātar-; ср. тадж. бародар.",
     "comment": "Забак. warūd — с гласной-вставкой (сварабхакти). Мн. ч. vrudárən.", "sources": [G, P]},

    {"lemma": "iχā", "pos": "noun", "domain": "люди",
     "ru": ["сестра"], "en": ["sister"], "variants": ["iχó"],
     "examples": [], "ety": "",
     "comment": "Вах. χūi, шугн. yax. Пахалина: i-χā.", "sources": [G, P]},

    {"lemma": "zas", "pos": "noun", "domain": "люди",
     "ru": ["сын"], "en": ["son"], "variants": ["zus", "zuk", "zāt"],
     "examples": [["Az zus.", "Я — (твой) сын."]],
     "ety": "Корень иран. *zan- «рождать»; ср. авест. zan-.",
     "comment": "Забак. zāt. Пахалина приводит также zuk.", "sources": [G, P]},

    {"lemma": "wuδōyd", "pos": "noun", "domain": "люди",
     "ru": ["дочь"], "en": ["daughter"], "variants": ["uδōyd", "wuδåd"],
     "examples": [], "ety": "Авест. duγδar-; ср. тадж. духтар.",
     "comment": "Протетическое w-/u-. Пахалина: wuδåd, мн. ч. wuδъ́tdár.", "sources": [G, P]},

    {"lemma": "zānǰ", "pos": "noun", "domain": "люди",
     "ru": ["жена", "женщина"], "en": ["wife"], "variants": ["zofinǰ", "wuǰinǰåk"],
     "examples": [], "ety": "Авест. jaini- «женщина, жена».",
     "comment": "Пахалина: zofinǰ «женщина», мн. ч. zonǰizēn; забак. wuǰinǰåk.", "sources": [G, P]},

    {"lemma": "vuts", "pos": "noun", "domain": "люди",
     "ru": ["дядя (брат отца)"], "en": ["paternal uncle"], "variants": ["vuc"],
     "examples": [], "ety": "", "comment": "", "sources": [G, P]},

    {"lemma": "zomān", "pos": "noun", "domain": "люди",
     "ru": ["мальчик", "юноша", "парень"], "en": ["boy", "youth"], "variants": ["zāman"],
     "examples": [["Am zomān fay tāzu.", "Этот юноша очень молод."]],
     "ety": "", "comment": "Сангл. zōmān; забак. zāman «дитя».", "sources": [G, P]},

    {"lemma": "pādšā", "pos": "noun", "domain": "люди",
     "ru": ["царь", "падишах"], "en": ["king"], "variants": ["pā́dšā"],
     "examples": [["Pādšā χē wazīr-āw gul kul.", "Царь собрал своих визирей."]],
     "ety": "Перс. pādšāh.", "comment": "Заимствование. Genitive: pādšā χān «царский дом».", "sources": [G, P]},

    {"lemma": "wazīr", "pos": "noun", "domain": "люди",
     "ru": ["визирь", "министр"], "en": ["vizier"], "variants": [],
     "examples": [], "ety": "Араб. wazīr.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "dehqān", "pos": "noun", "domain": "люди",
     "ru": ["дехканин", "крестьянин", "земледелец"], "en": ["peasant", "cultivator"], "variants": ["dekkón", "dequn"],
     "examples": [], "ety": "Перс. dehqān.", "comment": "Заимствование.", "sources": [P]},

    # =================== ТЕЛО ===================
    {"lemma": "sur", "pos": "noun", "domain": "тело",
     "ru": ["голова"], "en": ["head"], "variants": ["sār", "sar"],
     "examples": [["Ts'-χē sār wak tsām kif.", "Из своей головы вырви один глаз."]],
     "ety": "Перс. sar.", "comment": "Вах. sar.", "sources": [G, P]},

    {"lemma": "tsām", "pos": "noun", "domain": "тело",
     "ru": ["глаз"], "en": ["eye"], "variants": ["čъm"],
     "examples": [["Tu χē tsām kūr kun.", "Сделай свой (собственный) глаз слепым."]],
     "ety": "Авест. čašman-; ср. тадж. чашм.",
     "comment": "Группа -šm- > -m-. Неодушевл. мн. ч. согласуется с глаголом в ед. ч.", "sources": [G, P]},

    {"lemma": "nits", "pos": "noun", "domain": "тело",
     "ru": ["нос"], "en": ["nose"], "variants": ["nīts"],
     "examples": [], "ety": "Ср. др.-инд. nāsā, nasta- «нос».",
     "comment": "Забак. nīts.", "sources": [G, P]},

    {"lemma": "γōl", "pos": "noun", "domain": "тело",
     "ru": ["ухо"], "en": ["ear"], "variants": ["γāl"],
     "examples": [], "ety": "Авест. gaoša-; ср. тадж. гӯш.",
     "comment": "Начальный g- > γ-; -š- > -l-. Забак. γāl.", "sources": [G, P]},

    {"lemma": "dānd", "pos": "noun", "domain": "тело",
     "ru": ["зуб"], "en": ["tooth"], "variants": ["dåndъk", "dond"],
     "examples": [], "ety": "Авест. dantan-; ср. тадж. дандон.",
     "comment": "Забак. dåndъk (с суффиксом -ak).", "sources": [G, P]},

    {"lemma": "vin", "pos": "noun", "domain": "тело",
     "ru": ["борода"], "en": ["beard"], "variants": [],
     "examples": [], "ety": "", "comment": "Вах. reγiš.", "sources": [G, P]},

    {"lemma": "dust", "pos": "noun", "domain": "тело",
     "ru": ["рука"], "en": ["hand"], "variants": ["dūst", "dåst"],
     "examples": [["Azí χi dust-i ʒūd awqót, pъ uk dust-i digar vek.",
                   "В одну руку она взяла кушанье, а в другую — воду."]],
     "ety": "Др.-перс. dasta-; ср. тадж. даст.",
     "comment": "Забак. dåst. Слово dust также значит «подруга» (перс. dōst).", "sources": [G, P]},

    {"lemma": "pūd", "pos": "noun", "domain": "тело",
     "ru": ["нога", "ступня"], "en": ["foot"], "variants": ["pu"],
     "examples": [["Ti pūd χub daw kŭlúk-a!", "Хорошенько вытяни свои ноги!"]],
     "ety": "Авест. pāδa-; ср. тадж. по(й).",
     "comment": "Собственно ишкашимская форма pu — с отпадением конечного согласного; забак. pūd.", "sources": [G, P]},

    {"lemma": "dēr", "pos": "noun", "domain": "тело",
     "ru": ["живот"], "en": ["belly", "stomach"], "variants": ["der"],
     "examples": [["I dēr žūnduk šud.", "Его живот проголодался."]],
     "ety": "", "comment": "Забак. der.", "sources": [G, P]},

    {"lemma": "avzuk", "pos": "noun", "domain": "тело",
     "ru": ["сердце"], "en": ["heart"], "variants": ["duzak", "auzen"],
     "examples": [], "ety": "",
     "comment": "Не связано с авест. zərəd- «сердце». Пахалина: duzak/auzen.", "sources": [G, P]},

    {"lemma": "wēn", "pos": "noun", "domain": "тело",
     "ru": ["кровь"], "en": ["blood"], "variants": ["wen"],
     "examples": [], "ety": "Авест. vohuni-; ср. тадж. хун.",
     "comment": "Сангл. vain.", "sources": [G, P]},

    {"lemma": "wastuk", "pos": "noun", "domain": "тело",
     "ru": ["кость", "косточка (в плодах)"], "en": ["bone"], "variants": ["wůstъk", "wåstuk"],
     "examples": [], "ety": "Авест. ast-; ср. тадж. устухон.",
     "comment": "Протетическое w-; суффикс -uk. Юдг. yestoh — с протезой y-.", "sources": [G, P]},

    {"lemma": "zung", "pos": "noun", "domain": "тело",
     "ru": ["колено"], "en": ["knee"], "variants": ["žъng"],
     "examples": [], "ety": "Ср. тадж. зону.",
     "comment": "Вах. brin.", "sources": [G, P]},

    {"lemma": "zivuk", "pos": "noun", "domain": "тело",
     "ru": ["язык", "речь"], "en": ["tongue"], "variants": ["zēvuk", "zъvúk"],
     "examples": [], "ety": "Ср. тадж. забон.",
     "comment": "Вах. zik.", "sources": [G, P]},

    {"lemma": "vrits", "pos": "noun", "domain": "тело",
     "ru": ["бровь"], "en": ["eyebrow"], "variants": ["vric"],
     "examples": [], "ety": "", "comment": "", "sources": [G, P]},

    {"lemma": "suvd", "pos": "noun", "domain": "тело",
     "ru": ["плечо"], "en": ["shoulder"], "variants": [],
     "examples": [], "ety": "Авест. supti-.",
     "comment": "Группа ft > vd.", "sources": [G]},

    {"lemma": "alōša", "pos": "noun", "domain": "тело",
     "ru": ["подбородок", "челюсть"], "en": ["jaw", "chin"], "variants": ["alåša", "alaχ̌šå"],
     "examples": [], "ety": "", "comment": "Вах. zanāχ.", "sources": [G, P]},

    # =================== ЖИВОТНЫЕ ===================
    {"lemma": "kud", "pos": "noun", "domain": "животные",
     "ru": ["собака"], "en": ["dog"], "variants": ["ked"],
     "examples": [["Wak kud āγad.", "Пришла (одна) собака."]],
     "ety": "", "comment": "Забак. ked; вах. šac.", "sources": [G, P]},

    {"lemma": "vuz", "pos": "noun", "domain": "животные",
     "ru": ["коза"], "en": ["goat"], "variants": ["wuz"],
     "examples": [["Wa vuz-i zōγd āγad.", "Он взял козу и пришёл."]],
     "ety": "Авест. buza-; ср. тадж. буз.",
     "comment": "Начальный b- > v-. Забак. wuz.", "sources": [G, P]},

    {"lemma": "γū", "pos": "noun", "domain": "животные",
     "ru": ["корова"], "en": ["cow"], "variants": ["γūi"],
     "examples": [], "ety": "Авест. gav-; ср. тадж. гов.",
     "comment": "Забак. γūi.", "sources": [G, P]},

    {"lemma": "wrok", "pos": "noun", "domain": "животные",
     "ru": ["конь", "лошадь"], "en": ["horse"], "variants": ["vrūk", "verák"],
     "examples": [], "ety": "Возможно, к авест. aurvant- «быстрый».",
     "comment": "Забак. verák — с гласной-вставкой. Пахалина: vrūk.", "sources": [G, P]},

    {"lemma": "urk", "pos": "noun", "domain": "животные",
     "ru": ["волк"], "en": ["wolf"], "variants": [],
     "examples": [], "ety": "Авест. vəhrka-, др.-инд. vŕ̥ka-; ср. тадж. гург.",
     "comment": "Сохранён древний согласный k после r. Вах. šapt; юдг. wurγ.", "sources": [G, P]},

    {"lemma": "χurs", "pos": "noun", "domain": "животные",
     "ru": ["медведь"], "en": ["bear"], "variants": [],
     "examples": [["Χurs tsa urwēs frut.", "Медведь спросил у лисы."]],
     "ety": "Заимств. из перс. χirs.", "comment": "Вах. nāγordum.", "sources": [G, P]},

    {"lemma": "urwēs", "pos": "noun", "domain": "животные",
     "ru": ["лиса", "лисица"], "en": ["fox"], "variants": ["urwēsak"],
     "examples": [], "ety": "", "comment": "Вах. naχčīr.", "sources": [G, P]},

    {"lemma": "voks", "pos": "noun", "domain": "животные",
     "ru": ["змея"], "en": ["snake", "serpent"], "variants": [],
     "examples": [], "ety": "Шугн. *devusk.", "comment": "Вах. fuks.", "sources": [G]},

    {"lemma": "wārūk", "pos": "noun", "domain": "животные",
     "ru": ["ягнёнок"], "en": ["lamb"], "variants": ["wůrúk", "werák"],
     "examples": [], "ety": "Др.-инд. uraṇa- «ягнёнок».",
     "comment": "Пахалина: wůrúk «барашек», werák «ярочка».", "sources": [G, P]},

    {"lemma": "χūg", "pos": "noun", "domain": "животные",
     "ru": ["свинья", "кабан"], "en": ["pig"], "variants": [],
     "examples": [], "ety": "Авест. hu-; ср. тадж. хук.",
     "comment": "Возможно, заимств. из перс. χūk.", "sources": [G, P]},

    {"lemma": "kuwid", "pos": "noun", "domain": "животные",
     "ru": ["голубь"], "en": ["pigeon", "dove"], "variants": [],
     "examples": [], "ety": "Др.-инд. kapota-.",
     "comment": "Медиальное p > w. Вах. kibit.", "sources": [G]},

    {"lemma": "pis", "pos": "noun", "domain": "животные",
     "ru": ["кошка"], "en": ["cat"], "variants": ["puš"],
     "examples": [], "ety": "", "comment": "Забак., вах. piš.", "sources": [G, P]},

    {"lemma": "mēl", "pos": "noun", "domain": "животные",
     "ru": ["овца", "баран"], "en": ["sheep"], "variants": ["mei"],
     "examples": [], "ety": "Авест. maēša-.",
     "comment": "Вах. māi «овца».", "sources": [G]},

    {"lemma": "χūr", "pos": "noun", "domain": "животные",
     "ru": ["осёл"], "en": ["ass", "donkey"], "variants": ["χur"],
     "examples": [], "ety": "Авест. χara-; ср. тадж. хар.",
     "comment": "Забак. χūr.", "sources": [G, P]},

    {"lemma": "parinda", "pos": "noun", "domain": "животные",
     "ru": ["птица"], "en": ["bird"], "variants": [],
     "examples": [], "ety": "Перс. parinda.", "comment": "Заимствование.", "sources": [P]},

    # =================== ПРИРОДА ===================
    {"lemma": "rēmuz", "pos": "noun", "domain": "природа",
     "ru": ["солнце"], "en": ["sun"], "variants": ["ōrmozd"],
     "examples": [], "ety": "Восходит к др.-перс. ahuramazdāh- «Ахура-Мазда».",
     "comment": "Замечательное слово: забак. ōrmozd почти буквально сохраняет имя Ахура-Мазды. "
                "Произошло отождествление солнца с верховным божеством зороастризма.", "sources": [G]},

    {"lemma": "mā", "pos": "noun", "domain": "природа",
     "ru": ["луна", "месяц"], "en": ["moon"], "variants": ["māst"],
     "examples": [], "ety": "",
     "comment": "Язгул. māst; ср. язгул. miθ «день» < авест. miθra-.", "sources": [G]},

    {"lemma": "rōz", "pos": "noun", "domain": "природа",
     "ru": ["день"], "en": ["day"], "variants": ["mī"],
     "examples": [["Wak roz tā vužēr nulust.", "Один день до вечера он сидел."]],
     "ety": "Ср. тадж. рӯз.",
     "comment": "Язгул. miθ < авест. miθra-. Пахалина приводит также mī «день».", "sources": [G, P]},

    {"lemma": "šab", "pos": "noun", "domain": "природа",
     "ru": ["ночь"], "en": ["night"], "variants": ["šåb"],
     "examples": [["Šab šud.", "Настала ночь."]],
     "ety": "Авест. χšap-; ср. тадж. шаб.", "comment": "", "sources": [G, P]},

    {"lemma": "wek", "pos": "noun", "domain": "природа",
     "ru": ["вода"], "en": ["water"], "variants": ["vek"],
     "examples": [["Vek mъm-bo īžъm!", "Принеси мне воды!"]],
     "ety": "Ср. вах. yupk, мундж. yāoγa.",
     "comment": "Протетическое w-/v-. Забак. wē — с отпадением конечного -k.", "sources": [G, P]},

    {"lemma": "rōšnī", "pos": "noun", "domain": "природа",
     "ru": ["огонь"], "en": ["fire"], "variants": ["rošni"],
     "examples": [], "ety": "Ср. перс. rōšан «свет».",
     "comment": "Язгул. yēts; вах. raχnīg.", "sources": [G, P]},

    {"lemma": "varf", "pos": "noun", "domain": "природа",
     "ru": ["снег"], "en": ["snow"], "variants": ["warf"],
     "examples": [], "ety": "Авест. vafra-; ср. тадж. барф.",
     "comment": "Метатеза (vafra > varf). Рош. žiniž.", "sources": [G, P]},

    {"lemma": "ur-naduk", "pos": "noun", "domain": "природа",
     "ru": ["дождь"], "en": ["rain"], "variants": [],
     "examples": [], "ety": "Авест. vār-.", "comment": "Вах. vūr.", "sources": [G]},

    {"lemma": "struk", "pos": "noun", "domain": "природа",
     "ru": ["звезда"], "en": ["star"], "variants": ["stardk", "sitāra"],
     "examples": [], "ety": "Ср. тадж. ситора.",
     "comment": "Язгул. stardk. Пахалина приводит также заимств. sitāra.", "sources": [G, P]},

    {"lemma": "sung", "pos": "noun", "domain": "природа",
     "ru": ["камень", "скала"], "en": ["stone", "rock"], "variants": ["γrtsōk"],
     "examples": [], "ety": "", "comment": "Вах. γār; язгул. γrtsōk.", "sources": [G, P]},

    {"lemma": "daraχt", "pos": "noun", "domain": "природа",
     "ru": ["дерево (растущее)"], "en": ["tree"], "variants": ["draχt"],
     "examples": [], "ety": "Перс. daraχt.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "durk", "pos": "noun", "domain": "природа",
     "ru": ["дерево (срубленное)", "палка", "шест"], "en": ["wood", "stick"], "variants": [],
     "examples": [], "ety": "", "comment": "Вах. šung «дрова».", "sources": [G, P]},

    {"lemma": "wraza", "pos": "noun", "domain": "природа",
     "ru": ["горная вершина", "высота"], "en": ["mountain height"], "variants": ["vrāzā"],
     "examples": [], "ety": "", "comment": "Вах. vorz.", "sources": [G, P]},

    {"lemma": "γār", "pos": "noun", "domain": "природа",
     "ru": ["пещера"], "en": ["cave"], "variants": ["ambi"],
     "examples": [["Po wa ambi darūn wak χurǰīn durr åst.",
                   "Внутри той пещеры есть мешок жемчуга."]],
     "ety": "", "comment": "В сказке употребляется также ambi «пещера».", "sources": [G]},

    # =================== ДОМ / БЫТ / ЕДА ===================
    {"lemma": "χān", "pos": "noun", "domain": "дом_быт",
     "ru": ["дом"], "en": ["house"], "variants": ["χon", "χā"],
     "examples": [["Az-im nēr tar pādšā χān šud.", "Сегодня я пошёл в царский дом."]],
     "ety": "Ср. тадж. хона.",
     "comment": "Пахалина: χon; забак. χā — с отпадением конечного -n.", "sources": [G, P]},

    {"lemma": "var", "pos": "noun", "domain": "дом_быт",
     "ru": ["дверь"], "en": ["door"], "variants": [],
     "examples": [["Var vond za, paša na-átiyu!", "Закрой дверь, чтобы мухи не влетали!"]],
     "ety": "", "comment": "Сангл. vā. tsa var «изнутри, из дома».", "sources": [G, P]},

    {"lemma": "gāla", "pos": "noun", "domain": "еда",
     "ru": ["хлеб", "лепёшка"], "en": ["bread"], "variants": ["golá"],
     "examples": [["Wak lav gāla mum-bā dai.", "Дай мне кусок хлеба."]],
     "ety": "", "comment": "Вах. χoc; сангл. χēsta. Пахалина: golá.", "sources": [G, P]},

    {"lemma": "kel", "pos": "noun", "domain": "дом_быт",
     "ru": ["нож"], "en": ["knife"], "variants": ["kōž"],
     "examples": [], "ety": "Авест. karəta-; ср. тадж. корд.",
     "comment": "Вах. kōž.", "sources": [G, P]},

    {"lemma": "kūl", "pos": "noun", "domain": "дом_быт",
     "ru": ["пруд", "водоём", "лужа"], "en": ["pool"], "variants": [],
     "examples": [["Pī bun wak kūl åst.", "Под ним есть пруд."]],
     "ety": "Тюрк. köl «озеро».", "comment": "", "sources": [G]},

    {"lemma": "tilā", "pos": "noun", "domain": "дом_быт",
     "ru": ["золото"], "en": ["gold"], "variants": ["tillo", "tila"],
     "examples": [], "ety": "Перс. tillā.", "comment": "Заимствование; забак. tila.", "sources": [G, P]},

    {"lemma": "durr", "pos": "noun", "domain": "дом_быт",
     "ru": ["жемчуг"], "en": ["pearl"], "variants": ["dъr"],
     "examples": [["Durr χurǰīn gul tu-bā.", "Мешок жемчуга — весь тебе."]],
     "ety": "Араб. durr.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "χurǰīn", "pos": "noun", "domain": "дом_быт",
     "ru": ["мешок", "перемётная сума"], "en": ["sack", "saddle-bag"], "variants": [],
     "examples": [], "ety": "Перс. χurǰīn.", "comment": "Заимствование.", "sources": [G]},

    {"lemma": "wol", "pos": "noun", "domain": "дом_быт",
     "ru": ["шаровары", "штаны"], "en": ["trousers"], "variants": ["war"],
     "examples": [], "ety": "", "comment": "Забак. wal, war.", "sources": [G, P]},

    {"lemma": "wanǰī", "pos": "noun", "domain": "дом_быт",
     "ru": ["халат", "ватный халат"], "en": ["robe", "cloak"], "variants": ["vānǰi"],
     "examples": [], "ety": "", "comment": "Сангл. vanǰin.", "sources": [G, P]},

    {"lemma": "uspīr", "pos": "noun", "domain": "дом_быт",
     "ru": ["плуг"], "en": ["plough"], "variants": [],
     "examples": [], "ety": "Др.-инд. *sphāla- «лемех»; ср. перс. supār.",
     "comment": "Протетическое u-. Вах. spundar.", "sources": [G]},

    {"lemma": "yōγ", "pos": "noun", "domain": "дом_быт",
     "ru": ["ярмо"], "en": ["yoke"], "variants": [],
     "examples": [], "ety": "Др.-инд. yuga-; ср. тадж. юг.",
     "comment": "Сохранён начальный y- (не перешёл в ǰ-).", "sources": [G]},

    {"lemma": "dumb", "pos": "noun", "domain": "дом_быт",
     "ru": ["хвост"], "en": ["tail"], "variants": [],
     "examples": [["Wi dumb-i nad.", "Он схватил его (пса) за хвост."]],
     "ety": "Авест. duma-; ср. тадж. дум.", "comment": "", "sources": [G]},

    {"lemma": "taχt", "pos": "noun", "domain": "дом_быт",
     "ru": ["трон", "престол"], "en": ["throne"], "variants": [],
     "examples": [["Tar taχt nīd.", "Сядь на трон."]],
     "ety": "Перс. taχt.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "tablib", "pos": "noun", "domain": "дом_быт",
     "ru": ["врач", "лекарь"], "en": ["physician"], "variants": ["tabīb"],
     "examples": [["Wak tabīb avīraw, ižmuw.", "Найдите и приведите врача."]],
     "ety": "Араб. ṭabīb.", "comment": "Заимствование.", "sources": [G]},

    # =================== ПРИЗНАКИ (прилагательные) ===================
    {"lemma": "frī", "pos": "adj", "domain": "признаки",
     "ru": ["хороший", "добрый"], "en": ["good"], "variants": ["ferī"],
     "examples": [["Frī χē tsām kift.", "Добрый (человек) выколол свой глаз."]],
     "ety": "", "comment": "Вах. bāf; забак. ferī. Употр. также как имя героя сказки.", "sources": [G, P]},

    {"lemma": "šak", "pos": "adj", "domain": "признаки",
     "ru": ["плохой", "злой"], "en": ["bad", "wicked"], "variants": [],
     "examples": [["Šak mul.", "Злой (человек) умер."]],
     "ety": "", "comment": "Вах. šak. В сказке — имя злого героя.", "sources": [G, P]},

    {"lemma": "katta", "pos": "adj", "domain": "признаки",
     "ru": ["большой"], "en": ["great", "big"], "variants": ["kata"],
     "examples": [], "ety": "Тюрк. katta.", "comment": "Заимствование; вах. lup.", "sources": [G, P]},

    {"lemma": "cutokok", "pos": "adj", "domain": "признаки",
     "ru": ["маленький"], "en": ["little", "small"], "variants": ["cut"],
     "examples": [], "ety": "", "comment": "Забак. cut «маленький» (заимств. из инд.). Вах. dzaklāi.", "sources": [G]},

    {"lemma": "nawuk", "pos": "adj", "domain": "признаки",
     "ru": ["новый"], "en": ["new"], "variants": [],
     "examples": [], "ety": "Ср. тадж. нав.", "comment": "Вах. šöγd.", "sources": [G]},

    {"lemma": "dīr", "pos": "adj", "domain": "признаки",
     "ru": ["далёкий", "далеко"], "en": ["far", "distant"], "variants": [],
     "examples": [], "ety": "Авест. dūra-; ср. тадж. дур.",
     "comment": "Забак. dīr; вах. δīr.", "sources": [G, P]},

    {"lemma": "dъrōz", "pos": "adj", "domain": "признаки",
     "ru": ["длинный"], "en": ["long"], "variants": ["daroz"],
     "examples": [], "ety": "Перс. darāz.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "safēd", "pos": "adj", "domain": "признаки",
     "ru": ["белый"], "en": ["white"], "variants": ["surχūn"],
     "examples": [], "ety": "Заимств. из перс. safēd.",
     "comment": "Вах. ruχn. Пахалина приводит также surχūn.", "sources": [G, P]},

    {"lemma": "šu", "pos": "adj", "domain": "признаки",
     "ru": ["чёрный"], "en": ["black"], "variants": [],
     "examples": [], "ety": "Авест. syāva-; ср. тадж. сиёҳ.",
     "comment": "Группа sy > š.", "sources": [G]},

    {"lemma": "surχ", "pos": "adj", "domain": "признаки",
     "ru": ["красный"], "en": ["red"], "variants": [],
     "examples": [], "ety": "Авест. suχra-; ср. тадж. сурх.",
     "comment": "Юдг. surk-oh.", "sources": [G]},

    {"lemma": "kabūt", "pos": "adj", "domain": "признаки",
     "ru": ["синий", "голубой"], "en": ["blue"], "variants": [],
     "examples": [["Tu māl darūn wak kabūt vuz åst.",
                   "Среди твоего скота есть синяя коза."]],
     "ety": "Перс. kabūd.", "comment": "Вах. sāvz.", "sources": [G, P]},

    {"lemma": "sabz", "pos": "adj", "domain": "признаки",
     "ru": ["зелёный"], "en": ["green"], "variants": [],
     "examples": [["Ambi sar-dzā wak sabz cenār åst.",
                   "Перед пещерой есть зелёный чинар (платан)."]],
     "ety": "Перс. sabz.", "comment": "Заимствование.", "sources": [G]},

    {"lemma": "sard", "pos": "adj", "domain": "признаки",
     "ru": ["холодный"], "en": ["cold"], "variants": [],
     "examples": [], "ety": "Авест. sarəta-; ср. тадж. сард.", "comment": "", "sources": [G]},

    {"lemma": "tāza", "pos": "adj", "domain": "признаки",
     "ru": ["свежий", "новый"], "en": ["fresh", "renewed"], "variants": ["tažá"],
     "examples": [["I tsām tāza šu.", "Его глаза станут как новые (исцелятся)."]],
     "ety": "Перс. tāza.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "kūr", "pos": "adj", "domain": "признаки",
     "ru": ["слепой"], "en": ["blind"], "variants": [],
     "examples": [["Ar-wadak tsām kūr šud.", "Оба глаза стали слепыми."]],
     "ety": "Тюрк. kör.", "comment": "", "sources": [G]},

    {"lemma": "wuzduk", "pos": "adj", "domain": "признаки",
     "ru": ["высокий"], "en": ["high"], "variants": [],
     "examples": [], "ety": "Авест. bərəza-.", "comment": "Вах. wūc «высокий».", "sources": [G]},

    {"lemma": "žūnduk", "pos": "adj", "domain": "признаки",
     "ru": ["голодный"], "en": ["hungry"], "variants": ["žånduk", "zánduk"],
     "examples": [["Wēv dēr žūnduk šud.", "Их животы проголодались."]],
     "ety": "", "comment": "Вах. marz; забак. žandāki «голод».", "sources": [G, P]},

    # =================== ЧИСЛИТЕЛЬНЫЕ ===================
    {"lemma": "wak", "pos": "num", "domain": "числа",
     "ru": ["один"], "en": ["one"], "variants": ["wok", "uk"],
     "examples": [], "ety": "",
     "comment": "Употребляется также как неопределённый артикль «(один) некий». Ср. омоним wak «там» (нареч.).", "sources": [G, P]},

    {"lemma": "wak", "pos": "adv", "domain": "служебные",
     "ru": ["там", "туда"], "en": ["there"], "variants": ["wadak", "wåk"],
     "examples": [["Tsa wadak χut, tōyd.", "Оттуда он поднялся (и) пошёл."]],
     "ety": "",
     "comment": "Омоним числительного wak «один». tsa wadak / ts'-wadak «оттуда».", "sources": [G, P]},

    {"lemma": "dau", "pos": "num", "domain": "числа",
     "ru": ["два"], "en": ["two"], "variants": ["dō", "dov"],
     "examples": [["Dō ādam-ān safar-ān šud.", "Двое людей отправились в путь."]],
     "ety": "Авест. dva-; ср. тадж. ду.", "comment": "Язгул. δau.", "sources": [G, P]},

    {"lemma": "rūi", "pos": "num", "domain": "числа",
     "ru": ["три"], "en": ["three"], "variants": ["rāi", "rā"],
     "examples": [], "ety": "Авест. θrayō; ср. тадж. се.",
     "comment": "Утрачен начальный θ- (θrāyō > rūi). Забак. rāi.", "sources": [G, P]},

    {"lemma": "tsafur", "pos": "num", "domain": "числа",
     "ru": ["четыре"], "en": ["four"], "variants": ["tsafūr"],
     "examples": [], "ety": "Авест. čaθwārō; ср. тадж. чор.",
     "comment": "Забак. tsafūr; сангл. safōr.", "sources": [G, P]},

    {"lemma": "punz", "pos": "num", "domain": "числа",
     "ru": ["пять"], "en": ["five"], "variants": ["pūnz"],
     "examples": [], "ety": "Авест. panča; ср. тадж. панҷ.",
     "comment": "Группа -nč- > -nz-. Забак. pūnz.", "sources": [G, P]},

    {"lemma": "χol", "pos": "num", "domain": "числа",
     "ru": ["шесть"], "en": ["six"], "variants": ["χāl"],
     "examples": [], "ety": "Авест. χšvaš; ср. тадж. шаш.",
     "comment": "Забак. χāl; язгул. χū.", "sources": [G, P]},

    {"lemma": "uvd", "pos": "num", "domain": "числа",
     "ru": ["семь"], "en": ["seven"], "variants": ["aft"],
     "examples": [], "ety": "Авест. hapta; ср. тадж. ҳафт.",
     "comment": "Группа -pt- > -vd-; начальное h- отпало. Пахалина приводит также aft.", "sources": [G, P]},

    {"lemma": "åt", "pos": "num", "domain": "числа",
     "ru": ["восемь"], "en": ["eight"], "variants": ["ot"],
     "examples": [], "ety": "Авест. ašta, др.-инд. aṣṭau; ср. тадж. ҳашт.",
     "comment": "Церебральное ṭ указывает на индийское влияние. Забак. ot.", "sources": [G, P]},

    {"lemma": "naw", "pos": "num", "domain": "числа",
     "ru": ["девять"], "en": ["nine"], "variants": ["nao"],
     "examples": [], "ety": "Ср. тадж. нӯҳ.", "comment": "Язгул. nū.", "sources": [G, P]},

    {"lemma": "dah", "pos": "num", "domain": "числа",
     "ru": ["десять"], "en": ["ten"], "variants": ["dōs"],
     "examples": [["Nēr-bā dah roz tamuχ-bā qarār vud.",
                   "До сегодняшнего дня вам был дан срок в десять дней."]],
     "ety": "Авест. dasa; ср. тадж. даҳ.",
     "comment": "Собственно ишк. dah заимств. из перс.; исконная форма — забак. dōs.", "sources": [G, P]},

    {"lemma": "sad", "pos": "num", "domain": "числа",
     "ru": ["сто"], "en": ["hundred"], "variants": [],
     "examples": [], "ety": "Перс. sad; ср. тадж. сад.", "comment": "", "sources": [G, P]},

    {"lemma": "azār", "pos": "num", "domain": "числа",
     "ru": ["тысяча"], "en": ["thousand"], "variants": ["azor"],
     "examples": [], "ety": "Перс. hazār; ср. тадж. ҳазор.",
     "comment": "Начальное h- отпало.", "sources": [G, P]},

    # =================== МЕСТОИМЕНИЯ ===================
    {"lemma": "az", "pos": "pron", "domain": "местоимения",
     "ru": ["я"], "en": ["I"], "variants": ["azъm"],
     "examples": [["Az tu-bā dayum.", "Я тебе дам."]],
     "ety": "Авест. azəm; ср. тадж. ман (иной корень).",
     "comment": "Дат. mum-bā «мне», род. mun «мой».", "sources": [G, P]},

    {"lemma": "tu", "pos": "pron", "domain": "местоимения",
     "ru": ["ты"], "en": ["thou", "you (sg.)"], "variants": ["tъ"],
     "examples": [["Tu-t kum dzā vud?", "Ты где был?"]],
     "ety": "Авест. tū; ср. тадж. ту.",
     "comment": "Дат. tu-bā «тебе», род. ti «твой», мн. tamuχ «вы».", "sources": [G, P]},

    {"lemma": "wa", "pos": "pron", "domain": "местоимения",
     "ru": ["он", "она", "оно", "тот"], "en": ["he", "she", "it", "that"], "variants": ["āo", "wō"],
     "examples": [["Wa cenār nad.", "Он схватил чинар (платан)."]],
     "ety": "",
     "comment": "Указат. местоим. дальнего плана; одновременно личное мест. 3 л. Объектная форма wan, мн. wēv.", "sources": [G, P]},

    {"lemma": "am", "pos": "pron", "domain": "местоимения",
     "ru": ["этот", "эта", "это"], "en": ["this"], "variants": ["nakwa"],
     "examples": [["Am zomān fay tāzu.", "Этот юноша очень молод."]],
     "ety": "",
     "comment": "Указат. местоим. ближнего плана. В сказке также nakwa «этот».", "sources": [G, P]},

    {"lemma": "χē", "pos": "pron", "domain": "местоимения",
     "ru": ["свой", "своя", "своё"], "en": ["own"], "variants": ["χe"],
     "examples": [["Tu χē tsām kūr kun.", "Сделай свой (собственный) глаз слепым."]],
     "ety": "",
     "comment": "Возвратно-притяжательное; относится к подлежащему. Вах./шугн. χu.", "sources": [G, P]},

    {"lemma": "χadak", "pos": "pron", "domain": "местоимения",
     "ru": ["сам"], "en": ["self"], "variants": [],
     "examples": [["Az χadak χarum, nedum.", "Я сам поем, сам сяду."]],
     "ety": "", "comment": "Суффикс -ak. Шугн. χu-baθ.", "sources": [G]},

    {"lemma": "kudum", "pos": "pron", "domain": "местоимения",
     "ru": ["кто", "какой"], "en": ["who"], "variants": ["kāi"],
     "examples": [], "ety": "Древняя местоименная основа ka-.",
     "comment": "Забак. kāi; вах. kūi.", "sources": [G, P]},

    {"lemma": "ciz", "pos": "pron", "domain": "местоимения",
     "ru": ["что", "какой"], "en": ["what"], "variants": ["kum"],
     "examples": [["Ciz talapi tu?", "Чего ты просишь?"]],
     "ety": "Ср. перс. čī, čīz.",
     "comment": "kum dzā «где» (букв. «какое место»).", "sources": [G, P]},

    # =================== ГЛАГОЛЫ ===================
    {"lemma": "vunuk", "pos": "verb", "domain": "действия",
     "ru": ["быть", "становиться"], "en": ["to be", "to become"], "variants": ["vun-", "vud"],
     "examples": [["Az tъ-bo yor vúnъm.", "Я буду тебе другом."]],
     "ety": "Авест. √bū-; ср. тадж. будан.",
     "comment": "Основы: наст. vun-, прош. vud. Прош. вр. «был» — vud.", "sources": [G, P]},

    {"lemma": "kunuk", "pos": "verb", "domain": "действия",
     "ru": ["делать", "совершать"], "en": ["to do", "to make"], "variants": ["kъnък", "kun-", "kul"],
     "examples": [["Pādšā χē wazīr-āw gul kul.", "Царь собрал своих визирей."]],
     "ety": "Авест. √kar-; ср. тадж. кардан.",
     "comment": "Основы: наст. kun-, прош. kul. Образует составные глаголы: gul kul «собрал», trās kul «испугался».", "sources": [G, P]},

    {"lemma": "dayuk", "pos": "verb", "domain": "действия",
     "ru": ["давать"], "en": ["to give"], "variants": ["day-", "dud"],
     "examples": [["Az tu-bā dayum.", "Я тебе дам."]],
     "ety": "Авест. √dā-; ср. тадж. додан.",
     "comment": "Основы: наст. day-, прош. dud. para-day- «продавать».", "sources": [G, P]},

    {"lemma": "χaruk", "pos": "verb", "domain": "действия",
     "ru": ["есть", "кушать"], "en": ["to eat"], "variants": ["χar-", "χarum"],
     "examples": [["Az χadak χarum, nedum.", "Я сам поем, сам сяду."]],
     "ety": "Авест. √χvar-; ср. тадж. хӯрдан.",
     "comment": "Основа наст. χar-. Любопытно: в язгул. χvar- дало χvōr «солнце».", "sources": [G, P]},

    {"lemma": "suk", "pos": "verb", "domain": "действия",
     "ru": ["идти", "становиться"], "en": ["to go", "to become"], "variants": ["su-", "šud", "som"],
     "examples": [["Cenār viš šud.", "Он пошёл под чинар (платан)."]],
     "ety": "Авест. √šu-; ср. тадж. шудан.",
     "comment": "Основы: наст. su-/šu-, прош. šud. Как и тадж. шудан, значит и «идти», и «становиться».", "sources": [G, P]},

    {"lemma": "wenuk", "pos": "verb", "domain": "действия",
     "ru": ["видеть"], "en": ["to see"], "variants": ["wen-", "wend", "vīnum"],
     "examples": [["Tъ-t wan na-wendúk-o?", "Ты его (её) не видела?"]],
     "ety": "Авест. √vaen-.",
     "comment": "Основы: наст. wen-, прош. wend. Забак. vīnum «(я) вижу».", "sources": [G, P]},

    {"lemma": "γēžd", "pos": "verb", "domain": "действия",
     "ru": ["говорить", "сказать"], "en": ["to say"], "variants": ["γēd"],
     "examples": [["Sak γēžd.", "Злой (человек) сказал."]],
     "ety": "Авест. √vač-.",
     "comment": "Синкопа -ž-: забак. γēd. Прош. вр. (3 л.) «сказал».", "sources": [G, P]},

    {"lemma": "zānzuk", "pos": "verb", "domain": "действия",
     "ru": ["брать", "взять"], "en": ["to take"], "variants": ["zānz", "zōγd"],
     "examples": [["Wan zānz, mum-bā ižum.", "Возьми это (и) принеси мне."]],
     "ety": "",
     "comment": "Основы: наст. zānz, прош. zōγd. zōγd āγad «взял (и) пришёл» = «принёс».", "sources": [G]},

    {"lemma": "zanuk", "pos": "verb", "domain": "действия",
     "ru": ["убивать", "убить"], "en": ["to kill"], "variants": ["zan-", "zanum"],
     "examples": [["Nēr tamuχ zanum.", "Сегодня я убью вас."]],
     "ety": "Авест. √jan-; ср. тадж. задан.",
     "comment": "Начальное ǰ- > z-. Основа наст. zan-.", "sources": [G, P]},

    {"lemma": "āγad", "pos": "verb", "domain": "действия",
     "ru": ["приходить", "прийти"], "en": ["to come"], "variants": ["is-", "isъm"],
     "examples": [["Wak kud āγad.", "Пришла (одна) собака."]],
     "ety": "",
     "comment": "Прош. вр. (3 л.) «пришёл». Наст. основа is-: isъm «(я) прихожу».", "sources": [G, P]},

    {"lemma": "nīduk", "pos": "verb", "domain": "действия",
     "ru": ["сидеть", "сесть"], "en": ["to sit"], "variants": ["nīd", "nulust", "nalāst"],
     "examples": [["Wak roz tā vužēr nulust.", "Один день до вечера он сидел."]],
     "ety": "Авест. √had- с приставкой ni-.",
     "comment": "Основы: наст. nīd/ned-, прош. nulust; забак. nalāst.", "sources": [G, P]},

    {"lemma": "dēk", "pos": "verb", "domain": "действия",
     "ru": ["бить", "ударять"], "en": ["to strike", "to beat"], "variants": ["de-", "ded", "dū"],
     "examples": [], "ety": "",
     "comment": "Основы: наст. de-/dē-, прош. ded; стяжённая форма dūk. Образует составные глаголы: gap dēd «сказал».", "sources": [G, P]},

    {"lemma": "vonduk", "pos": "verb", "domain": "действия",
     "ru": ["вязать", "связывать", "закрывать"], "en": ["to bind"], "variants": ["vond-", "vūst", "wånd"],
     "examples": [["Var vond za, paša na-átiyu!", "Закрой дверь, чтобы мухи не влетали!"]],
     "ety": "Авест. √band-; ср. тадж. бастан.",
     "comment": "Основы: наст. vond-, прош. vūst. var vond «закрыл дверь».", "sources": [G, P]},

    {"lemma": "wazuk", "pos": "verb", "domain": "действия",
     "ru": ["падать"], "en": ["to fall"], "variants": ["waz-", "wat"],
     "examples": [["Kas za, ad galgī na-wázu!", "Смотри, чтобы эта шкурка не упала!"]],
     "ety": "", "comment": "Основы: наст. waz-, прош. wat.", "sources": [G, P]},

    {"lemma": "talapuk", "pos": "verb", "domain": "действия",
     "ru": ["просить", "требовать"], "en": ["to demand", "to ask"], "variants": ["talap-", "tilapum"],
     "examples": [["Ciz talapi tu?", "Чего ты просишь?"]],
     "ety": "Араб.-перс. talab.",
     "comment": "Основа наст. talap-.", "sources": [G, P]},

    {"lemma": "muluk", "pos": "verb", "domain": "действия",
     "ru": ["умирать", "умереть"], "en": ["to die"], "variants": ["mul"],
     "examples": [["Šak mul.", "Злой (человек) умер."]],
     "ety": "Авест. mərəta-; ср. тадж. мурдан.",
     "comment": "Группа -rt- > -l-. muluk «мёртвый, труп».", "sources": [G, P]},

    {"lemma": "frut", "pos": "verb", "domain": "действия",
     "ru": ["спрашивать", "спросить"], "en": ["to ask", "to inquire"], "variants": ["ferāt", "pors-"],
     "examples": [["Χurs tsa urwēs frut.", "Медведь спросил у лисы."]],
     "ety": "Др.-инд. pr̥ṣṭa-; ср. тадж. пурсидан.",
     "comment": "Забак. ferāt — с гласной-вставкой.", "sources": [G, P]},

    {"lemma": "šuduk", "pos": "verb", "domain": "действия",
     "ru": ["слышать", "услышать"], "en": ["to hear"], "variants": ["šud"],
     "examples": [["I gul gap-i šud.", "Он услышал весь его разговор."]],
     "ety": "Авест. sruta-; ср. тадж. шунидан.",
     "comment": "Омонимично šud «пошёл; стал» — различаются по контексту.", "sources": [G]},

    {"lemma": "kif", "pos": "verb", "domain": "действия",
     "ru": ["колоть", "вырывать (глаз)", "протыкать"], "en": ["to pierce"], "variants": ["kift"],
     "examples": [["Frī χē tsām kift.", "Добрый (человек) выколол свой глаз."]],
     "ety": "",
     "comment": "Прош. основа kift. (повел. накл. kif «выколи»).", "sources": [G]},

    {"lemma": "izuk", "pos": "verb", "domain": "действия",
     "ru": ["приносить", "принести"], "en": ["to bring"], "variants": ["ižum", "izmuw"],
     "examples": [["Mum-bā ižum.", "Принеси мне."]],
     "ety": "",
     "comment": "Повел. накл. ižum (ед.), ižmuw (мн.).", "sources": [G]},

    # =================== ВРЕМЯ / НАРЕЧИЯ ===================
    {"lemma": "nēr", "pos": "adv", "domain": "время",
     "ru": ["сегодня"], "en": ["today"], "variants": ["ner", "nur"],
     "examples": [["Nēr tamuχ zanum.", "Сегодня я убью вас."]],
     "ety": "Авест. nūrəm «теперь»; ср. тадж. нур (?).",
     "comment": "Язгул. nur. nēr-bā «до сегодняшнего дня».", "sources": [G, P]},

    {"lemma": "āluzd", "pos": "adv", "domain": "время",
     "ru": ["завтра"], "en": ["tomorrow"], "variants": ["afau"],
     "examples": [], "ety": "", "comment": "Вах. warok; язгул. afau.", "sources": [G]},

    {"lemma": "pāruzd", "pos": "adv", "domain": "время",
     "ru": ["вчера"], "en": ["yesterday"], "variants": ["biyer"],
     "examples": [], "ety": "", "comment": "Вах. yaz; язгул. biyer.", "sources": [G]},

    {"lemma": "vužēr", "pos": "noun", "domain": "время",
     "ru": ["вечер", "вечером"], "en": ["evening"], "variants": ["vajer", "vjerí"],
     "examples": [["Zomān vjerí tsa škor isu.", "Юноша вечером придёт с охоты."]],
     "ety": "", "comment": "Вах. pürz.", "sources": [G, P]},

    {"lemma": "waχt", "pos": "noun", "domain": "время",
     "ru": ["время"], "en": ["time"], "variants": ["waqt"],
     "examples": [["Cand waχt šuχt.", "Прошло некоторое время."]],
     "ety": "Араб. waqt.",
     "comment": "В заимствованных словах араб. q переходит в χ: waqt > waχt. waχt-i za «когда».", "sources": [G, P]},

    {"lemma": "tobistōn", "pos": "noun", "domain": "время",
     "ru": ["лето"], "en": ["summer"], "variants": ["tāvestån"],
     "examples": [], "ety": "Перс. tābistān.", "comment": "Заимствование; сангл. tāvestån.", "sources": [P]},

    {"lemma": "zimistōn", "pos": "noun", "domain": "время",
     "ru": ["зима", "зимой"], "en": ["winter"], "variants": ["zamistōn"],
     "examples": [], "ety": "Перс. zimistān.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "tiramō", "pos": "noun", "domain": "время",
     "ru": ["осень"], "en": ["autumn"], "variants": ["tiramå"],
     "examples": [], "ety": "Перс. tīrāmāh.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "sahar", "pos": "adv", "domain": "время",
     "ru": ["на рассвете", "утром"], "en": ["at dawn"], "variants": [],
     "examples": [["Sahar tsa wadak χut.", "На рассвете он поднялся оттуда."]],
     "ety": "Араб. saḥar.", "comment": "Заимствование.", "sources": [G]},

    # =================== СЛУЖЕБНЫЕ СЛОВА ===================
    {"lemma": "agar", "pos": "conj", "domain": "служебные",
     "ru": ["если"], "en": ["if"], "variants": [],
     "examples": [["Agar nakwa vuz avīrī, i tsām tāza šu.",
                   "Если он найдёт эту козу, её глаза исцелятся."]],
     "ety": "Перс. agar.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "za", "pos": "conj", "domain": "служебные",
     "ru": ["и", "а"], "en": ["and"], "variants": ["wa"],
     "examples": [], "ety": "",
     "comment": "Сочинит. союз; также употребляется как относительная частица «который; если».", "sources": [G, P]},

    {"lemma": "na", "pos": "part", "domain": "служебные",
     "ru": ["не", "нет"], "en": ["not"], "variants": ["nus", "nas"],
     "examples": [["Hē ciz nus vud.", "Ничего не было."]],
     "ety": "",
     "comment": "Отрицание. Forms: na, nus; забак. nas.", "sources": [G, P]},

    {"lemma": "bale", "pos": "part", "domain": "служебные",
     "ru": ["да"], "en": ["yes"], "variants": [],
     "examples": [], "ety": "Перс. bale.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "tā", "pos": "prep", "domain": "служебные",
     "ru": ["до", "пока"], "en": ["until", "up to"], "variants": ["to"],
     "examples": [["Wak roz tā vužēr nulust.", "Один день до вечера он сидел."]],
     "ety": "Перс. tā.",
     "comment": "Предлог. tā-za «до тех пор, пока».", "sources": [G, P]},

    {"lemma": "tar", "pos": "prep", "domain": "служебные",
     "ru": ["к", "в", "на"], "en": ["to", "into", "on to"], "variants": [],
     "examples": [["Tar pādšā qušlāq šud.", "Он пошёл в царский город."]],
     "ety": "",
     "comment": "Предлог направления.", "sources": [G]},

    {"lemma": "tsa", "pos": "prep", "domain": "служебные",
     "ru": ["из", "от", "с"], "en": ["from"], "variants": ["ts'-"],
     "examples": [["Χurs tsa urwēs frut.", "Медведь спросил у лисы."]],
     "ety": "",
     "comment": "Предлог; часто теряет гласный: ts'-wadak «оттуда».", "sources": [G, P]},

    {"lemma": "darūn", "pos": "postp", "domain": "служебные",
     "ru": ["внутри", "внутрь", "среди"], "en": ["within", "among"], "variants": ["dardún"],
     "examples": [["Tu māl darūn wak kabūt vuz åst.",
                   "Среди твоего скота есть синяя коза."]],
     "ety": "Перс. darūn.",
     "comment": "Послелог. po … darūn «внутри».", "sources": [G, P]},

    {"lemma": "viš", "pos": "postp", "domain": "служебные",
     "ru": ["под", "внизу"], "en": ["below", "under"], "variants": ["vъš"],
     "examples": [["Cenār viš šud.", "Он пошёл под чинар (платан)."]],
     "ety": "",
     "comment": "Послелог. pī viš «под ним».", "sources": [G, P]},

    {"lemma": "bā", "pos": "postp", "domain": "служебные",
     "ru": ["к", "для"], "en": ["to", "for"], "variants": ["-bo"],
     "examples": [["Mum-bā dai.", "Дай мне."]],
     "ety": "",
     "comment": "Послелог дательного значения; присоединяется к слову: mum-bā «мне», tu-bā «тебе».", "sources": [G, P]},

    # =================== ПРОЧЕЕ / КОММЕНТАРИИ ===================
    {"lemma": "dūd", "pos": "noun", "domain": "природа",
     "ru": ["дым", "копоть"], "en": ["smoke"], "variants": ["did", "dit"],
     "examples": [["Kāson-tsa uk χon did nēzu.", "Из одного дома идёт дым."]],
     "ety": "Иран. *dūta-.",
     "comment": "Язгул. δād. Пахалина: did.", "sources": [G, P]},

    {"lemma": "yau", "pos": "noun", "domain": "еда",
     "ru": ["провизия", "припасы", "зерно"], "en": ["provisions"], "variants": [],
     "examples": [], "ety": "", "comment": "Вах. zau.", "sources": [G, P]},

    {"lemma": "qušlāq", "pos": "noun", "domain": "дом_быт",
     "ru": ["селение", "кишлак", "город"], "en": ["town", "village"], "variants": ["qišlāq"],
     "examples": [["Tar pādšā qušlāq šud.", "Он пошёл в царский город."]],
     "ety": "Тюрк. qišlāq.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "xabar", "pos": "noun", "domain": "дом_быт",
     "ru": ["весть", "известие", "новость"], "en": ["news"], "variants": ["χabar"],
     "examples": [["Ciz χabar åst?", "Какие есть новости?"]],
     "ety": "Араб. χabar.", "comment": "Заимствование.", "sources": [G, P]},

    {"lemma": "watan", "pos": "noun", "domain": "дом_быт",
     "ru": ["родина", "отечество"], "en": ["homeland"], "variants": ["wotán"],
     "examples": [], "ety": "Араб. waṭan.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "dunyo", "pos": "noun", "domain": "дом_быт",
     "ru": ["мир", "вселенная"], "en": ["world"], "variants": ["dъnyo"],
     "examples": [], "ety": "Араб. dunyā.", "comment": "Заимствование; сангл. dönyā.", "sources": [P]},

    {"lemma": "dīn", "pos": "noun", "domain": "дом_быт",
     "ru": ["вера", "религия"], "en": ["faith", "religion"], "variants": [],
     "examples": [], "ety": "Араб. dīn.", "comment": "Заимствование.", "sources": [P]},

    {"lemma": "dard", "pos": "noun", "domain": "тело",
     "ru": ["боль"], "en": ["pain"], "variants": [],
     "examples": [["Mъno sar dard.", "У меня болит голова (головная боль)."]],
     "ety": "Перс. dard.", "comment": "Заимствование; забак. dard.", "sources": [G, P]},
]


# --------------------------------------------------------------------------- #
#  Сборка                                                                     #
# --------------------------------------------------------------------------- #
def build():
    records = []
    seen_lemmas = {}
    for i, e in enumerate(ENTRIES, start=1):
        lemma = e["lemma"]
        pos = e["pos"]
        if pos not in POS:
            raise ValueError("Неизвестная часть речи %r у слова %r" % (pos, lemma))
        pos_ru, pos_full = POS[pos]

        # стабильный id вида isk_0001 (порядок авторский, не зависит от сортировки)
        eid = "isk_%04d" % i

        # омонимы (одинаковое написание) допустимы, но отметим их в комментарии
        seen_lemmas.setdefault(lemma, []).append(eid)

        examples = [{"isk": ex[0], "ru": ex[1]} for ex in e.get("examples", [])]

        rec = {
            "id": eid,
            "lemma": lemma,
            "lemma_lat": to_ascii(lemma),
            "lemma_cyr": to_cyrillic(lemma),
            "pos": pos,
            "pos_ru": pos_ru,
            "pos_full": pos_full,
            "domain": e.get("domain", ""),
            "translations_ru": e.get("ru", []),
            "translations_en": e.get("en", []),
            "variants": e.get("variants", []),
            "examples": examples,
            "etymology": e.get("ety", ""),
            "comment": e.get("comment", ""),
            "sources": e.get("sources", []),
        }
        records.append(rec)

    return records


def write_json(records, path):
    meta = {
        "language": "ишкашимский язык",
        "language_en": "Ishkashimi",
        "iso639_3": "isk",
        "glottolog": "ishk1244",
        "script": "латинская научная транскрипция (по Грирсону), с вариантами",
        "version": "1.0",
        "entry_count": len(records),
        "description": (
            "Учебный двуязычный (ишкашимско-русский) словарь-прототип. "
            "Данные собраны из научных источников по ишкашимскому языку."
        ),
        "pos_legend": {code: {"short": s, "full": f} for code, (s, f) in POS.items()},
        "field_legend": {
            "id": "стабильный уникальный ключ статьи",
            "lemma": "заголовочное слово (научная латинская транскрипция)",
            "lemma_lat": "упрощённая ASCII-латиница без диакритики (для поиска)",
            "lemma_cyr": "приблизительная кириллица (вспомогательная, не орфография)",
            "pos": "код части речи (для фильтра)",
            "pos_ru": "краткая помета части речи (для показа)",
            "pos_full": "полное название части речи",
            "domain": "тематическая группа",
            "translations_ru": "русские переводы (список)",
            "translations_en": "английские переводы (список)",
            "variants": "варианты написания / диалектные формы (список)",
            "examples": "примеры: список объектов {isk, ru}",
            "etymology": "происхождение / этимология",
            "comment": "лингвистический комментарий, диалектные пометы",
            "sources": "источники данных (список)",
        },
        "sources": [
            "G. A. Grierson. Ishkashmi, Zebaki and Yazghulami. London: Royal Asiatic Society, 1920.",
            "Т. Н. Пахалина. Ишкашимский язык. Очерк фонетики и грамматики, тексты и словарь. "
            "М.: Изд-во АН СССР, 1959.",
        ],
        "note": (
            "Прототип для учебного проекта. Транскрипция упрощена и унифицирована; "
            "у ишкашимского языка нет общепринятой письменности."
        ),
    }
    doc = {"meta": meta, "entries": records}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return doc


def write_csv(records, path):
    # Многозначные поля внутри ячейки разделяются вертикальной чертой " | ".
    # Примеры: "ишк. пример :: рус. перевод" через " | ".
    cols = [
        "id", "lemma", "lemma_lat", "lemma_cyr", "pos", "pos_ru", "domain",
        "translations_ru", "translations_en", "variants", "examples",
        "etymology", "comment", "sources",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            ex = " | ".join("%s :: %s" % (x["isk"], x["ru"]) for x in r["examples"])
            w.writerow([
                r["id"], r["lemma"], r["lemma_lat"], r["lemma_cyr"],
                r["pos"], r["pos_ru"], r["domain"],
                " | ".join(r["translations_ru"]),
                " | ".join(r["translations_en"]),
                " | ".join(r["variants"]),
                ex,
                r["etymology"], r["comment"],
                " | ".join(r["sources"]),
            ])


def write_sample(records, path, n=20):
    # Представительный тестовый набор для участников 2 и 3:
    # включает разные части речи, омонимы, многозначные слова,
    # слова с диакритикой и с пустыми примерами.
    wanted_lemmas = [
        "vrūd", "tsām", "kud", "vuz", "wek", "χān", "rēmuz",  # сущ. разных групп
        "frī", "šak", "kabūt",                                 # прил.
        "punz", "dah",                                         # числ.
        "az", "tu", "wa",                                      # мест.
        "dayuk", "suk", "wenuk",                               # гл.
        "agar", "na",                                          # служебные
    ]
    by_lemma = {r["lemma"]: r for r in records}
    sample = [by_lemma[l] for l in wanted_lemmas if l in by_lemma][:n]
    doc = {
        "meta": {
            "version": "1.0-sample",
            "entry_count": len(sample),
            "description": "Тестовый набор из 20 статей для ранней отладки поиска и интерфейса.",
        },
        "entries": sample,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return sample


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)

    records = build()
    write_json(records, os.path.join(data_dir, "dictionary.json"))
    write_csv(records, os.path.join(data_dir, "dictionary.csv"))
    sample = write_sample(records, os.path.join(data_dir, "dictionary.sample.json"))

    # краткая сводка
    by_pos = {}
    by_domain = {}
    for r in records:
        by_pos[r["pos"]] = by_pos.get(r["pos"], 0) + 1
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1

    print("Готово. Всего статей: %d" % len(records))
    print("Тестовый набор: %d статей" % len(sample))
    print("\nПо частям речи:")
    for k in sorted(by_pos):
        print("  %-7s %d" % (k, by_pos[k]))
    print("\nПо темам:")
    for k in sorted(by_domain):
        print("  %-13s %d" % (k, by_domain[k]))


if __name__ == "__main__":
    sys.exit(main())
