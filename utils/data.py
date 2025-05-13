import pulp

# 创建一个线性规划问题
problem = pulp.LpProblem("WeightedRankingProblem", pulp.LpMinimize)

# 定义一些元素和关系及其频次
elements = ['A', 'B', 'C']
relations = [('A', 'B', '>', 100), ('B', 'C', '>=', 5), ('B', 'A', '>', 1)]

# 为每个元素创建一个变量
ranks = {el: pulp.LpVariable(f"rank_{el}", lowBound=0) for el in elements}

gt_vari = 0.5

# 初始化目标函数的组件
objective_components = []

# 添加约束和松弛变量
for el1, el2, relation, weight in relations:
    slack = pulp.LpVariable(f"slack_{el1}_{el2}", lowBound=0)
    if relation == '>':
        problem += (ranks[el1] - ranks[el2] + slack >= gt_vari, f"{el1}_gt_{el2}")
    elif relation == '>=':
        problem += (ranks[el1] - ranks[el2] + slack >= 0, f"{el1}_ge_{el2}")
    # 使用权重乘以松弛变量并添加到目标函数
    objective_components.append(weight * slack)

# 设置目标函数
problem += pulp.lpSum(objective_components)

# 解决问题
status = problem.solve()

print("Status:", pulp.LpStatus[status])

# 输出结果
for el in elements:
    print(f"Rank of {el}: {ranks[el].value()}")

# 输出松弛变量的值，以检查哪些约束被轻微违反
for v in problem.variables():
    if "slack" in v.name:
        print(f"{v.name}: {v.value()}")