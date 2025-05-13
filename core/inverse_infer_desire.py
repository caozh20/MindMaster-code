from core.world import *


def inverse_infer_desire(agent_self, world: World = None):

    # forward: value => intent => planning
    # backward: planning => intent => value

    if not world:
        for agent in agent_self.belief.agents:
            if agent.id == agent_self.id:
                continue

            if agent.intents_len() > 0:
                # todo: probability distribution
                if agent.intent_now.soc_intent is not None:
                    if agent.intent_now.soc_intent[0] == "help":
                        agent.desire.helpful = 1
                        agent.desire.social = 0.5
                        agent.desire.active = 0.5
                    # elif agent.intent_now.soc_intent[0] == "harm":
                    #     agent.desire.helpful = -1
                    elif agent.intent_now.soc_intent[0] == "request_help":
                        agent.desire.social = 1
                        agent.desire.active = 0
                    # elif agent.intent_now.soc_intent == None and agent.intent_failed:  # todo!!
                    #     agent.desire.social = -1
            if len(agent.action_history) > 0:
                for action in agent.action_history:
                    if action[0] == 'ActionMoveTo':
                        agent.desire.active = 1
                    if action[0] in ['ActionPointTo', 'ActionWaveHand', 'ActionShakeHead', 'ActionNodHead']:
                        agent.desire.social = 1
                    if action[0] in ['ActionFollowPointing', 'ActionFollowGaze']:
                        agent.desire.social = 1
    else:
        for agent in agent_self.belief.agents:
            if agent.id == agent_self.id:
                continue
            agent.desire = world.retrieve_by_id(agent.id).desire.clone()

