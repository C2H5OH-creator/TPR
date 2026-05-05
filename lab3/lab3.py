from __future__ import annotations

import numpy as np
from cvxopt import matrix, solvers

try:
    from tabulate import tabulate
except ModuleNotFoundError:
    tabulate = None

solvers.options["show_progress"] = False


YEARS = 5

DEFAULT_INITIAL_STEEL = 3800
DEFAULT_STEEL_CAPACITY = 2500
DEFAULT_MACHINE_CAPACITY = 1700

STEEL_PER_MACHINE = 1.4
STEEL_OUTPUT_RATE = 2.4
STEEL_CAPACITY_GROWTH = 0.1
MACHINE_CAPACITY_COST = 11

CONTROL_BLOCK = YEARS
STATE_BLOCK = YEARS + 1
NUM_VARIABLES = 4 * CONTROL_BLOCK + 3 * STATE_BLOCK


# =========================
# ИНДЕКСАЦИЯ ПЕРЕМЕННЫХ
# =========================


def x_idx(year: int) -> int:
    return year - 1


def y_idx(year: int) -> int:
    return CONTROL_BLOCK + year - 1


def z_idx(year: int) -> int:
    return 2 * CONTROL_BLOCK + year - 1


def w_idx(year: int) -> int:
    return 3 * CONTROL_BLOCK + year - 1


def s_idx(year: int) -> int:
    return 4 * CONTROL_BLOCK + year - 1


def steel_cap_idx(year: int) -> int:
    return 4 * CONTROL_BLOCK + STATE_BLOCK + year - 1


def machine_cap_idx(year: int) -> int:
    return 4 * CONTROL_BLOCK + 2 * STATE_BLOCK + year - 1


def empty_row() -> list[float]:
    return [0.0] * NUM_VARIABLES


def add_ub(G: list[list[float]], h: list[float], row: list[float], rhs: float) -> None:
    G.append(row)
    h.append(rhs)


def add_eq(A: list[list[float]], b: list[float], row: list[float], rhs: float) -> None:
    A.append(row)
    b.append(rhs)


# =========================
# РЕШЕНИЕ ЗАДАЧИ
# =========================


def solve_problem(
    initial_steel: float = DEFAULT_INITIAL_STEEL,
    initial_steel_capacity: float = DEFAULT_STEEL_CAPACITY,
    initial_machine_capacity: float = DEFAULT_MACHINE_CAPACITY,
) -> tuple[np.ndarray, float]:
    c = empty_row()

    # CVXOPT решает задачу минимизации, поэтому максимум выпуска задаем со знаком минус.
    for year in range(1, YEARS + 1):
        c[x_idx(year)] = -1.0 / STEEL_PER_MACHINE

    G: list[list[float]] = []
    h: list[float] = []
    A: list[list[float]] = []
    b: list[float] = []

    # Начальные условия.
    row = empty_row()
    row[s_idx(1)] = 1
    add_eq(A, b, row, initial_steel)

    row = empty_row()
    row[steel_cap_idx(1)] = 1
    add_eq(A, b, row, initial_steel_capacity)

    row = empty_row()
    row[machine_cap_idx(1)] = 1
    add_eq(A, b, row, initial_machine_capacity)

    for year in range(1, YEARS + 1):
        # x_i + y_i + z_i + w_i <= s_i
        row = empty_row()
        row[x_idx(year)] = 1
        row[y_idx(year)] = 1
        row[z_idx(year)] = 1
        row[w_idx(year)] = 1
        row[s_idx(year)] = -1
        add_ub(G, h, row, 0)

        # x_i + w_i <= 0.5 s_i
        row = empty_row()
        row[x_idx(year)] = 1
        row[w_idx(year)] = 1
        row[s_idx(year)] = -0.5
        add_ub(G, h, row, 0)

        # x_i / 1.4 <= p_i^mach
        row = empty_row()
        row[x_idx(year)] = 1 / STEEL_PER_MACHINE
        row[machine_cap_idx(year)] = -1
        add_ub(G, h, row, 0)

        # 2.4 y_i <= p_i^steel
        row = empty_row()
        row[y_idx(year)] = STEEL_OUTPUT_RATE
        row[steel_cap_idx(year)] = -1
        add_ub(G, h, row, 0)

        # s_{i+1} = s_i - x_i + 1.4 y_i - z_i - w_i
        row = empty_row()
        row[s_idx(year + 1)] = 1
        row[s_idx(year)] = -1
        row[x_idx(year)] = 1
        row[y_idx(year)] = -(STEEL_OUTPUT_RATE - 1)
        row[z_idx(year)] = 1
        row[w_idx(year)] = 1
        add_eq(A, b, row, 0)

        # p_{i+1}^steel = p_i^steel + 0.1 z_i
        row = empty_row()
        row[steel_cap_idx(year + 1)] = 1
        row[steel_cap_idx(year)] = -1
        row[z_idx(year)] = -STEEL_CAPACITY_GROWTH
        add_eq(A, b, row, 0)

        # p_{i+1}^mach = p_i^mach + w_i / 11
        row = empty_row()
        row[machine_cap_idx(year + 1)] = 1
        row[machine_cap_idx(year)] = -1
        row[w_idx(year)] = -1 / MACHINE_CAPACITY_COST
        add_eq(A, b, row, 0)

    # В последний год нет смысла производить сталь или расширять мощности:
    # результат этих действий проявится только после окончания планового периода.
    for variable_index in (y_idx(YEARS), z_idx(YEARS), w_idx(YEARS)):
        row = empty_row()
        row[variable_index] = 1
        add_eq(A, b, row, 0)

    # Неотрицательность всех переменных.
    for variable in range(NUM_VARIABLES):
        row = empty_row()
        row[variable] = -1
        add_ub(G, h, row, 0)

    sol = solvers.lp(
        matrix(c, tc="d"),
        matrix(np.array(G, dtype=float), tc="d"),
        matrix(np.array(h, dtype=float), tc="d"),
        matrix(np.array(A, dtype=float), tc="d"),
        matrix(np.array(b, dtype=float), tc="d"),
    )

    solution = np.array(sol["x"]).flatten()
    max_machines = -float(sol["primal objective"])
    return solution, max_machines


# =========================
# ВЫВОД РЕЗУЛЬТАТОВ
# =========================


def format_number(value: float) -> str:
    if abs(value) < 1e-5:
        value = 0.0
    return f"{value:.2f}"


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    string_rows = [[str(cell) for cell in row] for row in rows]

    if tabulate is not None:
        print(
            tabulate(
                string_rows,
                headers=headers,
                tablefmt="grid",
                stralign="right",
                disable_numparse=True,
            )
        )
        return

    table = [headers] + string_rows
    widths = [
        max(len(row[column]) for row in table)
        for column in range(len(headers))
    ]

    def format_row(row: list[str]) -> str:
        return " | ".join(
            value.rjust(widths[index])
            for index, value in enumerate(row)
        )

    separator = "-+-".join("-" * width for width in widths)
    print(format_row(headers))
    print(separator)
    for row in string_rows:
        print(format_row(row))


def get_year_values(solution: np.ndarray, year: int) -> dict[str, float]:
    return {
        "x": solution[x_idx(year)],
        "y": solution[y_idx(year)],
        "z": solution[z_idx(year)],
        "w": solution[w_idx(year)],
        "s": solution[s_idx(year)],
        "steel_cap": solution[steel_cap_idx(year)],
        "machine_cap": solution[machine_cap_idx(year)],
        "machines": solution[x_idx(year)] / STEEL_PER_MACHINE,
    }


def print_solution(solution: np.ndarray, max_machines: float) -> None:
    print("\n===== ОПТИМАЛЬНЫЙ ПЛАН =====")
    headers = [
        "Год",
        "Запас",
        "Мощн. стали",
        "Мощн. станков",
        "x станки",
        "y сталь",
        "z расш. сталь",
        "w расш. станки",
        "Выпуск",
    ]
    rows = []

    for year in range(1, YEARS + 1):
        values = get_year_values(solution, year)
        rows.append(
            [
                year,
                format_number(values["s"]),
                format_number(values["steel_cap"]),
                format_number(values["machine_cap"]),
                format_number(values["x"]),
                format_number(values["y"]),
                format_number(values["z"]),
                format_number(values["w"]),
                format_number(values["machines"]),
            ]
        )

    print_table(headers, rows)
    print(f"Суммарный выпуск: {max_machines:.2f} станков")

    final_steel = solution[s_idx(YEARS + 1)]
    final_steel_cap = solution[steel_cap_idx(YEARS + 1)]
    final_machine_cap = solution[machine_cap_idx(YEARS + 1)]
    print(
        "Итоговое состояние: "
        f"сталь={final_steel:.2f}, "
        f"мощность стали={final_steel_cap:.2f}, "
        f"мощность станков={final_machine_cap:.2f}"
    )


# =========================
# ПОДЗАДАЧИ
# =========================


def task1_base_plan() -> None:
    print("=== ПОДЗАДАЧА 1. БАЗОВЫЙ ПЛАН ===")
    solution, max_machines = solve_problem()
    print_solution(solution, max_machines)


def task2_research_initial_steel() -> None:
    print("\n=== ПОДЗАДАЧА 2. АНАЛИЗ НАЧАЛЬНОГО ЗАПАСА СТАЛИ ===")

    headers = [
        "Нач. запас",
        "Сумм. выпуск",
        "x1",
        "y1",
        "z1",
        "w1",
        "Итог. сталь",
        "Итог. мощн. стали",
        "Итог. мощн. станков",
    ]
    rows = []

    for initial_steel in range(1000, 10001, 1000):
        solution, max_machines = solve_problem(initial_steel=initial_steel)
        first_year = get_year_values(solution, 1)
        rows.append(
            [
                initial_steel,
                format_number(max_machines),
                format_number(first_year["x"]),
                format_number(first_year["y"]),
                format_number(first_year["z"]),
                format_number(first_year["w"]),
                format_number(solution[s_idx(YEARS + 1)]),
                format_number(solution[steel_cap_idx(YEARS + 1)]),
                format_number(solution[machine_cap_idx(YEARS + 1)]),
            ]
        )

    print_table(headers, rows)


def task3_research_machine_capacity() -> None:
    print("\n=== ПОДЗАДАЧА 3. АНАЛИЗ НАЧАЛЬНОЙ МОЩНОСТИ СТАНКОСТРОИТЕЛЬНОГО ЗАВОДА ===")

    headers = [
        "Нач. мощн. станков",
        "Сумм. выпуск",
        "x1",
        "y1",
        "z1",
        "w1",
        "Итог. сталь",
        "Итог. мощн. стали",
        "Итог. мощн. станков",
    ]
    rows = []

    machine_capacity_values = [100] + list(range(500, 5001, 500))

    for machine_capacity in machine_capacity_values:
        solution, max_machines = solve_problem(
            initial_machine_capacity=machine_capacity,
        )
        first_year = get_year_values(solution, 1)
        rows.append(
            [
                machine_capacity,
                format_number(max_machines),
                format_number(first_year["x"]),
                format_number(first_year["y"]),
                format_number(first_year["z"]),
                format_number(first_year["w"]),
                format_number(solution[s_idx(YEARS + 1)]),
                format_number(solution[steel_cap_idx(YEARS + 1)]),
                format_number(solution[machine_cap_idx(YEARS + 1)]),
            ]
        )

    print_table(headers, rows)


def main() -> None:
    task1_base_plan()
    task2_research_initial_steel()
    task3_research_machine_capacity()


if __name__ == "__main__":
    main()
