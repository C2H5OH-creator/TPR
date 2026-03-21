from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

MONTHS = 6
DEMAND = [0, 7, 6, 3, 0, 2]
INITIAL_STOCK = 1
MAX_ORDER = 5
CAPACITY = 20
LP_SOLVE = "lp_solve"


@dataclass(frozen=True)
class Solution:
    total_cost: float
    orders: tuple[int, ...]
    trips: tuple[int, ...]
    stocks_before: tuple[int, ...]
    stocks_after: tuple[int, ...]


def build_lp_model(
    storage_cost: float,
    fixed_trip_cost: float,
    final_stock: int | None = None,
) -> str:
    lines: list[str] = []

    objective_terms = []
    for month in range(1, MONTHS + 1):
        objective_terms.append(f"{fixed_trip_cost} y{month}")
        objective_terms.append(f"10 u{month}")
        objective_terms.append(f"{storage_cost} s{month + 1}")
    lines.append("min: " + " + ".join(objective_terms) + ";")

    lines.append(f"s1 = {INITIAL_STOCK};")

    for month, demand in enumerate(DEMAND, start=1):
        next_month = month + 1
        lines.append(f"s{next_month} = s{month} + u{month} - {demand};")
        lines.append(f"s{month} + u{month} >= {demand};")
        lines.append(f"u{month} <= {MAX_ORDER} y{month};")
        lines.append(f"0 <= s{month} <= {CAPACITY};")
        lines.append(f"0 <= u{month} <= {MAX_ORDER};")
        lines.append(f"0 <= y{month} <= 1;")

    lines.append(f"0 <= s{MONTHS + 1} <= {CAPACITY};")

    if final_stock is not None:
        lines.append(f"s{MONTHS + 1} = {final_stock};")

    for month in range(1, MONTHS + 1):
        lines.append(f"int u{month};")
        lines.append(f"bin y{month};")

    return "\n".join(lines) + "\n"


def parse_lp_solve_output(output: str) -> Solution:
    values: dict[str, float] = {}
    objective = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Value of objective function:"):
            objective = float(line.split(":", 1)[1].strip())
            continue

        parts = line.split()
        if len(parts) == 2:
            try:
                values[parts[0]] = float(parts[1])
            except ValueError:
                pass

    if objective is None:
        raise RuntimeError(f"Не удалось разобрать вывод lp_solve:\n{output}")

    orders = tuple(int(round(values[f"u{i}"])) for i in range(1, MONTHS + 1))
    trips = tuple(int(round(values[f"y{i}"])) for i in range(1, MONTHS + 1))
    stocks = tuple(int(round(values[f"s{i}"])) for i in range(1, MONTHS + 2))

    return Solution(
        total_cost=objective,
        orders=orders,
        trips=trips,
        stocks_before=stocks[:-1],
        stocks_after=stocks[1:],
    )


def solve_problem(
    storage_cost: float = 10,
    fixed_trip_cost: float = 50,
    final_stock: int | None = None,
) -> Solution:
    model = build_lp_model(storage_cost, fixed_trip_cost, final_stock)

    with tempfile.NamedTemporaryFile("w", suffix=".lp", delete=False) as handle:
        handle.write(model)
        lp_path = Path(handle.name)

    try:
        result = subprocess.run(
            [LP_SOLVE, str(lp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        lp_path.unlink(missing_ok=True)

    return parse_lp_solve_output(result.stdout)


def same_plan(left: Solution, right: Solution) -> bool:
    return left.orders == right.orders and left.stocks_after == right.stocks_after


def find_parameter_range(
    base_solution: Solution,
    base_storage_cost: int,
    base_fixed_trip_cost: int,
    parameter: str,
    lower_limit: int,
    upper_limit: int,
    final_stock: int | None = None,
) -> tuple[int, int]:
    if parameter not in {"storage_cost", "fixed_trip_cost"}:
        raise ValueError("parameter must be 'storage_cost' or 'fixed_trip_cost'")

    def solve_with(value: int) -> Solution:
        storage_cost = value if parameter == "storage_cost" else base_storage_cost
        fixed_trip_cost = (
            value if parameter == "fixed_trip_cost" else base_fixed_trip_cost
        )
        return solve_problem(storage_cost, fixed_trip_cost, final_stock)

    min_value = (
        base_storage_cost if parameter == "storage_cost" else base_fixed_trip_cost
    )
    max_value = min_value

    for value in range(min_value - 1, lower_limit - 1, -1):
        if same_plan(base_solution, solve_with(value)):
            min_value = value
        else:
            break

    for value in range(max_value + 1, upper_limit + 1):
        if same_plan(base_solution, solve_with(value)):
            max_value = value
        else:
            break

    return min_value, max_value


def print_solution(title: str, solution: Solution) -> None:
    print(title)
    print(f"Минимальная стоимость: {solution.total_cost:.0f}")
    print("Месяц | Спрос | Запас до | Заказ | Рейс | Запас после")
    for month in range(MONTHS):
        print(
            f"{month + 1:5d} |"
            f" {DEMAND[month]:5d} |"
            f" {solution.stocks_before[month]:8d} |"
            f" {solution.orders[month]:5d} |"
            f" {solution.trips[month]:4d} |"
            f" {solution.stocks_after[month]:11d}"
        )
    print()


def main() -> None:
    base_storage_cost = 10
    base_fixed_trip_cost = 50

    base_solution = solve_problem(base_storage_cost, base_fixed_trip_cost)
    print_solution("Базовая задача", base_solution)

    storage_range = find_parameter_range(
        base_solution=base_solution,
        base_storage_cost=base_storage_cost,
        base_fixed_trip_cost=base_fixed_trip_cost,
        parameter="storage_cost",
        lower_limit=0,
        upper_limit=100,
    )
    print(
        "Диапазон стоимости хранения, в котором базовый план остается оптимальным: "
        f"[{storage_range[0]}, {storage_range[1]}]"
    )

    fixed_range = find_parameter_range(
        base_solution=base_solution,
        base_storage_cost=base_storage_cost,
        base_fixed_trip_cost=base_fixed_trip_cost,
        parameter="fixed_trip_cost",
        lower_limit=0,
        upper_limit=200,
    )
    print(
        "Диапазон постоянных затрат на рейс, в котором базовый план остается оптимальным: "
        f"[{fixed_range[0]}, {fixed_range[1]}]"
    )
    print()

    final_stock_solution = solve_problem(
        storage_cost=base_storage_cost,
        fixed_trip_cost=base_fixed_trip_cost,
        final_stock=2,
    )
    print_solution("Задача с конечным запасом 2 станка", final_stock_solution)


if __name__ == "__main__":
    main()
