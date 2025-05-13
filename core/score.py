

class Score():
    def __init__(self, name="score"):
        self.name = name

    def name(self):
        return self.name


# consider whether the entity is playable or not
class Playable_Score(Score):
    def __init__(self):
        super(Playable_Score, self).__init__("playable_score")

    def __call__(self, agent_self, int, score=1):
        # ind_intent: play
        if int.ind_intent is not None and int.ind_intent[0] == "play":
            if agent_self.belief.get_by_id(int.ind_intent[1]).is_game:
                return score
        if int.soc_intent is not None:
            if int.soc_intent[0] == "help" or int.soc_intent[0] == "request_help":
                help_intent = int.soc_intent[2]
                if help_intent.ind_intent is not None and help_intent.ind_intent[0] == "play":
                    if agent_self.belief.get_by_id(help_intent.ind_intent[1]).is_game:
                        return score
        return 0

