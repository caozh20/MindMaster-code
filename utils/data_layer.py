import cvxpy as cp
from cvxpylayers.torch import CvxpyLayer
import torch

# 定义元素和关系及其频次
elements = ['A', 'B', 'C']
relations = [('A', 'B', '>', 100), ('B', 'C', '>=', 5), ('B', 'A', '>', 1)]

# 为每个元素创建一个非负变量
ranks = {el: cp.Variable(name=f"rank_{el}", nonneg=True) for el in elements}

# 大于关系的参数化边界定义为 PyTorch 张量
gt_vari = torch.tensor(0.5, requires_grad=True)

# 创建一个cvxpy参数
gt_vari_param = cp.Parameter(nonneg=True)

# 目标函数的组件和约束列表
objective_components = []
constraints = []

# 添加约束和松弛变量
for el1, el2, relation, weight in relations:
    slack = cp.Variable(name=f"slack_{el1}_{el2}", nonneg=True)
    if relation == '>':
        constraints.append(ranks[el1] - ranks[el2] + slack >= gt_vari_param)
    elif relation == '>=':
        constraints.append(ranks[el1] - ranks[el2] + slack >= 0)
    objective_components.append(weight * slack)

# 设置目标函数
objective = cp.Minimize(cp.sum(objective_components))

# 创建问题
problem = cp.Problem(objective, constraints)

# 将问题转换成可微分层，包括gt_vari_param作为参数
cvxpylayer = CvxpyLayer(problem, parameters=[gt_vari_param], variables=[ranks[el] for el in elements] + [v for v in problem.variables() if 'slack' in v.name()])

# 运行求解器，这里需要为gt_vari_param提供值
solution = cvxpylayer(gt_vari)

# 输出解
for i, el in enumerate(elements):
    print(f"Rank of {el}: {solution[i]}")

# 输出松弛变量的值
for v in problem.variables():
    if "slack" in v.name():
        print(f"{v.name}: {solution[v].item()}")