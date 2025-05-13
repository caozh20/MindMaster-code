

# predicate function 是对 agent 状态的判断，因此其接受一个 agent 对象即可满足对该 intent 成功与否的判断
def default_intent_pred(who=None):
    return True


def test_intent_pred(who):
    return 3 in who.holding_ids
