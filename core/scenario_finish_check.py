# decide when the scenario is finished

from core.world import World
from core.entity_utils import Is_Near

# scenario的名称统一为intent + 对应id，便于设计场景终止


class scenario_finish_check():
    def __init__(self, W: World, scenario):
        if scenario in ['chimpanzee', 'classroom', 'container', 'cuptotable',
                        'helping', 'multipointing', 'play_game', 'sally_anne',
                        'baby', 'refer_disambiguation', 'demo']:
            return
        # 这里运用到了指针
        # center_person：拥有核心intent的agent
        # help_person：如果涉及到另一个agent的行为，则为help_person
        # target: 目标物体
        # container
        # supporter
        start = 0
        id_end = scenario.find('_')
        self.center_agent_id = int(scenario[start:id_end])
        self.center_agent = W.retrieve_by_id(self.center_agent_id)
        self.intent_name = scenario

        # 在初始化过程中就根据intent类型读取相应的目标，避免反复读取，从而在一定程度上提高效率
        # 先检查request_help与help，因为他们会涉及到其他intent
        if "request_help" in scenario:
            # 前移三个_
            # 核心agent不变
            start = id_end + 1
            id_end = scenario.find('_', start)
            start = id_end + 1
            id_end = scenario.find('_', start)
            start = id_end + 1
            id_end = scenario.find('_', start)
            pass
        elif "help" in scenario:
            # 前移一个_
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 更改核心agent
            start = id_end + 1
            id_end = scenario.find('_', start)
            self.center_agent_id = int(scenario[start:id_end])
            self.center_agent = W.retrieve_by_id(self.center_agent_id)
            pass
        if "play_with" in scenario:
            # id_play_with_id_id
            # 找到第二个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第三个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第四个_的位置，即可推出第二个id的起始位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            self.help_agent_id = int(scenario[start: id_end])
            self.help_agent = W.retrieve_by_id(self.help_agent_id)
            # 找到第四个_的位置，即可推出第三个id的起始位置
            start = id_end + 1
            self.target_id = int(scenario[start:])
            self.target = W.retrieve_by_id(self.target_id)
            self.play_count = 0
        elif "show" in scenario or "inform" in scenario:
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第四个_的位置，即可推出第二个id的起始位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            self.help_agent_id = int(scenario[start: id_end])
            self.help_agent = W.retrieve_by_id(self.help_agent_id)
            # 找到第四个_的位置，即可推出第三个id的起始位置
            start = id_end + 1
            self.target_id = int(scenario[start:])
            self.target = W.retrieve_by_id(self.target_id)
            self.play_count = 0
        elif "play" in scenario or "open" in scenario or "check" in scenario or "confirm" in scenario or \
                "attract" in scenario or "find" in scenario:
            # 找到第二个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 没有第三个_
            start = id_end + 1
            self.target_id = int(scenario[start:])
            self.target = W.retrieve_by_id(self.target_id)
            self.play_count = 0
        elif "move_to" in scenario:
            # 先前移，抵消move_to中的_
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第二个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 没有第三个_
            start = id_end + 1
            self.target_id = int(scenario[start:])
            self.target = W.retrieve_by_id(self.target_id)
            self.play_count = 0
        elif "put_into" in scenario or "put_onto" in scenario:
            # 找到第二个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第三个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第四个_的位置，即可推出第二个id的起始位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            self.target_id = int(scenario[start: id_end])
            self.target = W.retrieve_by_id(self.target_id)
            # 找到第四个_的位置，即可推出第三个id的起始位置
            start = id_end + 1
            self.container_id = int(scenario[start:])
            self.container = W.retrieve_by_id(self.container_id)
        elif "give" in scenario:
            # 找到第三个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第四个_的位置，即可推出第二个id的起始位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            self.target_id = int(scenario[start: id_end])
            self.target = W.retrieve_by_id(self.target_id)
            # 找到第四个_的位置，即可推出第三个id的起始位置
            start = id_end + 1
            self.help_agent_id = int(scenario[start:])
            self.help_agent = W.retrieve_by_id(self.help_agent_id)
        elif "get" in scenario:
            # 找到第三个_的位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            # 找到第四个_的位置，即可推出第二个id的起始位置
            start = id_end + 1
            id_end = scenario.find('_', start)
            if id_end == -1:
                # 表明未指定从哪里获得
                self.target_id = int(scenario[start:])
                self.target = W.retrieve_by_id(self.target_id)
            else:
                self.target_id = int(scenario[start: id_end])
                self.target = W.retrieve_by_id(self.target_id)
                # 找到第四个_的位置，即可推出第三个id的起始位置
                start = id_end + 1
                self.container_id = int(scenario[start:])
                self.container = W.retrieve_by_id(self.container_id)
        pass

    def __call__(self, W: World, scenario):

        # 对于场景化生成
        if scenario == "cuptotable":
            # check whether the cup is put into table
            table = W.get("table")
            box = W.get('box')
            if table is not None and 4 in table.supporting_ids:
                return True
            if box is not None and 4 in box.containing:
                return True
            return False
        elif scenario == "play_game":
            # assuming that there are only two agents
            # 采取临近 + 一次play判定
            self.center_agent = W.retrieve_by_id(1)
            self.help_agent = W.retrieve_by_id(2)
            self.target = W.retrieve_by_id(3)
            self.target_id = 3
            if Is_Near(self.center_agent, self.target, W) and Is_Near(self.help_agent, self.target, W):
                center_played = (len(self.center_agent.action_history) > 0 and self.center_agent.action_history[-1][0] == "ActionPlay" 
                                 and int(self.center_agent.action_history[-1][2]) == self.target_id)
                help_played = (len(self.help_agent.action_history) > 0 and self.help_agent.action_history[-1][0] == "ActionPlay" 
                               and int(self.help_agent.action_history[-1][2]) == self.target_id)
                # if center_played or help_played:
                #     return True
                # update 1113
                if center_played and help_played:
                    return True
            return False
            if not len(W.agents[0].action_history) == 0 or len(W.agents[1].action_history) == 0:
                if W.agents[0].action_history[-1][0] == "ActionPlay" and W.agents[1].action_history[-1][
                    0] == "ActionPlay":
                    return True
            return False
        elif scenario == "baby":
            # when the bookshelf is opened and the book is in it, the scenario will finish
            bookshelf = W.get(4)
            books = W.get(3)
            if bookshelf is None or books is None:
                raise Exception("Scenario baby does not have bookshelf or books")
            if len(bookshelf.containing) and books.id in bookshelf.containing:
                return True
            else:
                return False
        elif scenario == "chimpanzee":
            box = W.get(3)
            if box is None:
                raise Exception("Scenario chimpanzee does not have box")
            if box.locked is False and box.open is True:
                return True
            else:
                return False
        elif scenario == "classroom":
            prof = W.get(1)
            assistant = W.get(2)
            ipad = W.get(4)
            if prof is None or assistant is None:
                raise Exception("Scenario classroom does not have prof or assistant")
            if ipad is None:
                raise Exception("Scenario classroom does not have ipad")
            if prof.belief.get(ipad) is not None:
                return True
            # if prof.attention_check(ipad, W, Att_R=0.001) == 1:
            #     return True
            else:
                return False
        elif scenario == "container":
            # when the agent get toy
            requirer = W.get(1)
            target_id = 3
            # toy = W.get('object toy') or W.get('object banana') or W.get('object cup')
            # if requirer is None or toy is None:
            #     raise Exception("Scenario container does not have requirer or toy")
            if len(requirer.holding_ids) and (target_id in requirer.holding_ids):
                return True
            else:
                return False
        elif scenario == "helping":
            cabinet = W.get(3)
            book = W.get(4)
            if cabinet is None or book is None:
                raise Exception("Scenario helping does not have cabinet or book")
            if len(cabinet.containing) and book.id in cabinet.containing:
                return True
            else:
                return False
        elif scenario == "multipointing":
            cup = W.get(3)
            requirer = W.get(1)
            if cup is None or requirer is None:
                raise Exception("Scenario multipointing does not have cup or requirer")
            if len(cup.being_held_id) and (requirer.id in cup.being_held_id):
                return True
            else:
                return False
        elif scenario == "refer_disambiguation":
            requirer = W.get(1)
            target = W.get(4)
            if requirer is None or target is None:
                raise Exception("Scenario refer_disambiguation does not have target or requirer")
            if len(target.being_held_id) and (requirer.id in target.being_held_id):
                return True
            else:
                return False
        elif scenario == 'sally_anne':
            # target = W.get(5)
            obj = W.get(3)
            # if len(obj.being_contained) > 0 and (5 in obj.being_contained):
            #     return True
            return False

        # 对于intent_targeted 判定
        if "play_with" in self.intent_name:
            # assuming that there are only two agents
            # 采取临近 + 一次play判定
            if Is_Near(self.center_agent, self.target, W) and Is_Near(self.help_agent, self.target, W):
                if self.center_agent.action_history[-1][0] == "ActionPlay" and self.center_agent.action_history[-1][2] == str(self.target_id) \
                    and self.help_agent.action_history[-1][0] == "ActionPlay" and self.help_agent.action_history[-1][2] == str(self.target_id):
                    return True
            return False
        elif "play" in self.intent_name:
            if len(self.center_agent.action_history) == 0:
                self.play_count = 0
                return False
            if self.center_agent.action_history[-1][0] == "ActionPlay" and self.center_agent.action_history[-1][2] == self.target_id:
                self.play_count += 1
                if self.play_count > 3:
                    self.play_count = 0
                    return True
                else:
                    return False
            self.play_count = 0
            return False
        elif "put_onto" in self.intent_name:
            if self.target_id in self.container.supporting_ids:
                return True
            else:
                return False
        elif "put_into" in self.intent_name:
            print(self.container.containing)
            if self.target_id in self.container.containing:
                return True
            else:
                return False
        elif "give" in self.intent_name:
            if self.target_id in self.help_agent.holding_ids:
                return True
            else:
                return False
        elif "get" in self.intent_name:
            if self.target_id in self.center_agent.holding_ids:
                return True
            else:
                return False
        elif "find" in self.intent_name or "check" in self.intent_name:
            if self.center_agent.belief.get(self.target_id) is not None:
                return True
            else:
                return False
        elif "move_to" in self.intent_name:
            return Is_Near(self.center_agent, self.target, None)
        elif "open" in self.intent_name:
            return self.target.open
        elif "confirm" in self.intent_name:
            # 向对方点头即可
            if self.center_agent.belief.get(self.target_id) is not None and self.center_agent.nodding and \
                    self.target.belief.get(self.center_agent_id) is not None:
                return True
            else:
                return False
        elif "attract" in self.intent_name:
            if self.target.belief.get(self.center_agent_id) is not None:
                return True
            else:
                return False
        elif "share" in self.intent_name or "inform" in self.intent_name:
            if self.help_agent.belief.get(self.target_id) is not None:
                return True
            else:
                return False

        # todo: 考虑shared_attention的作用，而并非只考虑belief
