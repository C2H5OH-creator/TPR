from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

# =========================
# ПАРАМЕТРЫ МОДЕЛИ
# =========================

YEARS = 5

INITIAL_STEEL = 3800
INITIAL_STEEL_CAPACITY = 2500
INITIAL_MACHINE_CAPACITY = 1700

STEEL_PER_MACHINE = 1.4
STEEL_OUTPUT_RATE = 2.4
STEEL_CAPACITY_GROWTH = 0.1
MACHINE_CAPACITY_COST = 11

STEEL_STEP = 10
CAPACITY_STEP = 10
DECISION_STEP = 100


# =========================
# СТРУКТУРЫ ДАННЫХ
# =========================


# Шаг
@dataclass(frozen=True)
class State:
    steel: int
    steel_capacity: int
    machine_capacity: int


# Управление
@dataclass(frozen=True)
class Decision:
    machines_steel: int
    steel_production: int
    steel_expansion: int
    machine_expansion: int


# Годовой план
@dataclass(frozen=True)
class YearPlan:
    year: int
    state: State
    decision: Decision
    machines: float
    next_state: State


# =========================
# ДИСКРЕТИЗАЦИЯ
# =========================


def round_to_step(value: float, step: int) -> int:
    """Округляет значение до ближайшего узла дискретной сетки."""
    return int(round(value / step) * step)


def floor_to_step(value: float, step: int) -> int:
    """Округляет значение вниз до ближайшего узла дискретной сетки."""
    return int(value // step * step)


def normalize_state_values(
    steel: float,
    steel_capacity: float,
    machine_capacity: float,
) -> State:
    """Приводит компоненты состояния к выбранной дискретной сетке."""
    return State(
        steel=round_to_step(steel, STEEL_STEP),
        steel_capacity=round_to_step(steel_capacity, CAPACITY_STEP),
        machine_capacity=round_to_step(machine_capacity, CAPACITY_STEP),
    )


# =========================
# ДОПУСТИМЫЕ УПРАВЛЕНИЯ
# =========================


def value_range(limit: float, step: int = DECISION_STEP) -> range:
    """Возвращает диапазон неотрицательных значений на сетке управлений."""
    upper = floor_to_step(limit, step)
    return range(0, upper + 1, step)


@lru_cache(maxsize=None)
def generate_decisions(year: int, state: State) -> tuple[Decision, ...]:
    """Возвращает все допустимые управления для заданного состояния."""
    max_machines_steel = min(
        floor_to_step(0.5 * state.steel, DECISION_STEP),
        floor_to_step(state.machine_capacity * STEEL_PER_MACHINE, DECISION_STEP),
    )

    if year == YEARS:
        return (
            Decision(
                machines_steel=max_machines_steel,
                steel_production=0,
                steel_expansion=0,
                machine_expansion=0,
            ),
        )

    decisions = []

    max_steel_production = floor_to_step(
        state.steel_capacity / STEEL_OUTPUT_RATE,
        DECISION_STEP,
    )

    for machines_steel in value_range(max_machines_steel):
        max_machine_expansion = min(
            floor_to_step(0.5 * state.steel - machines_steel, DECISION_STEP),
            state.steel - machines_steel,
        )

        for machine_expansion in value_range(max_machine_expansion):
            remaining_after_machine = state.steel - machines_steel - machine_expansion
            steel_production_limit = min(max_steel_production, remaining_after_machine)

            for steel_production in value_range(steel_production_limit):
                remaining = remaining_after_machine - steel_production

                for steel_expansion in value_range(remaining):
                    decisions.append(
                        Decision(
                            machines_steel=machines_steel,
                            steel_production=steel_production,
                            steel_expansion=steel_expansion,
                            machine_expansion=machine_expansion,
                        )
                    )

    return tuple(decisions)


# =========================
# ПЕРЕХОД СОСТОЯНИЯ И ВЫИГРЫШ
# =========================


def calculate_machines(decision: Decision) -> float:
    """Считает выпуск станков за год."""
    return decision.machines_steel / STEEL_PER_MACHINE


def apply_decision(state: State, decision: Decision) -> State:
    """Возвращает состояние следующего года после выбранного управления."""
    next_steel = (
        state.steel
        - decision.machines_steel
        - decision.steel_production
        - decision.steel_expansion
        - decision.machine_expansion
        + STEEL_OUTPUT_RATE * decision.steel_production
    )
    next_steel_capacity = (
        state.steel_capacity + STEEL_CAPACITY_GROWTH * decision.steel_expansion
    )
    next_machine_capacity = (
        state.machine_capacity + decision.machine_expansion / MACHINE_CAPACITY_COST
    )

    return normalize_state_values(
        next_steel,
        next_steel_capacity,
        next_machine_capacity,
    )


# =========================
# ДИНАМИЧЕСКОЕ ПРОГРАММИРОВАНИЕ
# =========================


def solve_dp(initial_state: State) -> tuple[float, dict[tuple[int, State], Decision]]:
    """Решает задачу ДП и возвращает максимум выпуска и оптимальную политику."""
    policy: dict[tuple[int, State], Decision] = {}

    @lru_cache(maxsize=None)
    def dp(year: int, state: State) -> float:
        if year > YEARS:
            return 0.0

        best_value = float("-inf")
        best_decision = None

        for decision in generate_decisions(year, state):
            machines = calculate_machines(decision)
            next_state = apply_decision(state, decision)
            value = machines + dp(year + 1, next_state)

            if value > best_value:
                best_value = value
                best_decision = decision

        if best_decision is not None:
            policy[(year, state)] = best_decision

        return best_value

    total_machines = dp(1, initial_state)
    print(f"Состояний в кеше ДП: {dp.cache_info().currsize}")

    return total_machines, policy


# =========================
# ВОССТАНОВЛЕНИЕ И ВЫВОД ПЛАНА
# =========================


def restore_plan(
    initial_state: State,
    policy: dict[tuple[int, State], Decision],
) -> list[YearPlan]:
    """Восстанавливает оптимальный план от первого года до конца периода."""
    plan = []
    state = initial_state

    for year in range(1, YEARS + 1):
        decision = policy.get((year, state))
        if decision is None:
            break

        machines = calculate_machines(decision)
        next_state = apply_decision(state, decision)
        plan.append(
            YearPlan(
                year=year,
                state=state,
                decision=decision,
                machines=machines,
                next_state=next_state,
            )
        )
        state = next_state

    return plan


def print_plan(plan: list[YearPlan], total_machines: float) -> None:
    """Печатает годовой план распределения стали."""
    print("\n=== ОПТИМАЛЬНЫЙ ПЛАН ===")
    print(
        "Год | Запас | Мощн. стали | Мощн. станков | "
        "x станки | y сталь | z расш. сталь | w расш. станки | Выпуск"
    )
    print("-" * 103)

    for row in plan:
        decision = row.decision
        state = row.state
        print(
            f"{row.year:>3} | "
            f"{state.steel:>5} | "
            f"{state.steel_capacity:>11} | "
            f"{state.machine_capacity:>13} | "
            f"{decision.machines_steel:>8} | "
            f"{decision.steel_production:>7} | "
            f"{decision.steel_expansion:>13} | "
            f"{decision.machine_expansion:>15} | "
            f"{row.machines:>7.2f}"
        )

    print("-" * 103)
    print(f"Суммарный выпуск: {total_machines:.2f} станков")


# =========================
# ПРОВЕРКА ТЕКУЩЕГО ЭТАПА
# =========================


def main() -> None:
    initial_state = normalize_state_values(
        INITIAL_STEEL,
        INITIAL_STEEL_CAPACITY,
        INITIAL_MACHINE_CAPACITY,
    )

    print("=== ПАРАМЕТРЫ МОДЕЛИ ===")
    print(f"Плановый горизонт: {YEARS} лет")
    print(
        "Начальное состояние: "
        f"сталь={initial_state.steel}, "
        f"мощность стали={initial_state.steel_capacity}, "
        f"мощность станков={initial_state.machine_capacity}"
    )
    print(f"Шаг дискретизации стали: {STEEL_STEP} т")
    print(f"Шаг дискретизации мощностей: {CAPACITY_STEP}")
    print(f"Шаг перебора управлений: {DECISION_STEP} т")

    decisions = generate_decisions(1, initial_state)
    print("\n=== ПРОВЕРКА ДОПУСТИМЫХ УПРАВЛЕНИЙ ===")
    print(f"Количество допустимых управлений: {len(decisions)}")
    print("Первые 5 управлений:")
    for decision in decisions[:5]:
        print(decision)

    test_decision = Decision(
        machines_steel=1000,
        steel_production=1000,
        steel_expansion=500,
        machine_expansion=500,
    )
    next_state = apply_decision(initial_state, test_decision)
    machines = calculate_machines(test_decision)

    print("\n=== ПРОВЕРКА ПЕРЕХОДА СОСТОЯНИЯ ===")
    print(f"Тестовое управление: {test_decision}")
    print(f"Выпуск станков: {machines:.2f}")
    print(
        "Следующее состояние: "
        f"сталь={next_state.steel}, "
        f"мощность стали={next_state.steel_capacity}, "
        f"мощность станков={next_state.machine_capacity}"
    )

    print("\n=== ПРОВЕРКА ДП НА МАЛОМ СОСТОЯНИИ ===")
    test_state = State(steel=500, steel_capacity=500, machine_capacity=200)
    total_machines, policy = solve_dp(test_state)
    plan = restore_plan(test_state, policy)
    print(f"Тестовое состояние: {test_state}")
    print(f"Максимальный выпуск за {YEARS} лет: {total_machines:.2f} станков")
    print_plan(plan, total_machines)


if __name__ == "__main__":
    main()
