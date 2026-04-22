import numpy as np
from cvxopt import matrix, solvers

solvers.options["show_progress"] = False


# =========================
# РЕШЕНИЕ ЗАДАЧИ
# =========================
def solve_problem(A1a, A1b, A2a, A2b, cost_b1=2.0, cost_b2=5.3):

    # порядок переменных:
    # [x11a, x12a, x21a, x22a, x11b, x12b, x21b, x22b, y11, y12, y21, y22]

    # x11a — сколько стали марки a везём со склада A1 в пункт B1
    # x12a — со склада A1 в B2
    # x21a — со склада A2 в B1
    # x22a — со склада A2 в B2
    # x11b — аналогично `x11a` для стали марки `b`
    # x12b — аналогично `x12a`
    # x21b — аналогично `x21a`
    # x22b — аналогично `x22a`
    # y11, y12, y21, y22 — объёмы замещения в соответствующих маршрутах

    transport_cost = np.array(
        [
            2,
            5.3,
            2,
            5.3,
            cost_b1,
            cost_b2,
            cost_b1,
            cost_b2,
            0,
            0,
            0,
            0,
        ],
        dtype=float,
    )

    G = []
    h = []

    # Запасы
    G += [[1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    h += [A1a]
    G += [[0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]]
    h += [A2a]
    G += [[0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]]
    h += [A1b]
    G += [[0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]]
    h += [A2b]

    # Спрос B1
    G += [[-1, 0, -1, 0, 0, 0, 0, 0, 1, 0, 1, 0]]
    h += [-2400]
    G += [[0, 0, 0, 0, -1, 0, -1, 0, -0.7, 0, -0.7, 0]]
    h += [-4500]
    G += [[-1, 0, -1, 0, -1, 0, -1, 0, 0, 0, 0, 0]]
    h += [-8300]

    # Спрос B2
    G += [[0, -1, 0, -1, 0, 0, 0, 0, 0, 1, 0, 1]]
    h += [-3400]
    G += [[0, 0, 0, 0, 0, -1, 0, -1, 0, -0.7, 0, -0.7]]
    h += [-2300]
    G += [[0, -1, 0, -1, 0, -1, 0, -1, 0, 0, 0, 0]]
    h += [-6300]

    # Связь y <= x^a
    G += [[-1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]]
    h += [0]
    G += [[0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]]
    h += [0]
    G += [[0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0]]
    h += [0]
    G += [[0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1]]
    h += [0]

    # неотрицательность
    for i in range(12):
        row = [0] * 12
        row[i] = -1
        G.append(row)
        h.append(0)

    base_G = np.array(G, dtype=float)
    base_h = np.array(h, dtype=float)

    cost_sol = solvers.lp(
        matrix(transport_cost, tc="d"),
        matrix(base_G, tc="d"),
        matrix(base_h, tc="d"),
    )
    optimal_cost = float(cost_sol["primal objective"])

    # Среди всех решений с минимальными затратами выбираем то, где замещение минимально.
    cost_tolerance = 1e-7
    refined_G = np.vstack([base_G, transport_cost])
    refined_h = np.append(base_h, optimal_cost + cost_tolerance)
    substitution_cost = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1], dtype=float)

    refined_sol = solvers.lp(
        matrix(substitution_cost, tc="d"),
        matrix(refined_G, tc="d"),
        matrix(refined_h, tc="d"),
    )

    return np.array(refined_sol["x"]).flatten(), optimal_cost


def get_y_sum(x):
    return sum(x[8:])


def print_solution(x, Z):
    x = np.round(x, 2)

    print("\n===== ОПТИМАЛЬНЫЙ ПЛАН =====")

    print("\n--- Сталь марки A ---")
    print(f"A1 → B1: x11a = {x[0]}")
    print(f"A1 → B2: x12a = {x[1]}")
    print(f"A2 → B1: x21a = {x[2]}")
    print(f"A2 → B2: x22a = {x[3]}")

    print("\n--- Сталь марки B ---")
    print(f"A1 → B1: x11b = {x[4]}")
    print(f"A1 → B2: x12b = {x[5]}")
    print(f"A2 → B1: x21b = {x[6]}")
    print(f"A2 → B2: x22b = {x[7]}")

    print("\n--- Замещение (A → B) ---")
    print(f"A1 → B1: y11 = {x[8]}")
    print(f"A1 → B2: y12 = {x[9]}")
    print(f"A2 → B1: y21 = {x[10]}")
    print(f"A2 → B2: y22 = {x[11]}")

    print("\n--- Итоги ---")
    print(f"Общее замещение: {round(sum(x[8:]), 2)} т")
    print(f"Минимальные затраты: Z = {round(Z, 2)}")

    print("=" * 35)


# 1. БАЗОВОЕ РЕШЕНИЕ
print("=== БАЗОВОЕ РЕШЕНИЕ ===")
x, Z = solve_problem(5100, 3200, 2900, 5600)
print_solution(x, Z)


# 2. ИЗМЕНЕНИЕ ПРАВОЙ ЧАСТИ
print("\n=== АНАЛИЗ ПРАВОЙ ЧАСТИ (добиваемся появления замещения) ===")

A1a, A1b = 5100, 3200
A2a, A2b = 2900, 5600

for step in range(200):
    x, Z = solve_problem(A1a, A1b, A2a, A2b)
    y_sum = get_y_sum(x)

    print(f"\nШаг {step}")
    print(f"Запасы стали A: A1a={A1a}, A2a={A2a}")
    print(f"Запасы стали B: A1b={A1b}, A2b={A2b}")
    print(f"Замещение: {round(y_sum, 2)}")

    if y_sum >= 100:
        print(">>> Появилось замещение не менее 100 т")
        break

    A1a += 50
    A2a += 50
    A1b -= 50
    A2b -= 50


# 3. ИЗМЕНЕНИЕ ЦЕЛЕВОЙ ФУНКЦИИ
print("\n=== АНАЛИЗ ЦЕЛЕВОЙ ФУНКЦИИ ===")

A1a = A2a = 10000
A1b = A2b = 10000

cost_b1 = 2.0
cost_b2 = 5.3

for step in range(50):
    x, Z = solve_problem(A1a, A1b, A2a, A2b, cost_b1, cost_b2)
    y_sum = get_y_sum(x)

    print(
        f"\nШаг {step}: cost_b1={round(cost_b1, 2)}, cost_b2={round(cost_b2, 2)}"
    )
    print("Замещение:", round(y_sum, 2))

    if y_sum >= 100:
        print(">>> Появилось замещение")
        break

    cost_b1 += 0.2
    cost_b2 += 0.2
