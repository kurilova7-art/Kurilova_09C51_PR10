"""
Локальный сервер анкет

Ручки:
    GET  /                        таблицы принятых анкет
    GET  /anketi/<int:nomer>      данные об анкете по номеру
    GET  /gruppa/<title>          таблица анкет по группам/кафедрам
    GET  /statistika              сводки по ролям, группам и отклоненным анкетам
    GET  /dobavit                 форма добавления анкеты
    POST /dobavit                 принимает форму и добавляет к принятым анкетам
    GET  /anketi/<номер>/izmenit  форма, заполненная данными этой анкеты
    POST /anketi/<номер>/izmenit  проверка и замена; при удаче - перенаправление на страницу анкеты
    GET  /anketi/<номер>/udalit   страница подтверждения с ФИО и кнопкой
    POST /anketi/<номер>/udalit   удаление, сохранение и перенаправление на список

Ручки с api, возвращают в JSON:
    GET    /api/anketi              все анкеты студентов с параметром rol=s, либо все анкеты
    GET    /api/anketi/<int:nomer>  анкета по номеру
    GET    /api/statistika          таблица анкет по группам/кафедрам
    GET    /api/brak                отклоненные анкеты
    POST   /api/anketi              принимает анкету
    DELETE /api/anketi/<номер>      удаление для программы
"""

from flask import Flask, current_app, render_template, abort, request, flash, url_for, redirect, jsonify
from werkzeug.exceptions import HTTPException
import os
from dotenv import load_dotenv

from registry import Registry
from people import Student, Teacher, AnketaError


load_dotenv()
app = Flask(__name__, template_folder="templates/anketi_app")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
FAYL = "anketa.txt"


zhurnal = Registry()
if not zhurnal.load(FAYL):
    print("ВНИМАНИЕ: файл не найден, журнал пуст")

app.zhurnal = zhurnal
def sohranit():
    current_app.zhurnal.save_all(FAYL)


@app.errorhandler(HTTPException)
def any_error(e):
    """Принимает любую ошибку и возвращает страницу с этой ошибкой"""
    if e.code >= 500:
        message = "Ошибка сервера"
        print("ОШИБКА:", e.code, e.description)
    else:
        message = e.description

    return render_template("error.html", message=message), e.code


@app.route("/")
def index():
    """Возвращает главную страницу с таблицей принятых анкет"""
    accepted = []
    for i, p in enumerate(current_app.zhurnal.accepted, 1):
        accepted.append([str(i), p.fio, p.role(), p.extra(), p.masked_phone()])
    return render_template("index.html", accepted=accepted, ok=len(current_app.zhurnal.accepted), error=len(current_app.zhurnal.rejected)), 200


@app.route("/anketi/<int:nomer>")
def anketa_by_nomer(nomer):
    """Возвращает страницу с анкетой по номеру"""
    accepted = current_app.zhurnal.accepted
    if not 1 <= nomer <= len(accepted):
        abort(404, description="Анкета с таким номером не найдена")
    person = accepted[nomer - 1]
    return render_template("anketa_by_nomer.html", nomer=nomer, person=person), 200


@app.route("/gruppa/<title>")
def gruppa_by_title(title):
    """Возвращает список анкет по группам/кафедрам"""
    key = title.strip().casefold()
    persons = []
    for p in current_app.zhurnal.accepted:
        if p.extra().strip().casefold() == key:
            persons.append(p)
    return render_template("gruppa_by_title.html", title=title, persons=persons), 200


@app.route("/statistika")
def statistika():
    """Возвращает сводку по ролям, группам и таблицу отклоненных анкет"""
    return render_template("statistika.html", role_stats=current_app.zhurnal.role_stats(),
                           group_stats=current_app.zhurnal.group_stats(), rejected=current_app.zhurnal.rejected), 200


@app.route("/dobavit")
def dobavit_get():
    """Возвращает форму добавления анкеты"""
    return render_template("forma.html", zagolovok="Добавить анкету", deystvie=url_for('dobavit_post')), 200


@app.route("/dobavit", methods=["POST"])
def dobavit_post():
    """Принимает форму и добавляет к принятым анкетам"""
    role = request.form.get("role")
    fio = request.form.get("fio")
    email = request.form.get("email")
    phone = request.form.get("phone")
    extra = request.form.get("extra")

    if not fio or not email or not phone or not extra:
        flash("Заполните все поля", "error")
        return render_template("forma.html", zagolovok="Добавить анкету",
                               role=role, fio=fio, email=email,
                               phone=phone, extra=extra, deystvie=url_for('dobavit_post')), 400

    try:
        if role == "s":
            person = Student(fio, email, phone, extra)
        elif role == "t":
            person = Teacher(fio, email, phone, extra)
        else:
            raise AnketaError(f"Неизвестный тип: {role or '—'}")
    except AnketaError as e:
        flash(str(e), "error")
        return render_template("forma.html", zagolovok="Добавить анкету", role=role,
                               fio=fio, email=email, phone=phone, extra=extra, deystvie=url_for('dobavit_post')), 400

    current_app.zhurnal.add(person)
    sohranit()
    flash(f"Анкета «{person.fio}» добавлена", "success")
    return redirect(url_for("index")), 302


@app.route("/anketi/<int:nomer>/izmenit")
def izmenit_get(nomer):
    """Возвращает форму на изменение с заполненными данными"""
    person = current_app.zhurnal.poluchit(nomer)
    if person is None:
        abort(404, description="Анкета с таким номером не найдена")

    return render_template("forma.html", zagolovok=f"Изменить анкету №{nomer}",
        nomer=nomer, role=person.TIP, fio=person.fio, email=person.email,
        phone=person.phone, extra=person.extra(), deystvie=url_for("izmenit_post", nomer=nomer)), 200


@app.route("/anketi/<int:nomer>/izmenit", methods=["POST"])
def izmenit_post(nomer):
    """Принимает данные из формы и заменяет анкету по номеру"""
    person = current_app.zhurnal.poluchit(nomer)
    if person is None:
        abort(404, description="Анкета с таким номером не найдена")

    role = request.form.get("role")
    fio = request.form.get("fio")
    email = request.form.get("email")
    phone = request.form.get("phone")
    extra = request.form.get("extra")

    if not fio or not email or not phone or not extra:
        flash("Заполните все поля", "error")
        return render_template("forma.html", zagolovok=f"Изменить анкету №{nomer}",
                               deystvie=url_for("izmenit_post", nomer=nomer),
                               role=role, fio=fio, email=email,
                               phone=phone, extra=extra), 400

    try:
        if role == "s":
            person = Student(fio, email, phone, extra)
        elif role == "t":
            person = Teacher(fio, email, phone, extra)
        else:
            raise AnketaError(f"Неизвестный тип: {role or '—'}")
    except AnketaError as e:
        flash(str(e), "error")
        return render_template("forma.html", zagolovok=f"Изменить анкету №{nomer}", role=role,
                               deystvie=url_for("izmenit_post", nomer=nomer),
                               fio=fio, email=email, phone=phone, extra=extra), 400

    current_app.zhurnal.zamenit(nomer, person)
    sohranit()
    flash(f"Анкета №{nomer} изменена", "success")
    return redirect(url_for("anketa_by_nomer", nomer=nomer)), 302


@app.route("/anketi/<int:nomer>/udalit")
def udalit_get(nomer):
    """Возвращает страницу подтверждения удаления с ФИО и кнопкой"""
    person = current_app.zhurnal.poluchit(nomer)
    if person is None:
        abort(404, description="Анкета с таким номером не найдена")

    return render_template("udalit.html", nomer=nomer, fio=person.fio)


@app.route("/anketi/<int:nomer>/udalit", methods=["POST"])
def udalit_post(nomer):
    """Удаляет анкету"""
    anketa = current_app.zhurnal.udalit(nomer)
    if anketa is None:
        abort(404, description="Анкета с таким номером не найдена")
    sohranit()
    flash(f"Анкета «{anketa.fio}» удалена", "success")
    return redirect(url_for("index")), 303


@app.route("/api/anketi")
def api_anketi():
    """Возвращает в JSON все анкеты студентов с параметром rol=s, либо все анкеты"""
    rol = request.args.get("rol", "").strip().lower()
    result = []

    if not rol:
        for i, p in enumerate(current_app.zhurnal.accepted, 1):
            result.append({
                "№": i,
                "ФИО": p.fio,
                "Роль": p.role(),
                "Почта": p.email,
                "Телефон": p.masked_phone(),
                "Группа/Кафедра": p.extra(),
            })
        return jsonify(result), 200

    for i, p in enumerate(current_app.zhurnal.accepted, 1):
        if rol == "s" and p.role() == "Студент":
            result.append({
                "№": i,
                "ФИО": p.fio,
                "Роль": p.role(),
                "Почта": p.email,
                "Телефон": p.masked_phone(),
                "Группа/Кафедра": p.extra(),
            })
    return jsonify(result), 200


@app.route("/api/anketi/<int:nomer>", methods=["DELETE"])
def anketi_delete(nomer):
    """Удаляет анкету для программы и возвращает ее в JSON"""
    anketa = current_app.zhurnal.udalit(nomer)
    if anketa is None:
        return jsonify({"Ошибка": "Анкета не найдена"}), 404

    sohranit()
    return jsonify({
        "№": nomer,
        "ФИО": anketa.fio,
        "Роль": anketa.role(),
        "Почта": anketa.email,
        "Телефон": anketa.masked_phone(),
        "Группа/Кафедра": anketa.extra()}), 200


@app.route("/api/anketi/<int:nomer>")
def api_anketi_by_nomer(nomer):
    """Возвращает одну анкету в JSON по номеру"""
    accepted = current_app.zhurnal.accepted
    if not 1 <= nomer <= len(accepted):
        return jsonify({"Ошибка": "Анкета не найдена"}), 404
    person = accepted[nomer - 1]

    result = {
        "№": nomer,
        "ФИО": person.fio,
        "Роль": person.role(),
        "Почта": person.email,
        "Телефон": person.masked_phone(),
        "Группа/Кафедра": person.extra(),
    }
    return jsonify(result), 200


@app.route("/api/statistika")
def api_statistika():
    """Возвращает в JSON сводки по ролям и группам и сколько принято и отклонено"""
    role_stats = []
    for role, count in current_app.zhurnal.role_stats().items():
        role_stats.append({role: count})

    group_stats = []
    for group, count in current_app.zhurnal.group_stats().items():
        group_stats.append({group: count})

    stat = {
        "Принято": len(current_app.zhurnal.accepted),
        "Отклонено": len(current_app.zhurnal.rejected),
    }

    return jsonify({"По ролям": role_stats, "По группам": group_stats, "Итоги": stat,}), 200


@app.route("/api/brak")
def api_brak():
    """Возвращает отклоненные анкеты в JSON"""
    rejected = []
    for n, raw, reason in current_app.zhurnal.rejected:
        rejected.append({"№": n, "Анкета": raw, "Причина": reason})

    if not rejected:
        return jsonify([]), 200
    return jsonify(rejected), 200


@app.route("/api/anketi", methods=["POST"])
def api_anketi_post():
    """Принимает анкету в JSON, отвечает кодом 201"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"Ошибка": "Передан не JSON"}), 400

    if not data:
        return jsonify({"error": "Анкета пустая"}), 400

    required = ("tip", "fio", "email", "phone", "extra")
    missing = []
    for k in required:
        if not data.get(k):
            missing.append(k)

    if missing:
        return jsonify({"Ошибка": f"Не хватает полей: {', '.join(missing)}"}), 400

    try:
        if data["tip"] == "s":
            person = Student(data["fio"], data["email"], data["phone"], data["extra"])
        elif data["tip"] == "t":
            person = Teacher(data["fio"], data["email"], data["phone"], data["extra"])
        else:
            raise AnketaError(f"Неизвестный тип: {data['tip']}")
    except AnketaError as e:
        return jsonify({"Ошибка": str(e)}), 400

    result = {
        "№": len(current_app.zhurnal.accepted) + 1,
        "ФИО": person.fio,
        "Роль": person.role(),
        "Почта": person.email,
        "Телефон": person.masked_phone(),
        "Группа/Кафедра": person.extra(),
    }

    current_app.zhurnal.add(person)
    sohranit()
    return jsonify(result), 201


if __name__ == "__main__":
    app.run(debug=True)