import numpy as np
from cvxopt import matrix, solvers

solvers.options["show_progress"] = False


def solve_problem(A1a, A1b, A2a, A2b, cost_b1=2.0, cost_b2=5.3):
    # Variable order:
    # [x11a, x12a, x21a, x22a, x11b, x12b, x21b, x22b, y11, y12, y21, y22]

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

    # Stock constraints
    G += [[1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    h += [A1a]
    G += [[0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]]
    h += [A2a]
    G += [[0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]]
    h += [A1b]
    G += [[0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]]
    h += [A2b]

    # Demand at B1
    G += [[-1, 0, -1, 0, 0, 0, 0, 0, 1, 0, 1, 0]]
    h += [-2400]
    G += [[0, 0, 0, 0, -1, 0, -1, 0, -0.7, 0, -0.7, 0]]
    h += [-4500]
    G += [[-1, 0, -1, 0, -1, 0, -1, 0, 0, 0, 0, 0]]
    h += [-8300]

    # Demand at B2
    G += [[0, -1, 0, -1, 0, 0, 0, 0, 0, 1, 0, 1]]
    h += [-3400]
    G += [[0, 0, 0, 0, 0, -1, 0, -1, 0, -0.7, 0, -0.7]]
    h += [-2300]
    G += [[0, -1, 0, -1, 0, -1, 0, -1, 0, 0, 0, 0]]
    h += [-6300]

    # Link constraints: y <= x^a
    G += [[-1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]]
    h += [0]
    G += [[0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]]
    h += [0]
    G += [[0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0]]
    h += [0]
    G += [[0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1]]
    h += [0]

    # Non-negativity
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

    # Among all minimum-cost plans choose the one with minimal substitution.
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

    print("\n===== OPTIMAL PLAN =====")

    print("\n--- Steel grade A ---")
    print(f"A1 -> B1: x11a = {x[0]}")
    print(f"A1 -> B2: x12a = {x[1]}")
    print(f"A2 -> B1: x21a = {x[2]}")
    print(f"A2 -> B2: x22a = {x[3]}")

    print("\n--- Steel grade B ---")
    print(f"A1 -> B1: x11b = {x[4]}")
    print(f"A1 -> B2: x12b = {x[5]}")
    print(f"A2 -> B1: x21b = {x[6]}")
    print(f"A2 -> B2: x22b = {x[7]}")

    print("\n--- Substitution (A -> B) ---")
    print(f"A1 -> B1: y11 = {x[8]}")
    print(f"A1 -> B2: y12 = {x[9]}")
    print(f"A2 -> B1: y21 = {x[10]}")
    print(f"A2 -> B2: y22 = {x[11]}")

    print("\n--- Totals ---")
    print(f"Total substitution: {round(sum(x[8:]), 2)} t")
    print(f"Minimum cost: Z = {round(Z, 2)}")

    print("=" * 35)


print("=== BASE SOLUTION ===")
x, Z = solve_problem(5100, 3200, 2900, 5600)
print_solution(x, Z)


print("\n=== RHS ANALYSIS (forcing substitution) ===")

A1a, A1b = 5100, 3200
A2a, A2b = 2900, 5600

for step in range(200):
    x, Z = solve_problem(A1a, A1b, A2a, A2b)
    y_sum = get_y_sum(x)

    print(f"\nStep {step}")
    print(f"Stock A: A1a={A1a}, A2a={A2a}")
    print(f"Stock B: A1b={A1b}, A2b={A2b}")
    print(f"Substitution: {round(y_sum, 2)}")

    if y_sum >= 100:
        print(">>> Substitution reached at least 100 t")
        break

    A1a += 50
    A2a += 50
    A1b -= 50
    A2b -= 50


print("\n=== OBJECTIVE FUNCTION ANALYSIS ===")

A1a = A2a = 10000
A1b = A2b = 10000

cost_b1 = 2.0
cost_b2 = 5.3

for step in range(50):
    x, Z = solve_problem(A1a, A1b, A2a, A2b, cost_b1, cost_b2)
    y_sum = get_y_sum(x)

    print(
        f"\nStep {step}: cost_b1={round(cost_b1, 2)}, cost_b2={round(cost_b2, 2)}"
    )
    print("Substitution:", round(y_sum, 2))

    if y_sum >= 100:
        print(">>> Substitution appeared")
        break

    cost_b1 += 0.2
    cost_b2 += 0.2
