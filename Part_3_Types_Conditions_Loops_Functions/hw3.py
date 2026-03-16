#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
DAYS_IN_MONTH = (
    0, 31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31,
)
MIN_YEAR = 1
MIN_MONTH = 1
MIN_DAY = 1
MAX_MONTH = 12
FEBRUARY = 2

INCOME_ARGS_COUNT = 2
COST_ARGS_COUNT = 3
STATS_ARGS_COUNT = 1

Date = tuple[int, int, int]
Income = tuple[float, Date]
Cost = tuple[str, float, Date]
CostSummary = tuple[float, float, dict[str, float]]


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    by_four = year % 4 == 0
    not_by_hundred = year % 100 != 0
    by_four_hundred = year % 400 == 0

    return (by_four and not_by_hundred) or by_four_hundred


def is_valid_date(date: Date) -> bool:
    day = date[0]
    month = date[1]
    year = date[2]

    if year < MIN_YEAR or month < MIN_MONTH:
        return False
    if day < MIN_DAY or month > MAX_MONTH:
        return False

    max_day = DAYS_IN_MONTH[month]
    if month == FEBRUARY and is_leap_year(year):
        max_day += 1

    return day <= max_day


def extract_date(maybe_dt: str) -> Date | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    raw_date = maybe_dt.split("-")

    if len(raw_date) != DATE_PARTS_COUNT:
        return None

    numbers = []
    for number in raw_date:
        if not number.isdigit():
            return None
        numbers.append(int(number))

    date: Date = (numbers[0], numbers[1], numbers[2])

    if not is_valid_date(date):
        return None

    return date


def get_amount(raw_amount: str) -> float | None:
    normal_amount = raw_amount.replace(",", ".")

    index = 0
    if normal_amount.startswith("-"):
        index += 1

    dot_found = False
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


def is_le_date(date_lhs: Date, date_rhs: Date) -> bool:
    return tuple(reversed(date_lhs)) <= tuple(reversed(date_rhs))


def is_same_month(date_a: Date, date_b: Date) -> bool:
    same_year = date_a[2] == date_b[2]
    same_mo = date_a[1] == date_b[1]

    return same_year and same_mo


def handle_income(args: list[str], incomes: list[Income]) -> str:
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


def handle_cost(args: list[str], costs: list[Cost]) -> str:
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


def calculate_incomes(incomes: list[Income], date: Date) -> tuple[float, float]:
    total = float(0)
    monthly = float(0)

    for amount, op_date in incomes:
        if is_le_date(op_date, date):
            total += amount
            if is_same_month(op_date, date):
                monthly += amount

    return (total, monthly)


def calculate_total_cost(costs: list[Cost], date: Date) -> float:
    total = float(0)

    for _, amount, op_date in costs:
        if is_le_date(op_date, date):
            total += amount

    return total


def add_category_cost(
    categories: dict[str, float],
    category: str,
    amount: float,
) -> None:
    prev = categories.get(category, float(0))
    categories[category] = prev + amount


def calculate_month_costs(
    costs: list[Cost],
    date: Date,
) -> tuple[float, dict[str, float]]:
    monthly = float(0)
    categories: dict[str, float] = {}

    for category, amount, op_date in costs:
        if is_le_date(op_date, date) and is_same_month(op_date, date):
            monthly += amount
            add_category_cost(categories, category, amount)

    return (monthly, categories)


def calculate_costs(costs: list[Cost], date: Date) -> CostSummary:
    total = calculate_total_cost(costs, date)
    month_data = calculate_month_costs(costs, date)

    return (total, month_data[0], month_data[1])


def format_month_line(month_diff: float) -> str:
    if month_diff >= 0:
        return f"B этом месяце прибыль составила {month_diff:.2f} рублей"

    loss = -month_diff
    return f"B этом месяце убыток составил {loss:.2f} рублей"


def format_category_details(category_costs: dict[str, float]) -> str:
    lines = ["Детализация (категория: сумма):"]

    for index, category in enumerate(sorted(category_costs.keys()), 1):
        lines.append(f"{index}. {category}: {round(category_costs[category])}")

    return "\n".join(lines)


def build_stats_parts(
    date_str: str,
    income_data: tuple[float, float],
    cost_data: CostSummary,
) -> list[str]:
    capital = income_data[0] - cost_data[0]
    month_diff = income_data[1] - cost_data[1]

    return [
        f"Ваша статистика по состоянию на {date_str}:",
        f"Суммарный капитал: {capital:.2f} рублей",
        format_month_line(month_diff),
        f"Доходы: {income_data[1]:.2f} рублей",
        f"Расходы: {cost_data[1]:.2f} рублей",
        "",
        format_category_details(cost_data[2]),
    ]


def handle_stats(args: list[str], incomes: list[Income], costs: list[Cost]) -> str:
    if len(args) != STATS_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    date = extract_date(args[0])
    if date is None:
        return INCORRECT_DATE_MSG

    income_data = calculate_incomes(incomes, date)
    cost_data = calculate_costs(costs, date)
    return "\n".join(build_stats_parts(args[0], income_data, cost_data))


def dispatch_command(
    tokens: list[str],
    incomes: list[Income],
    costs: list[Cost],
) -> str:
    command = tokens[0]
    args = tokens[1:]

    match(command):
        case "income":
            return handle_income(args, incomes)
        case "cost":
            return handle_cost(args, costs)
        case "stats":
            return handle_stats(args, incomes, costs)
        case _:
            return UNKNOWN_COMMAND_MSG


def main() -> None:
    """Ваш код здесь"""

    incomes: list[Income] = []
    costs: list[Cost] = []

    running = True
    while running:
        line = input()
        tokens = line.strip().split()

        if not tokens:
            print(UNKNOWN_COMMAND_MSG)
            continue

        print(dispatch_command(tokens, incomes, costs))


if __name__ == "__main__":
    main()
