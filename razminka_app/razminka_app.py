from flask import Flask, render_template, request, redirect, url_for, abort, flash


app = Flask(__name__, template_folder="templates/razminka_app")
app.secret_key = "345018c2bf1f1d4eb6829700dc6daffd6cd0a3f0"


DEFAULT = ["Кондратьев", "Ондина", "Максимова"]
FILE = "spisok.txt"


def sohranit(imya, spisok):
    """Записывает весь список в файл по одной фамилии на строку"""
    with open(imya, "w", encoding="utf-8") as f:
        for i in spisok:
            f.write(str(i) + "\n")


def zagruzit(imya):
    """Читает файл"""
    spisok = []
    try:
        with open(imya, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    spisok.append(line.replace("\n", ""))
    except FileNotFoundError:
        return DEFAULT.copy()
    return spisok


spisok = zagruzit(FILE)

@app.route('/')
def index():
    """Страница со списком фамилий, у каждой ссылка «изменить» и «удалить»"""
    return render_template('index.html', spisok=list(enumerate(spisok, start=1))), 200


@app.route('/izmenit/<int:nomer>', methods=["GET", "POST"])
def izmenit(nomer):
    """Изменяет фамилию в списке"""
    if not(1 <= nomer <= len(spisok)):
        abort(404, description="Такого номера нет")

    if request.method == "POST":
        novaya = request.form.get("novaya", "").strip()
        if novaya:
            spisok[nomer-1] = novaya
            sohranit(FILE, spisok)
            flash("Фамилия изменена", category="success")
            return redirect(url_for("index")), 302
        abort(400, description="Вы ничего не ввели")
    return render_template("izmenit.html", nomer=nomer, name=spisok[nomer-1]), 200


@app.route("/udalit/<int:nomer>", methods=["GET", "POST"])
def udalit(nomer):
    """Удаляет фамилию из списка"""
    if not (1 <= nomer <= len(spisok)):
        abort(404, description="Такого номера нет")

    if request.method == "POST":
        spisok.pop(nomer-1)
        sohranit(FILE, spisok)
        flash("Фамилия удалена", category="success")
        return redirect(url_for("index")), 302
    return render_template("udalit.html", name=spisok[nomer-1]), 200


if __name__ == "__main__":
    app.run(debug=True)




