import pytest
import razminka_app


@pytest.fixture(autouse=True)
def reset_state(tmp_path, monkeypatch):
    monkeypatch.setattr(razminka_app, "FILE", str(tmp_path / "spisok.txt"))
    razminka_app.spisok = ["Кондратьев", "Ондина", "Максимова"]
    razminka_app.sohranit(razminka_app.FILE, razminka_app.spisok)
    yield


KLIENT = razminka_app.app.test_client()

def test_glavnaya():
    otvet = KLIENT.get("/")
    assert otvet.status_code == 200
    assert any(fam.encode("utf-8") in otvet.data for fam in razminka_app.spisok)


def test_udalit_get_ne_menyaet():
    dlina_do = len(razminka_app.spisok)
    KLIENT.get("/udalit/1")
    assert len(razminka_app.spisok) == dlina_do


def test_udalit_redirect():
    assert KLIENT.post("/udalit/1").status_code == 302