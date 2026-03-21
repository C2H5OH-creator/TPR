Ниже в порядке реального выполнения программы.

Сначала `main()` в [lab1.cpp](/home/c2h5oh/dev/projects/TPR/lab1/lab1.cpp):
```cpp
std::vector<int> plan;
int total_cost = 0;

minimize_cost(plan, total_cost, DEMAND);
```
Здесь создаётся пустой вектор плана и переменная для общей стоимости. Потом вызывается `minimize_cost(...)`, которая и решает задачу.

Дальше выполнение переходит в:
```cpp
void minimize_cost(std::vector<int>& plan, int& total_cost, const std::vector<int>& demand)
```

Первая строка внутри:
```cpp
int warehouse = INITIAL_NUMBER_OF_MACHINES;
```
В `warehouse` кладётся начальный запас на складе. У тебя это `1`.

Следующая строка:
```cpp
total_cost = min_cost(0, warehouse, demand);
```
Здесь начинается главная рекурсия. Мы спрашиваем:
какова минимальная возможная стоимость, если сейчас `0`-й месяц и на складе `1` станок?

Программа уходит в:
```cpp
int min_cost(int month, int warehouse, const std::vector<int>& demand)
```

Первая проверка:
```cpp
if (month == demand.size()) {
    return 0;
}
```
Если месяцы закончились, дальше платить уже не за что, возвращаем `0`.

Потом:
```cpp
int best = INT_MAX;
```
Это текущий лучший найденный минимум. Пока ничего не нашли, ставим очень большое число.

Дальше главный перебор:
```cpp
for (int order = 0; order <= MAX_ORDER; order++) {
```
Пробуем все возможные заказы в этом месяце: `0, 1, 2, 3, 4, 5`.

Проверка допустимости:
```cpp
if (warehouse + order < demand[month]) {
    continue;
}
```
Если имеющийся запас плюс заказ не покрывают спрос месяца, такой вариант невозможен, пропускаем.

Потом:
```cpp
int next_warehouse = warehouse + order - demand[month];
```
Считаем, сколько останется на складе после удовлетворения спроса.

Проверка склада:
```cpp
if (next_warehouse > WAREHOUSE_CAPACITY) {
    continue;
}
```
Если остаток превышает вместимость склада, вариант запрещён.

Дальше считаем стоимость текущего месяца:
```cpp
int step_cost = 0;
```

Если заказ был:
```cpp
if (order > 0) {
    step_cost += DELIVERY_COST + PER_MACHINE_COST * order;
}
```
Добавляем фиксированную цену рейса `50` и `10` за каждый привезённый станок.

Потом всегда:
```cpp
step_cost += STORAGE_COST * next_warehouse;
```
Добавляем стоимость хранения остатка на конец месяца.

Теперь рекурсивно считаем, сколько будет стоить оптимальное продолжение:
```cpp
int future_cost = min_cost(month + 1, next_warehouse, demand);
```

Проверка:
```cpp
if (future_cost == INT_MAX) {
    continue;
}
```
Если из следующего состояния нельзя дойти до конца допустимым образом, такую ветку не рассматриваем.

Полная стоимость этого варианта:
```cpp
int total = step_cost + future_cost;
```

Сравнение с лучшим найденным:
```cpp
if (total < best) {
    best = total;
}
```
Если этот вариант лучше, обновляем минимум.

Когда цикл по всем `order` закончился:
```cpp
return best;
```
Функция возвращает минимальную стоимость для состояния `(month, warehouse)`.

После того как `min_cost(0, 1, demand)` вернулась, в `minimize_cost(...)` уже записана итоговая оптимальная стоимость:
```cpp
total_cost = min_cost(0, warehouse, demand);
```

Дальше:
```cpp
plan.clear();
```
Очищаем план на случай повторного вызова.

Потом идёт восстановление решений по месяцам:
```cpp
for (int month = 0; month < demand.size(); month++) {
    int order = machines_num(month, warehouse, demand);
    plan.push_back(order);
    warehouse = warehouse + order - demand[month];
}
```

Здесь уже не считаем стоимость, а по очереди восстанавливаем, сколько именно заказать в каждом месяце.

Теперь про `machines_num(...)`.

Вход:
```cpp
int machines_num(int month, int warehouse, const std::vector<int>& demand)
```
Она получает текущий месяц и текущий запас и должна вернуть лучший `order`.

База:
```cpp
if (month == demand.size()) {
    return 0;
}
```
Если месяцев больше нет, заказывать нечего.

Инициализация:
```cpp
int best = INT_MAX;
int best_order = 0;
```
`best` хранит минимальную стоимость среди всех пробованных заказов, а `best_order` какой заказ эту стоимость даёт.

Потом опять перебор:
```cpp
for (int order = 0; order <= MAX_ORDER; order++) {
```
Пробуем все допустимые объёмы заказа.

Дальше всё почти так же, как в `min_cost(...)`:
- проверяем, покрывает ли заказ спрос;
- считаем `next_warehouse`;
- проверяем вместимость;
- считаем `step_cost`;
- считаем `future_cost = min_cost(...)`;
- получаем `total = step_cost + future_cost`.

Ключевая строка:
```cpp
if (total < best) {
    best = total;
    best_order = order;
}
```
Если нашли более выгодный вариант, запоминаем не только стоимость, но и сам `order`.

В конце:
```cpp
return best_order;
```
Функция возвращает, сколько нужно заказать именно в этом месяце при текущем остатке на складе.

После завершения `minimize_cost(...)` управление возвращается в `main()`.

Там идёт вывод:
```cpp
std::cout << "Optimal plan: ";
for (int order : plan) {
    std::cout << order << " ";
}
std::cout << "\nTotal cost: " << total_cost << std::endl;
```

То есть программа печатает:
- последовательность оптимальных заказов по месяцам;
- минимальную суммарную стоимость.
