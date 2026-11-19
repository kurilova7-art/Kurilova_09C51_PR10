from people import AnketaError, Student, Teacher, Person


class Registry:
    """Принятые объекты и отклонённые строки с причинами"""
    def __init__(self) -> None:
        self.accepted = []
        self.rejected = []

    def __len__(self) -> int:
        """Возвращает число принятых анкет"""
        return len(self.accepted)

    def __iter__(self):
        """Перебор через цикл for"""
        return iter(self.accepted)

    def add(self, person: Student | Teacher) -> None:
        """Добавляет анкету в принятые объекты"""
        self.accepted.append(person)

    def load(self, filename: str) -> bool:
        """Читает файл, возвращает False если файла нет"""
        try:
            with open(filename, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self.add(self._parse_line(line))
                    except AnketaError as e:
                        self.rejected.append((n, line, str(e)))
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def _parse_line(line: str) -> Student | Teacher:
        """Разбирает строку и создаёт Student или Teacher"""
        parts = line.split(";")
        if len(parts) != 5:
            raise AnketaError(f"Полей не 5, передано {len(parts)}")

        kind, fio, email, phone, extra = (p.strip() for p in parts)
        kind = kind.lower()

        if kind in ("s", "student", "студент"):
            return Student(fio, email, phone, extra)
        if kind in ("t", "teacher", "преподаватель"):
            return Teacher(fio, email, phone, extra)
        raise AnketaError(f"Неизвестный тип: {kind}")

    def role_stats(self) -> dict:
        """Возвращает словарь: роль и число"""
        result = {}
        for p in self.accepted:
            result[p.role()] = result.get(p.role(), 0) + 1
        return result

    def group_stats(self) -> dict:
        """Возвращает словарь: группа, число. Только для студентов"""
        result = {}
        for p in self.accepted:
            if isinstance(p, Student):
                result[p.extra()] = result.get(p.extra(), 0) + 1
        return result

    def save_in_accepted(self) -> None:
        """Сохраняет правильные строки в файл ok.txt"""
        with open("ok.txt", "w", encoding="utf-8") as f:
            for p in self.accepted:
                f.write(f"{p.role()};{p.fio};{p.email};{p.phone};{p.extra()}\n")

    def save_in_rejected(self) -> None:
        """Сохраняет бракованные строки в файл errors.txt с причиной брака"""
        with open("errors.txt", "w", encoding="utf-8") as f:
            for n, raw, reason in self.rejected:
                f.write(f"{n}: {reason} -> {raw}\n")

    @staticmethod
    def ask_file():
        """Спрашивает файл у пользователя"""
        while True:
            name = input("Файл: ").strip()
            if not name:
                return "anketa.txt"
            if name.lower().endswith(".txt"):
                return name
            print("Нужно расширение .txt")

    def poluchit(self, nomer):
        """Возвращает анкету по номеру, считая с единицы, или None"""
        if 0 < nomer <= len(self.accepted):
            return self.accepted[nomer - 1]
        return None

    def zamenit(self, nomer, person):
        """Заменяет анкету, возвращает True или False"""
        if 0 < nomer <= len(self.accepted):
            self.accepted[nomer - 1] = person
            return True
        return False

    def udalit(self, nomer):
        """Убирает анкету и возвращает её, или None"""
        if 0 < nomer <= len(self.accepted):
            return self.accepted.pop(nomer - 1)
        return None

    def save_all(self, filename):
        """Пишет принятые анкеты через v_stroku, затем брак"""
        with open(filename, "w", encoding="utf-8") as f:
            for p in self.accepted:
                f.write(p.v_stroku() + "\n")
            for _n, raw, _reason in self.rejected:
                f.write(raw + "\n")



if __name__ == "__main__":
    student = Student("белов максим", "belov@yandex.ru", "89113334455", "10а12")
    registry = Registry()

    registry.add(student)
    assert registry.accepted == [student]


