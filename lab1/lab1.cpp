#include <iostream>
#include <vector>
#include <climits>

std::vector<int> DEMAND = {0,7,6,3,0,2};
#define INITIAL_NUMBER_OF_MACHINES 1
#define WAREHOUSE_CAPACITY 20
#define MAX_ORDER 5
#define DELIVERY_COST 50
#define PER_MACHINE_COST 10
#define STORAGE_COST 10

int min_cost(
    int month,
    int warehouse,
    const std::vector<int>& demand,
    int final_warehouse = -1,
    int storage_cost = STORAGE_COST,
    int delivery_cost = DELIVERY_COST) {

    if (month == demand.size()) {
        if (final_warehouse == -1 || warehouse == final_warehouse) {
            return 0;
        }
        return INT_MAX;
    }

    int best = INT_MAX;

    for (int order = 0; order <= MAX_ORDER; order++) {
        if (warehouse + order < demand[month]) {
            continue;
        }

        int next_warehouse = warehouse + order - demand[month];
        if (next_warehouse > WAREHOUSE_CAPACITY) {
            continue;
        }

        int step_cost = 0;
        if (order > 0) {
            step_cost += delivery_cost + PER_MACHINE_COST * order;
        }
        step_cost += storage_cost * next_warehouse;

        int future_cost = min_cost(month + 1, next_warehouse, demand, final_warehouse, storage_cost, delivery_cost);
        if (future_cost == INT_MAX) {
            continue;
        }

        int total = step_cost + future_cost;
        if (total < best) {
            best = total;
        }
    }

    return best;
}

int machines_num(
    int month,
    int warehouse,
    const std::vector<int>& demand,
    int final_warehouse = -1,
    int storage_cost = STORAGE_COST,
    int delivery_cost = DELIVERY_COST) {

    if (month == demand.size()) {
        return 0;
    }


    int best = INT_MAX;
    int best_order = 0;

    for (int order = 0; order <= MAX_ORDER; order++) {
        if (warehouse + order < demand[month]) {
            continue;
        }

        int next_warehouse = warehouse + order - demand[month];
        if (next_warehouse > WAREHOUSE_CAPACITY) {
            continue;
        }

        int step_cost = 0;
        if (order > 0) {
            step_cost += delivery_cost + PER_MACHINE_COST * order;
        }
        step_cost += storage_cost * next_warehouse;

        int future_cost = min_cost(month + 1, next_warehouse, demand, final_warehouse, storage_cost, delivery_cost);
        if (future_cost == INT_MAX) {
            continue;
        }

        int total = step_cost + future_cost;
        if (total < best) {
            best = total;
            best_order = order;
        }
    }

    return best_order;
}

void minimize_cost(
    std::vector<int>& plan,
    int& total_cost,
    const std::vector<int>& demand,
    int final_warehouse = -1,
    int storage_cost = STORAGE_COST,
    int delivery_cost = DELIVERY_COST) {
    int warehouse = INITIAL_NUMBER_OF_MACHINES;
    total_cost = min_cost(0, warehouse, demand, final_warehouse, storage_cost, delivery_cost);
    plan.clear();

    for (int month = 0; month < demand.size(); month++) {
        int order = machines_num(month, warehouse, demand, final_warehouse, storage_cost, delivery_cost);
        plan.push_back(order);
        warehouse = warehouse + order - demand[month];
    }
}

std::vector<int> task1(int final_warehouse = -1) {
    std::vector<int> plan;
    int total_cost = 0;

    minimize_cost(plan, total_cost, DEMAND, final_warehouse);

    std::cout << "Оптимальный план закупок "
              << (final_warehouse == -1 ? "без ограничения" : "с ограничением")
              << " на количество станков на последнем месяце";

    if (final_warehouse != -1) {
        std::cout << " (" << final_warehouse << ")";
    }

    std::cout << ": ";

    for (int order : plan) {
        std::cout << order << " ";
    }
    std::cout << "\nОбщая стоимость: " << total_cost << std::endl;

    return plan;
}

int task2(std::vector<int> base_plan = {}){
    int base_cost = 0;
    if (base_plan.empty()) {
        minimize_cost(base_plan, base_cost, DEMAND, STORAGE_COST);
    }

    int left = STORAGE_COST;
    int right = STORAGE_COST;

    for (int cost = STORAGE_COST - 1; cost >= 0; cost--) {
        std::vector<int> current_plan;
        int current_cost = 0;
        minimize_cost(current_plan, current_cost, DEMAND, cost);

        if (current_plan == base_plan) {
            left = cost;
        } else {
            break;
        }
    }

    for (int cost = STORAGE_COST + 1; ; cost++) {
        std::vector<int> current_plan;
        int current_cost = 0;
        minimize_cost(current_plan, current_cost, DEMAND, cost);

        if (current_plan == base_plan) {
            right = cost;
        } else {
            break;
        }
    }

    std::cout << "Границы изменения стоимости хранения: ["
              << left << ", " << right << "]" << std::endl;

    return 0;
}

int task3(std::vector<int> base_plan = {}){
    int base_cost = 0;
    if (base_plan.empty()) {
        minimize_cost(base_plan, base_cost, DEMAND, STORAGE_COST, DELIVERY_COST);
    }

    int left = DELIVERY_COST;
    int right = DELIVERY_COST;

    // Проверка для верхней границы
    int total_demand = 0;
    for (int value : DEMAND) {
        total_demand += value;
    }

    int required = total_demand - INITIAL_NUMBER_OF_MACHINES;
    int min_trips = (required + MAX_ORDER - 1) / MAX_ORDER;

    int base_trips = 0;
    for (int order : base_plan) {
        if (order > 0) {
            base_trips++;
        }
    }

    for (int cost = DELIVERY_COST - 1; cost >= 0; cost--) {
        std::vector<int> current_plan;
        int current_cost = 0;
        minimize_cost(current_plan, current_cost, DEMAND, STORAGE_COST, cost);

        if (current_plan == base_plan) {
            left = cost;
        } else {
            break;
        }
    }

    for (int cost = DELIVERY_COST + 1; ; cost++) {

        if (base_trips == min_trips) {
            std::cout << "Верхняя граница отсутствует: базовый план использует "
                      << min_trips
                      << " рейса(ов), это минимально возможное число рейсов."
                      << std::endl;
        }
        right = -1;
        break;

        std::vector<int> current_plan;
        int current_cost = 0;
        minimize_cost(current_plan, current_cost, DEMAND, STORAGE_COST, cost);

        if (current_plan == base_plan) {
            right = cost;
        } else {
            break;
        }
    }

    std::cout << "Границы изменения постоянных затрат на рейс: ["
              << left << ", " << right << "]" << std::endl;

    return 0;
}

void task4(int final_warehouse) {
    auto plan = task1(final_warehouse);
    std::vector<int> remains = {};
    for (int i = 0; i < plan.size(); ++i) {
        remains.push_back(plan[i] - DEMAND[i]);
    }
    std::cout << "Остатки станков в начале каждого месяца: ";
    for (int remain : remains) {
        std::cout << remain << " ";
    }
    std::cout << std::endl;

}

int main(){
    std::cout << "================ Задача №3 ================" << std::endl;
    std::cout << "\n" << "================ Подзадача №1 ================" << std::endl;
    auto plan = task1();

    std::cout << "\n" << "================ Подзадача №2 ================" << std::endl;
    task2(plan);

    std::cout << "\n" << "================ Подзадача №3 ================" << std::endl;
    task3(plan);

    std::cout << "\n" << "================ Подзадача №4 ================" << std::endl;
    task4(2);
    return 0;
}
