#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    return bool(year)  # Change this


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """


def main() -> None:
    """Ваш код здесь"""
#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"

DATE_PARTS_COUNT = 3
DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MIN_YEAR  = 1
MIN_MONTH = 1
MIN_DAY   = 1
MAX_MONTH = 12
FEBRUARY = 2

INCOME_ARGS_COUNT = 2
COST_ARGS_COUNT   = 3
STATS_ARGS_COUNT  = 1

def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """

    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """

    raw_date = maybe_dt.split("-")

    if len(raw_date) != DATE_PARTS_COUNT:
        return None

    for number in raw_date:
        if not number.isdigit():
            return None

    day   = int(raw_date[0])
    month = int(raw_date[1])
    year  = int(raw_date[2])

    if year < MIN_YEAR or month < MIN_MONTH or day < MIN_DAY or month > MAX_MONTH:
        return None

    max_day = DAYS_IN_MONTH[month]
    if month == FEBRUARY and is_leap_year(year):
        max_day += 1

    if day > max_day:
        return None

    return (day, month, year)


def get_amount(raw_amount: str) -> float | None:
    normal_amount = raw_amount.replace(",", ".")

    index = 0
    if normal_amount.startswith("-"):
        index += 1

    dot_found   = False
    digit_found = False

    for char in normal_amount[index:]:
        if char == ".":
            if dot_found:
                return None
            dot_found = True
        elif char.isdigit():
            digit_found = True
        else:
            return None

    if not digit_found:
        return None

    return float(normal_amount)


def is_le_date(date_lhs: tuple[int, int, int], date_rhs: tuple[int, int, int]) -> bool:
    return date_lhs[::-1] <= date_rhs[::-1]


def handle_income(args: list[str], incomes: list) -> str:
    if len(args) != INCOME_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    amount = get_amount(args[0])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(args[1])
    if date is None:
        return INCORRECT_DATE_MSG

    incomes.append((amount, date))
    return OP_SUCCESS_MSG


def handle_cost(args: list[str], costs: list) -> str:
    if len(args) != COST_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    category = args[0]

    amount = get_amount(args[1])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(args[2])
    if date is None:
        return INCORRECT_DATE_MSG

    costs.append((category, amount, date))
    return OP_SUCCESS_MSG


def calculate_incomes(incomes: list, date: tuple[int, int, int]) -> tuple[float, float]:
    total_income = 0.0
    month_income = 0.0

    for amount, op_date in incomes:
        if is_le_date(op_date, date):
            total_income += amount
            if op_date[2] == date[2] and op_date[1] == date[1]:
                month_income += amount

    return (total_income, month_income)


def calculate_costs(costs: list, date: tuple[int, int, int]) -> tuple[float, float, dict]:
    total_cost = 0.0
    month_cost = 0.0
    category_costs = {}

    for category, amount, op_date in costs:
        if is_le_date(op_date, date):
            total_cost += amount
            if op_date[2] == date[2] and op_date[1] == date[1]:
                month_cost += amount
                if category not in category_costs:
                    category_costs[category] = 0.0
                category_costs[category] += amount

    return (total_cost, month_cost, category_costs)


def handle_stats(args: list[str], incomes: list, costs: list) -> str:
    if len(args) != STATS_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    date = extract_date(args[0])
    if date is None:
        return INCORRECT_DATE_MSG

    total_income, month_income = calculate_incomes(incomes, date)
    total_cost, month_cost, category_costs = calculate_costs(costs, date)

    capital     = total_income  - total_cost
    month_diff = month_income - month_cost

    stats = f"Ваша статистика по состоянию на {args[0]}:\n"
    stats += f"Суммарный капитал: {capital:.2f} рублей\n"

    if month_diff >= 0:
        stats += f"В этом месяце прибыль составила {month_diff:.2f} рублей\n"
    else:
        stats += f"В этом месяце убыток составил {-month_diff:.2f} рублей\n"

    stats += f"Доходы: {month_income:.2f} рублей\n"
    stats += f"Расходы: {month_cost:.2f} рублей\n"
    stats += "\n"
    stats += "Детализация (категория: сумма):"

    sorted_category_costs = sorted(category_costs.keys())
    for index, category in enumerate(sorted_category_costs, 1):
        amount = category_costs[category]
        stats += f"\n{index}. {category}: {round(amount)}"

    return stats


def main() -> None:
    """Ваш код здесь"""

    incomes = []
    costs   = []

    while True:
        line = input()
        tokens = line.strip().split()

        if not tokens:
            print(UNKNOWN_COMMAND_MSG)
            continue

        command = tokens[0]
        args    = tokens[1:]

        match(command):
            case "income":
                result = handle_income(args, incomes)
            case "cost":
                result = handle_cost(args, costs)
            case "stats":
                result = handle_stats(args, incomes, costs)
            case _:
                result = UNKNOWN_COMMAND_MSG

        print(result)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
