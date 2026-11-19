import pytest
import app as prilozhenie


STROKI = (
    "s;иванов иван петрович;ivanov@mail.ru;89211112233;09с33\n"
    "t;петров пётр сергеевич;petrov@voenmeh.ru;89217654321;Кафедра И9\n"
    "s;сидорова анна;sidorova@mail.ru;89219998877;09с34\n"
    "плохая строка без всего\n"
)


POLYA = ("role", "fio", "email", "phone", "extra")

DANNYE = []
for line in STROKI.split("\n"):
    if line:
        DANNYE.append(dict(zip(POLYA, line.split(";"))))


@pytest.fixture
def klient(tmp_path):
    fayl = tmp_path / "anketa.txt"
    fayl.write_text(STROKI, encoding="utf-8")

    prilozhenie.FAYL = str(fayl)
    prilozhenie.zhurnal = prilozhenie.Registry()
    prilozhenie.zhurnal.load(str(fayl))
    prilozhenie.app.zhurnal = prilozhenie.zhurnal
    prilozhenie.app.config["TESTING"] = True
    return prilozhenie.app.test_client()


def test_glavnaya_stranica(klient):
    r = klient.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Иванов" in html
    assert "Петров" in html
    assert "Сидорова" in html


def test_anketa_ok(klient):
    r = klient.get("/anketi/1")
    assert r.status_code == 200
    assert "Иванов" in r.get_data(as_text=True)


def test_anketa_404(klient):
    assert klient.get("/anketi/99").status_code == 404


def test_forma_dobavit_otkryvaetsya(klient):
    r = klient.get("/dobavit")
    assert r.status_code == 200


def test_dobavit_ok(klient):
    r = klient.post("/dobavit", data=DANNYE[0])
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
    assert len(prilozhenie.zhurnal.accepted) == 4


def test_dobavit_bad(klient):
    old = len(prilozhenie.zhurnal.accepted)
    r = klient.post("/dobavit", data=DANNYE[3])
    assert r.status_code == 400
    assert len(prilozhenie.zhurnal.accepted) == old


def test_izmenit_forma_zapolnena(klient):
    r = klient.get("/anketi/1/izmenit")
    assert r.status_code == 200
    assert "Иванов" in r.get_data(as_text=True)


def test_izmenit_ok(klient):
    r = klient.post("/anketi/1/izmenit", data=DANNYE[1])
    assert r.status_code == 302
    assert prilozhenie.zhurnal.accepted[0].fio == "Петров Пётр Сергеевич"


def test_izmenit_bad(klient):
    old_fio = prilozhenie.zhurnal.accepted[0].fio
    old_len = len(prilozhenie.zhurnal.accepted)
    r = klient.post("/anketi/1/izmenit", data=DANNYE[3])
    assert r.status_code == 400
    assert prilozhenie.zhurnal.accepted[0].fio == old_fio
    assert len(prilozhenie.zhurnal.accepted) == old_len


def test_udalit_get_ne_udaalyaet(klient):
    old = len(prilozhenie.zhurnal.accepted)
    klient.get("/anketi/1/udalit")
    assert len(prilozhenie.zhurnal.accepted) == old


def test_udalit_post(klient):
    old = len(prilozhenie.zhurnal.accepted)
    r = klient.post("/anketi/1/udalit")
    assert r.headers["Location"].endswith("/")
    assert len(prilozhenie.zhurnal.accepted) == old - 1


def test_udalit_sdvig(klient):
    klient.post("/anketi/1/udalit")
    assert prilozhenie.zhurnal.accepted[0].fio == "Петров Пётр Сергеевич"


def test_izmenit_v_fayle(klient):
    klient.post("/anketi/1/izmenit", data=DANNYE[1])
    with open(prilozhenie.FAYL, encoding="utf-8") as f:
        text = f.read()
    assert text.count("Петров Пётр Сергеевич") == 2


def test_udalit_v_fayle(klient):
    klient.post("/anketi/1/udalit")
    with open(prilozhenie.FAYL, encoding="utf-8") as f:
        text = f.read()
    assert "Иванов Иван Петрович" not in text


def test_brak_ostalsya(klient):
    klient.post("/dobavit", data=DANNYE[0])
    with open(prilozhenie.FAYL, encoding="utf-8") as f:
        text = f.read()
    assert "плохая строка без всего" in text


def test_api_anketi(klient):
    r = klient.get("/api/anketi")
    assert len(r.get_json()) == 3


def test_api_anketi_rol_s(klient):
    r = klient.get("/api/anketi?rol=s")
    assert len(r.get_json()) == 2


def test_api_brak(klient):
    data = klient.get("/api/brak").get_json()
    assert len(data) == 1
    assert "плохая строка без всего" in data[0]["Анкета"]


def test_api_delete(klient):
    r = klient.delete("/api/anketi/1")
    assert r.status_code == 200
    assert len(prilozhenie.zhurnal.accepted) == 2


def test_flash_odin_raz(klient):
    klient.post("/dobavit", data=DANNYE[0])
    r1 = klient.get("/")
    assert "добавлена" in r1.get_data(as_text=True)
    r2 = klient.get("/")
    assert "добавлена" not in r2.get_data(as_text=True)


def test_izmenit_0(klient):
    assert klient.get("/anketi/0/izmenit").status_code == 404


def test_izmenit_99(klient):
    assert klient.get("/anketi/99/izmenit").status_code == 404


def test_udalit_0(klient):
    assert klient.get("/anketi/0/udalit").status_code == 404


def test_udalit_99(klient):
    assert klient.get("/anketi/99/udalit").status_code == 404


def test_pustoy_zhurnal(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    prilozhenie.FAYL = str(f)
    prilozhenie.zhurnal = prilozhenie.Registry()
    prilozhenie.zhurnal.load(str(f))
    prilozhenie.app.zhurnal = prilozhenie.zhurnal
    prilozhenie.app.config["TESTING"] = True
    c = prilozhenie.app.test_client()
    assert c.get("/").status_code == 200
    assert c.get("/anketi/1").status_code == 404
    assert c.get("/api/anketi").get_json() == []