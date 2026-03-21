from __future__ import annotations

import sys

DEMAND = [0, 7, 6, 3, 0, 2]
INITIAL_NUMBER_OF_MACHINES = 1
WAREHOUSE_CAPACITY = 20
MAX_ORDER = 5
DELIVERY_COST = 50
PER_MACHINE_COST = 10
STORAGE_COST = 10

USE_MEMOIZATION = True


def min_cost(
    month: int,
    warehouse: int,
    demand: list[int],
    dp: list[list[int]],
    used: list[list[bool]],
    use_memoization: bool = True,
    final_warehouse: int = -1,
    storage_cost: int = STORAGE_COST,
    delivery_cost: int = DELIVERY_COST,
) -> int:
    if month == len(demand):
        if final_warehouse == -1 or warehouse == final_warehouse:
            return 0
        return sys.maxsize

    if use_memoization and used[month][warehouse]:
        return dp[month][warehouse]

    best = sys.maxsize

    for order in range(MAX_ORDER + 1):
        if warehouse + order < demand[month]:
            continue

        next_warehouse = warehouse + order - demand[month]
        if next_warehouse > WAREHOUSE_CAPACITY:
            continue

        step_cost = 0
        if order > 0:
            step_cost += delivery_cost + PER_MACHINE_COST * order
        step_cost += storage_cost * next_warehouse

        future_cost = min_cost(
            month + 1,
            next_warehouse,
            demand,
            dp,
            used,
            use_memoization,
            final_warehouse,
            storage_cost,
            delivery_cost,
        )
        if future_cost == sys.maxsize:
            continue

        total = step_cost + future_cost
        if total < best:
            best = total

    if use_memoization:
        used[month][warehouse] = True
        dp[month][warehouse] = best

    return best


def machines_num(
    month: int,
    warehouse: int,
    demand: list[int],
    dp: list[list[int]],
    used: list[list[bool]],
    use_memoization: bool = True,
    final_warehouse: int = -1,
    storage_cost: int = STORAGE_COST,
    delivery_cost: int = DELIVERY_COST,
) -> int:
    if month == len(demand):
        return 0

    best = sys.maxsize
    best_order = 0

    for order in range(MAX_ORDER + 1):
        if warehouse + order < demand[month]:
            continue

        next_warehouse = warehouse + order - demand[month]
        if next_warehouse > WAREHOUSE_CAPACITY:
            continue

        step_cost = 0
        if order > 0:
            step_cost += delivery_cost + PER_MACHINE_COST * order
        step_cost += storage_cost * next_warehouse

        future_cost = min_cost(
            month + 1,
            next_warehouse,
            demand,
            dp,
            used,
            use_memoization,
            final_warehouse,
            storage_cost,
            delivery_cost,
        )
        if future_cost == sys.maxsize:
            continue

        total = step_cost + future_cost
        if total < best:
            best = total
            best_order = order

    return best_order


def minimize_cost(
    plan: list[int],
    demand: list[int],
    use_memoization: bool = True,
    final_warehouse: int = -1,
    storage_cost: int = STORAGE_COST,
    delivery_cost: int = DELIVERY_COST,
) -> int:
    warehouse = INITIAL_NUMBER_OF_MACHINES
    dp = [[0] * (WAREHOUSE_CAPACITY + 1) for _ in range(len(demand) + 1)]
    used = [[False] * (WAREHOUSE_CAPACITY + 1) for _ in range(len(demand) + 1)]

    total_cost = min_cost(
        0,
        warehouse,
        demand,
        dp,
        used,
        use_memoization,
        final_warehouse,
        storage_cost,
        delivery_cost,
    )
    plan.clear()

    for month in range(len(demand)):
        order = machines_num(
            month,
            warehouse,
            demand,
            dp,
            used,
            use_memoization,
            final_warehouse,
            storage_cost,
            delivery_cost,
        )
        plan.append(order)
        warehouse = warehouse + order - demand[month]

    return total_cost


def task1(final_warehouse: int = -1) -> list[int]:
    plan: list[int] = []
    total_cost = minimize_cost(plan, DEMAND, USE_MEMOIZATION, final_warehouse)

    print(
        "Optimal order plan "
        + ("without constraint" if final_warehouse == -1 else "with constraint")
        + " on final warehouse stock",
        end="",
    )

    if final_warehouse != -1:
        print(f" ({final_warehouse})", end="")

    print(": ", end="")

    for order in plan:
        print(order, end=" ")
    print(f"\nTotal cost: {total_cost}")

    return plan


def task2(base_plan: list[int] | None = None) -> int:
    if base_plan is None:
        base_plan = []

    if not base_plan:
        minimize_cost(base_plan, DEMAND, USE_MEMOIZATION, -1, STORAGE_COST)

    left = STORAGE_COST
    right = STORAGE_COST

    for cost in range(STORAGE_COST - 1, -1, -1):
        current_plan: list[int] = []
        minimize_cost(current_plan, DEMAND, USE_MEMOIZATION, -1, cost)

        if current_plan == base_plan:
            left = cost
        else:
            break

    cost = STORAGE_COST + 1
    while True:
        current_plan = []
        minimize_cost(current_plan, DEMAND, USE_MEMOIZATION, -1, cost)

        if current_plan == base_plan:
            right = cost
            cost += 1
        else:
            break

    print(f"Storage cost range: [{left}, {right}]")
    return 0


def task3(base_plan: list[int] | None = None) -> int:
    if base_plan is None:
        base_plan = []

    if not base_plan:
        minimize_cost(
            base_plan,
            DEMAND,
            USE_MEMOIZATION,
            -1,
            STORAGE_COST,
            DELIVERY_COST,
        )

    left = DELIVERY_COST
    right = DELIVERY_COST

    total_demand = 0
    for value in DEMAND:
        total_demand += value

    required = total_demand - INITIAL_NUMBER_OF_MACHINES
    min_trips = (required + MAX_ORDER - 1) // MAX_ORDER

    base_trips = 0
    for order in base_plan:
        if order > 0:
            base_trips += 1

    for cost in range(DELIVERY_COST - 1, -1, -1):
        current_plan: list[int] = []
        minimize_cost(current_plan, DEMAND, USE_MEMOIZATION, -1, STORAGE_COST, cost)

        if current_plan == base_plan:
            left = cost
        else:
            break

    cost = DELIVERY_COST + 1
    while True:
        if base_trips == min_trips:
            print(
                "No upper bound: the base plan uses "
                f"{min_trips} trips, which is the minimum possible number of trips."
            )
        right = -1
        break

        current_plan = []
        minimize_cost(current_plan, DEMAND, USE_MEMOIZATION, -1, STORAGE_COST, cost)

        if current_plan == base_plan:
            right = cost
            cost += 1
        else:
            break

    print(f"Trip fixed cost range: [{left}, {right}]")
    return 0


def task4(final_warehouse: int) -> None:
    plan = task1(final_warehouse)
    remains: list[int] = []
    for i in range(len(plan)):
        remains.append(plan[i] - DEMAND[i])

    print("Stock at the beginning of each month: ", end="")
    for remain in remains:
        print(remain, end=" ")
    print()


def main() -> int:
    global USE_MEMOIZATION

    for arg in sys.argv[1:]:
        if arg == "--memo":
            USE_MEMOIZATION = True
        elif arg == "--no-memo":
            USE_MEMOIZATION = False
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: ./lab1.py [--memo | --no-memo]")
            return 1

    print("\n================ Task 1 ================")
    plan = task1()

    print("\n================ Task 2 ================")
    task2(plan)

    print("\n================ Task 3 ================")
    task3(plan)

    print("\n================ Task 4 ================")
    task4(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
