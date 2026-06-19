# data/ — данные словаря

| Файл | Назначение |
|---|---|
| `dictionary.json` | **основной формат**, источник правды для кода (участники 2 и 3) |
| `dictionary.sample.json` | тестовый набор из 20 статей (та же структура) |
| `dictionary.csv` | человекочитаемый экспорт (для просмотра в Excel) |

* Кодировка — **UTF-8**.
* **В коде используйте JSON.** CSV — только для просмотра глазами.
* Файлы порождаются скриптом `../scripts/build_dictionary.py` — **руками не правьте**.
* Полное описание полей — в `../docs/data_format.md`.

Быстрый просмотр статьи:

```bash
python3 -c "import json;d=json.load(open('dictionary.json',encoding='utf-8'));print(json.dumps(d['entries'][12],ensure_ascii=False,indent=2))"
```
