"""
Тесты для ручек api_anketi, api_anketi_by_nomer, api_statistika, api_brak, api_anketi_post
Для запуска необходим запущенный сервер
"""

import pytest
import requests


BASE = "http://127.0.0.1:5000"


def test_list_anketi_filter_students():
    r = requests.get(f"{BASE}/api/anketi", params={"rol": "s"}, timeout=3)
    assert r.status_code == 200
    for item in r.json():
        assert item["Роль"] == "Студент"


def test_list_anketi_no_filter():
    r = requests.get(f"{BASE}/api/anketi", timeout=3)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_anketa_by_nomer_ok():
    r = requests.get(f"{BASE}/api/anketi/1", timeout=3)
    assert r.status_code == 200
    data = r.json()
    for key in ("№", "ФИО", "Роль", "Почта", "Телефон", "Группа/Кафедра"):
        assert key in data


def test_anketa_by_nomer_404():
    r = requests.get(f"{BASE}/api/anketi/99999", timeout=3)
    assert r.status_code == 404
    assert r.json() == {"Ошибка": "Анкета не найдена"}


def test_statistika():
    r = requests.get(f"{BASE}/api/statistika", timeout=3)
    assert r.status_code == 200


def test_brak():
    r = requests.get(f"{BASE}/api/brak", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        assert item.keys() == {"№", "Анкета", "Причина"}


@pytest.mark.parametrize("value, expected", [
    ("ФИО", "Иванов Иван"),
    ("Роль", "Студент"),
    ("Телефон", "+7 (911) ***-**-55"),
    ("Группа/Кафедра", "10а12"),
])
def test_post_student_ok(value, expected):
    payload = {
        "tip": "s",
        "fio": "Иванов Иван",
        "email": "ivanov@example.com",
        "phone": "89113334455",
        "extra": "10а12",
    }
    r = requests.post(f"{BASE}/api/anketi", json=payload, timeout=3)

    data = r.json()
    assert r.status_code == 201, f"{r.status_code}: {r.text}"
    assert data[value] == expected


def test_post_empty_body():
    r = requests.post(f"{BASE}/api/anketi", json={}, timeout=3)
    assert r.status_code == 400
    assert r.json() == {"error": "Анкета пустая"}