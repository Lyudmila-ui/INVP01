"""
INVP01 — конверсионный сайт «AI-дайджест для новичков».

Запуск из папки проекта (после установки зависимостей):

    python app.py

Сайт откроется на http://127.0.0.1:4721
"""

import re
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from data import MATERIALS, TAGS

app = Flask(__name__)

# Секрет нужен, чтобы Flask мог показать одноразовое сообщение после формы.
# Для учёбы ключ лежит прямо здесь. В настоящем проекте его прячут в переменную окружения.
app.secret_key = "invp01-local-learning-key"

# Адреса подписчиков дописываются в этот файл рядом с app.py.
# Файл в .gitignore: учебные почты не должны попадать в репозиторий.
BASE_DIR = Path(__file__).resolve().parent
SUBSCRIBERS_FILE = BASE_DIR / "subscribers.txt"

# Простая проверка почты: что-то @ что-то . что-то, без пробелов.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def validate_materials():
    """Останавливаем запуск, если карточка заполнена криво."""
    seen_slugs = []
    required = [
        "slug",
        "number",
        "title",
        "tag",
        "minutes",
        "teaser",
        "lead",
        "sections",
        "remember",
    ]

    for item in MATERIALS:
        slug = item.get("slug", "без slug")
        for field in required:
            if field not in item or item[field] in ("", None, []):
                raise ValueError(f"У материала «{slug}» пустое поле {field}")

        if not SLUG_RE.match(item["slug"]):
            raise ValueError(
                f"Slug «{item['slug']}» можно писать только латиницей, цифрами и дефисом"
            )
        if item["slug"] in seen_slugs:
            raise ValueError(f"Slug «{item['slug']}» повторяется. Он должен быть уникальным.")
        seen_slugs.append(item["slug"])

        if item["tag"] not in TAGS:
            raise ValueError(
                f"Тема «{item['tag']}» не описана в TAGS. Добавьте её в data.py."
            )
        if not isinstance(item["number"], int) or not isinstance(item["minutes"], int):
            raise ValueError(f"У «{slug}» номер и минуты должны быть целыми числами")
        if item["minutes"] <= 0:
            raise ValueError(f"У «{slug}» время чтения должно быть больше нуля")

        for section in item["sections"]:
            if not section.get("heading") or not section.get("paragraphs"):
                raise ValueError(f"В «{slug}» есть раздел без заголовка или абзацев")

        example = item.get("example")
        if example is not None and ("bad" not in example or "good" not in example):
            raise ValueError(f"В «{slug}» пример должен содержать поля bad и good")


def find_material(slug):
    """Ищем материал по куску адреса. Если такого нет — вернём None."""
    for item in MATERIALS:
        if item["slug"] == slug:
            return item
    return None


def related_materials(current):
    """Две следующие карточки. После последней снова идём с начала выпуска."""
    start = MATERIALS.index(current)
    result = []
    for step in range(1, len(MATERIALS)):
        # % — остаток от деления. Он помогает после последней карточки вернуться к первой.
        result.append(MATERIALS[(start + step) % len(MATERIALS)])
        if len(result) == 2:
            break
    return result


def count_materials_by_tag():
    """Сколько карточек в каждой теме. Число видно на кнопке фильтра."""
    counts = {}
    for tag in TAGS:
        total = 0
        for item in MATERIALS:
            if item["tag"] == tag:
                total += 1
        counts[tag] = total
    return counts


def safe_next(raw_path):
    """После формы возвращаем человека только на страницу этого сайта."""
    if not raw_path or not raw_path.startswith("/"):
        return url_for("index")
    if raw_path.startswith("//") or "\\" in raw_path:
        return url_for("index")
    return raw_path


def read_subscribers():
    if not SUBSCRIBERS_FILE.exists():
        return set()
    text = SUBSCRIBERS_FILE.read_text(encoding="utf-8")
    return {line.strip() for line in text.splitlines() if line.strip()}


def save_subscriber(email):
    with SUBSCRIBERS_FILE.open("a", encoding="utf-8") as file:
        file.write(email + "\n")


validate_materials()


@app.route("/")
def index():
    """Главная: обещание, форма и сетка карточек."""
    return render_template(
        "index.html",
        materials=MATERIALS,
        tags=TAGS,
        counts=count_materials_by_tag(),
        featured=MATERIALS[0],
    )


@app.route("/material/<slug>")
def material(slug):
    """Страница одного разбора. Сюда ведёт кнопка «Открыть материал»."""
    item = find_material(slug)
    if item is None:
        abort(404)
    return render_template(
        "material.html",
        material=item,
        related=related_materials(item),
        tags=TAGS,
    )


@app.route("/subscribe", methods=["GET", "POST"])
def subscribe():
    """Сохраняем почту из формы. Письма в учебном проекте никуда не отправляются."""
    if request.method == "GET":
        return redirect(url_for("index") + "#subscribe")

    email = request.form.get("email", "").strip().lower()
    next_path = safe_next(request.form.get("next", "/"))

    if not EMAIL_RE.match(email) or len(email) > 120:
        flash("Похоже, в адресе опечатка. Проверьте его и попробуйте ещё раз.", "error")
        return redirect(next_path)

    try:
        already = read_subscribers()
        if email in already:
            flash("Этот адрес уже в списке. До встречи в понедельник.", "success")
            return redirect(next_path)
        save_subscriber(email)
    except OSError:
        flash("Не получилось записать адрес. Проверьте права на папку проекта.", "error")
        return redirect(next_path)

    flash(
        "Адрес сохранён. В этом учебном проекте он записан в файл subscribers.txt, письма пока не отправляются.",
        "success",
    )
    return redirect(next_path)


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    # debug=True перезапускает сайт, когда вы сохраняете файлы.
    # use_debugger=False выключает страницу отладчика: она опасна, если сайт открыт не только вам.
    # Если порт 4721 занят, поменяйте число ниже.
    app.run(host="0.0.0.0", port=4721, debug=True, use_debugger=False)
