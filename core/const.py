
from enum import Enum, unique

ENTITY_SIZE_CONFIG = {
    'agent': [100, 100],
    'chess': [83, 78],
    'timer': [70, 80],
    'cup': [64, 46],
    'table': [150, 160],
    'banana': [78, 69],
    'key': [48, 48],
    'books': [67, 75],
    'dumbbell': [70, 32],
    'wall': [50, 400],
    # 'box': [194, 157],
    'box': [232, 188],
    'box_open': [260, 182],
    'box_lock': [232, 188],
    # 'box_lock_open': [260, 182],
    'box_unlock': [232, 188],
    'box_unlock_open': [260, 182],
    'shelf': [192, 220],
    'shelf_open': [265, 218],
    'box_small': [180, 145],
    'box_open_small': [180, 126],
    'box_lock_small': [180, 145],
    # 'box_lock_open_small': [180, 126],
    'box_unlock_small': [180, 145],
    'box_unlock_open_small': [180, 126],
}

# world control
WORLD_WIDTH = 700.
WORLD_HEIGHT = 700.

# gesture_dict
GESTURES = {"pointing": 0, "ok": 1, "wave_hand": 2}
# word_dict
WORDS = {"hello", "ok", "there"}

INTENTS_PRIORITY_LIST = ["HIHU", "LIHU", "HILU", "LILU"]

# exponential distribution
LAMBDA = 1.5
# von Mises distribution
MU = 1
KAPPA = 10

# LOG
LOG = 0

NODDING_EPOCHS = 2
WAVING_EPOCHS = 2
SHAKING_EPOCHS = 2
POINTING_EPOCHS = 2
PERFORMING_EPOCHS = 3

# ACTION
PUTDOWN = -1
EXPLORE = -1
SEARCH = -1
STOP = -1
WAVING = 1
NONE = 0

MAX_TRIAL = 30
# turning
V_ANGULAR_1 = 0.04
V_ANGULAR_2 = 0.05

ATTENTION_RADIUS = 0.4
REACHABLE_RADIUS = 100
dis_accepted = 100
NEAR_DIS = 10  # todo?

# save
FPS = 24
# FPS below used for ActionEat
# FPS = 10
MAX_STEPS = 16


@unique
class ScenarioFinishedStatus(Enum):
    # Normal termination
    SUCCESS = 'success'
    # Not finished within the maximum number of steps
    STOPPED = 'stopped'
    # Abnormal termination
    EXCEPTION = 'exception'

# action
action_dict = {"gaze_at": 0, "turn_to": 1, "move_to": 2, "grab": 3, "put_down": 4,
               "point_to": 5, "nod_head": 6, "wave_hand": 7, "raise": 8, "speak": 9}

# intent
intent_dict = {"move": 1, "get": 2, "play": 3, "request": 4,
               "share": 5, "inform": 6, "attract": 7, "check": 8, "confirm": 9}

# move:1, get:2, playwith:3, request:4, share:5, inform:6, pass:7, attract:8, check:9
# invert infer other agent's intent
SIMU_EPOCHS = 20

# intent proposal calculation
# likelihood weight
alpha = 1
# hoiterm weight
beta = 1


# 不在 attention，而在 belief 中的 entity，降低 alpha（透明度）
DOWN_SCALED_ALPHA = 3

@unique
class IntentCategory(Enum):
    Ind = 'individual intent'
    Soc = 'social intent'
    Ref = 'refer intent'
    Comm = 'communication intent'


intent_prior_config_dict = {
    IntentCategory.Ind: {
        "put_onto": 2, "put_into": 2, "get": 2, "find": 2, "open": 2, "play": 2,
        "check": 1, "give": 1, "confirm": 1, "explore": -5, "move_to": 1, "attract": 1
    },
    IntentCategory.Soc: {
        # meaning of infer is to help or harm, I help other help me doesn't make sense.
        "help": 1, "inform": 1, "request_help": 2,
        "share": 1
    },
    IntentCategory.Ref: {
        "ref": 2
    }
}


# fixme, 0425, may need some description
# constants.js
default_action_choices = [
            ['ActionMoveTo', 'somebody or something'],
            ['ActionRotateTo', 'somebody or something'],
            ['ActionOpen', 'something'],
            ['ActionUnlock', 'something'],
            ['ActionGrab', 'something'],
            # give <something> to <somebody>
            ['ActionGiveTo', 'something', 'somebody'],
            ['ActionWaveHand', 'somebody'],
            # move to <somebody>'s attention
            ['ActionMoveToAttention', 'somebody'],
            ['ActionPointTo', 'somebody or something'],
            ['ActionWait'],
            # nod head to somebody
            ['ActionNodHead', 'somebody'],
            # shake head to somebody
            ['ActionShakeHead', 'somebody'],
            ['ActionPlay', 'something'],
            # put something1 into something2
            ['ActionPutInto', 'something1', 'something2'],
            # put something1 onto something2
            ['ActionPutOnto', 'something1', 'something2'],
            # put something down
            ['ActionPutDown', 'something'],
            # follow somebody's pointing
            ['ActionFollowPointing', 'somebody'],
            ['ActionPerform', 'eat or drink'],
            ['ActionSmash', 'cup'],
            ['ActionEat', 'banana'],
            ['ActionClose', 'something'],
            ['ActionSpeak', 'Hello/Thank you']
            # ['ActionExplore'],
            # ['ActionObserve','somebody or world'],
            # check somebody's waving actually rotate to somebody
            # ['ActionCheckWaving', 'somebody'],
            # ['ActionWaveHand', 'STOP'],
            # ['ActionShakeHead', 'STOP'],
            # ['ActionNodHead', 'STOP'],
            # follow somebody's gaze
            # ['ActionFollowGaze', 'somebody'],
            # ['ActionPointTo', 'STOP'],
            # ['ActionObserveAgent', 'somebody'],
            # ['ActionHit', 'something'],
            ]

# "['ActionExplore'] means rotating to a random angle where you may find something\n" \
# "['ActionCheckWaving', 'somebody'] means check <somebody>'s waving actually rotate to <somebody>\n" \
# "['ActionHit', 'something'] means hitting something to inform somebody to seek help\n" \
action_description = "['ActionWaveHand', 'somebody'] means wave hand to somebody to attract his attention\n" \
                     "['ActionNodHead', 'somebody'] means nod head to <somebody>\n" \
                     "['ActionShakeHead', 'somebody'] means shake head to <somebody>\n" \
                     "['ActionUnlock', 'something'] means unlock a locked object. And you need to make sure you have keys on your hands\n" \
                     "['ActionFollowPointing', 'somebody'] means follow somebody's pointing to see what and where the target being pointed to is, which actually rotates to the pointed-to target."
                    # "['ActionGiveTo', 'something', 'somebody'] means give <something> to <somebody>, " \
                   # "['ActionWaveHand', 'STOP'] means stop current hand waving action, " \
                   # "['ActionMoveToAttention', 'somebody'] means move to <somebody>'s attention, " \
                   # "['ActionPointTo', 'somebody or something'] means pointing to somebody or something, "\
                   # "['ActionPointTo', 'STOP'] means stop current pointing action, " \
                   # "['ActionFollowGaze', 'somebody'] means follow <somebody>'s gaze, " \
                   # "['ActionNodHead', 'STOP'] means stop current head nodding action, " \
                   # "['ActionShakeHead', 'somebody'] means shake head to <somebody>, " \
                   # "['ActionShakeHead', 'STOP'] means stop current head shaking action, " \
                   # "['ActionPutInto', 'something1', 'something2'] means put <something1> into <something2>, " \
                   # "['ActionPutOnto', 'something1', 'something2'] means put <something1> onto <something2>, " \
                   # "['ActionPutDown', 'something'] means put something down, " \
                   # "['ActionFollowPointing', 'somebody'] means follow somebody's pointing"


default_intent_space = [['put_onto', 'something1', 'something2'],
                        ['put_into', 'something1', 'something2'],
                        ['give', 'something', 'somebody'],
                        ['get', 'something'],
                        ['find', 'something'],
                        ['move_to', 'somewhere'],
                        ['open', 'something'],
                        ['play', 'something'],
                        ['play_with', 'somebody', 'something'],
                        ['greet', 'somebody'],
                        ['observe', 'somebody or world'],
                        ['inform', 'somebody', 'something'],
                        ['respond_to', 'somebody'],
                        # ['check', 'something or somebody'],
                        # ['confirm', 'somebody'],
                        # ['attract', 'somebody'],
                        # ['follow', 'somebody'],
                        # ['explore'],
]

# constant.js: intent_desc_dict
intent_space_desc = "['put_onto', 'something1', 'something2'], which means put something1 onto something2\n" \
    "['put_into', 'something1', 'something2'], which means put something1 into something2\n" \
    "['give', 'something', 'somebody'], which means give something to somebody\n" \
    "['get', 'something'], which means get something (possibly from a location or from somebody)\n" \
    "['find', 'something'], which means find something\n" \
    "['open', 'something'], which means open something\n" \
    "['play_with', 'somebody', 'something'], which means play with something together with somebody\n" \
    "['respond_to', 'somebody', 'something'], which means respond to somebody with something\n" \
    "['inform', 'somebody', 'something'], which means inform somebody about something\n" \
    "['observe', 'something'], which means observe or pay attention to something\n" \
    "['greet', 'somebody'], which means greet somebody"


social_intent_space_desc = "['help', 'somebody', individual_intent], which means helping someone accomplish their individual intent," \
    "or," \
    "['request_help', 'somebody', individual_intent], which means requesting someone's help to accomplish your own individual intent," \
    "or," \
    "['harm', 'somebody', individual_intent], which means intentionally preventing or disrupting someone's ability to accomplish their individual intent."

intent_simple_desc = '''The representation of intent comes in two types: individual and social. 
Individual intent is represented in the form of ['intent predicate', 'params'].
Social intent has a nested structure and is divided into three types:
1. ['help', 'somebody', individual intent] - means helping someone to accomplish their intent
2. ['request_help', 'somebody', individual intent] - means requesting someone's help to accomplish one's own intent
3. ['harm', 'somebody', individual intent] - means impeding someone from achieving their intent.
Note that you should not use double quotation marks in the intent estimation.'''

formatting_instruction = f'''Formatting instruction: 
1. For individual intent, format as ['intent predicate', 'params']. For example, {intent_space_desc}. Choose an individual intent from the provided examples when possible. If you cannot find a similar intent, create one following the ['intent predicate', 'params'] structure.
2. For social intent, format as {social_intent_space_desc}
3. You must wrap the entire intent expression in double quotation marks, like "['intent predicate', 'params']".
4. Do not use 'me' as a parameter. Replace 'me' with your agent name.'''

desire_value_desc = '''The desire value is represented as a 3-dimensional vector, where each dimension corresponds to a specific aspect of the agent's desires and is assigned discrete values associated with particular characteristics:

Active: Measures the agent's energy levels and preference for physical motion. The possible scores are:
0 (inactive): Indicates a complete absence of energy and a preference for no physical activity.
0.5 (neutral): Reflects a moderate energy level with no strong preference towards activity or inactivity.
1 (active): Signifies high energy levels and a strong preference for physical motion.

Social: Assesses the agent's inclination towards social communication and interactions with others. The possible scores are:
0 (unsocial): Signifies a preference for solitude and avoidance of social interactions.
0.5 (neutral): Indicates no strong preference toward being social or unsocial.
1 (social): Reflects a strong preference for engaging in social communications and interactions with others.

Helpful: Evaluates the agent's propensity to assist others. The possible scores are:
-1 (harmful): Indicates an inclination to hinder others from achieving their goals.
0 (unhelpful): Shows no interest in helping others.
0.5 (helpful): Demonstrates some willingness to provide assistance to others.
1 (very helpful): Shows a strong willingness to provide help.

Note: Unlike the other dimensions, the Helpful dimension does not have a neutral value.'''

if __name__ == '__main__':
    print(f'The intent space is {default_intent_space}({intent_space_desc})')