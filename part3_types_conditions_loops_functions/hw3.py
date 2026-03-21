#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


KEY_DATE = "date"
KEY_AMOUNT = "amount"
KEY_CATEGORY = "category"


financial_transactions_storage: list[dict[str, Any]] = []


DATE_PARTS_COUNT = 3
MIN_YEAR = 1
MIN_MONTH = 1
MIN_DAY = 1
MAX_MONTH = 12
FEBRUARY = 2
DAYS_IN_MONTH = (
    0,
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)


CATEGORY_PARTS_COUNT = 2
INCOME_ARGS_COUNT = 2
COST_CATEGORY_ARGS_COUNT = 1
COST_ARGS_COUNT = 3
STATS_ARGS_COUNT = 1


Date = tuple[int, int, int]


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


def get_category(maybe_cat: str) -> str | None:
    raw_categories = maybe_cat.split("::")

    if len(raw_categories) != CATEGORY_PARTS_COUNT:
        return None

    if raw_categories[0] not in EXPENSE_CATEGORIES:
        return None

    if raw_categories[1] not in EXPENSE_CATEGORIES[raw_categories[0]]:
        return None

    return raw_categories[1]


def is_le_date(date_lhs: Date, date_rhs: Date) -> bool:
    return tuple(reversed(date_lhs)) <= tuple(reversed(date_rhs))


def is_same_month(date_a: Date, date_b: Date) -> bool:
    same_year = date_a[2] == date_b[2]
    same_month = date_a[1] == date_b[1]

    return same_year and same_month


def get_capital(report_date: Date) -> float:
    capital = float(0)

    for operation in financial_transactions_storage:
        op_date = operation[KEY_DATE]
        amount = operation[KEY_AMOUNT]

        if not is_le_date(op_date, report_date):
            continue

        if KEY_CATEGORY in operation:
            continue

        capital += amount

    return capital


def get_summary(report_date: Date) -> tuple[float, float]:
    income = float(0)
    expenses = float(0)

    for operation in financial_transactions_storage:
        op_date = operation[KEY_DATE]
        amount = operation[KEY_AMOUNT]

        if is_le_date(op_date, report_date) and not is_same_month(op_date, report_date):
            continue

        if KEY_CATEGORY in operation:
            expenses += amount
        else:
            income += amount

    return (income, expenses)


def get_details(report_date: Date) -> dict[str, float]:
    details: dict[str, float] = {}

    for operation in financial_transactions_storage:
        op_date = operation[KEY_DATE]
        amount = operation[KEY_AMOUNT]

        if is_le_date(op_date, report_date) and not is_same_month(op_date, report_date):
            continue

        if KEY_CATEGORY not in operation:
            continue

        category = operation[KEY_CATEGORY]
        details[category] = details.get(category, float(0)) + amount

    return details


def format_category_line(index: int, category: str, amount: float) -> str:
    return f"{index}. {category}: {round(amount)}"


def format_details(report_date: Date) -> str:
    details: dict[str, float] = get_details(report_date)
    lines: list[str] = []
    for index, category in enumerate(sorted(details), 1):
        lines.append(format_category_line(index, category, details[category]))

    return "\n".join(lines)


def format_diff(diff: float) -> str:
    word = "loss" if diff < 0 else "profit"
    return f"This month, the {word} amounted to {abs(diff):.2f} rubles."


def storage_stub() -> None:
    financial_transactions_storage.append({})


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        storage_stub()
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(income_date)
    if date is None:
        storage_stub()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({KEY_AMOUNT: amount, KEY_DATE: date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    category = get_category(category_name)
    if category is None:
        storage_stub()
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        storage_stub()
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(income_date)
    if date is None:
        storage_stub()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({KEY_CATEGORY: category, KEY_AMOUNT: amount, KEY_DATE: date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []

    for common_category, target_categories in EXPENSE_CATEGORIES.items():
        if target_categories:
            lines.extend(f"{common_category}::{target_category}" for target_category in target_categories)

    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG

    capital = get_capital(date)
    income, expenses = get_summary(date)

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {capital:.2f} rubles",
        format_diff(income - expenses),
        f"Income: {income:.2f} rubles",
        f"Expenses: {expenses:.2f} rubles",
        "",
        format_details(date),
    ]

    return "\n".join(lines)


def dispatch_income(args: list[str]) -> str:
    if len(args) != INCOME_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    amount = get_amount(args[0])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    return income_handler(amount, args[1])


def dispatch_cost(args: list[str]) -> str:
    if len(args) == COST_CATEGORY_ARGS_COUNT and args[0] == "category":
        return cost_categories_handler()

    if len(args) != COST_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    amount = get_amount(args[1])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    return cost_handler(args[0], amount, args[2])


def dispatch_stats(args: list[str]) -> str:
    if len(args) != STATS_ARGS_COUNT:
        return UNKNOWN_COMMAND_MSG

    return stats_handler(args[0])


def dispatch_command(tokens: list[str]) -> str:
    command = tokens[0]
    args = tokens[1:]
    result = UNKNOWN_COMMAND_MSG

    match command:
        case "income":
            result = dispatch_income(args)
        case "cost":
            result = dispatch_cost(args)
        case "stats":
            result = dispatch_stats(args)

    return result


def main() -> None:
    """Ваш код здесь"""
    running = True
    while running:
        line = input()
        tokens = line.strip().split()

        if not tokens:
            print(UNKNOWN_COMMAND_MSG)
            continue

        print(dispatch_command(tokens))


if __name__ == "__main__":
    main()
