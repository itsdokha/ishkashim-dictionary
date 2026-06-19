# -*- coding: utf-8 -*-
"""
validate_data.py
================

Проверка целостности данных словаря. Запускать после build_dictionary.py.

Проверяется:
  * data/dictionary.json — корректный JSON в кодировке UTF-8;
  * у каждой статьи есть обязательные поля и они не пусты;
  * id уникальны;
  * pos входит в допустимый список;
  * число строк в CSV совпадает с числом статей в JSON;
  * у каждой статьи есть хотя бы один русский перевод.

Запуск:
    python3 scripts/validate_data.py
Код возврата 0 — всё в порядке, 1 — найдены ошибки.
"""

import csv
import json
import os
import sys

REQUIRED = ["id", "lemma", "lemma_lat", "pos", "pos_ru", "translations_ru"]
ALLOWED_POS = {"noun", "verb", "adj", "adv", "num", "pron",
               "prep", "postp", "conj", "part", "interj"}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jpath = os.path.join(root, "data", "dictionary.json")
    cpath = os.path.join(root, "data", "dictionary.csv")

    errors = []
    warnings = []

    with open(jpath, encoding="utf-8") as f:
        doc = json.load(f)
    entries = doc["entries"]

    ids = set()
    homonyms = {}
    for e in entries:
        tag = e.get("id", "?")
        for field in REQUIRED:
            if not e.get(field):
                errors.append("%s: пустое обязательное поле %r" % (tag, field))
        if e["id"] in ids:
            errors.append("%s: повторяющийся id" % tag)
        ids.add(e["id"])
        if e["pos"] not in ALLOWED_POS:
            errors.append("%s: недопустимая часть речи %r" % (tag, e["pos"]))
        if not e.get("translations_ru"):
            errors.append("%s (%s): нет русского перевода" % (tag, e.get("lemma")))
        # примеры должны иметь оба поля
        for ex in e.get("examples", []):
            if not ex.get("isk") or not ex.get("ru"):
                errors.append("%s: пример без isk/ru" % tag)
        homonyms.setdefault(e["lemma"], []).append(e["id"])

    # омонимы — не ошибка, но полезно знать (для участника 2: поиск вернёт несколько статей)
    for lemma, lst in homonyms.items():
        if len(lst) > 1:
            warnings.append("омонимы для %r: %s" % (lemma, ", ".join(lst)))

    # сверка с CSV
    with open(cpath, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    csv_data_rows = len(rows) - 1  # минус заголовок
    if csv_data_rows != len(entries):
        errors.append("CSV: строк данных %d, а статей в JSON %d" % (csv_data_rows, len(entries)))

    print("Статей в JSON: %d" % len(entries))
    print("Строк данных в CSV: %d" % csv_data_rows)
    print("meta.entry_count: %d" % doc["meta"]["entry_count"])

    if warnings:
        print("\nПредупреждения:")
        for w in warnings:
            print("  - " + w)

    if errors:
        print("\nОШИБКИ (%d):" % len(errors))
        for e in errors:
            print("  ! " + e)
        return 1

    print("\nOK: данные корректны.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
