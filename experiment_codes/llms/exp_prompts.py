
IntentionSpace = '''
    ['PutOnto'/'PutInto', <something1>, <something2>] put <something1> onto/into <something2> \n 
    ['Give', <something>, <somebody>]: give <something> to <somebody>\n 
    ['Get', <something>, <somewhere/somebody>]: get <something> from <somewhere> or <somebody>\n 
    ['Find'/'Open'/'Observe', <something>]\n 
    ['PlayWith', <something>, <somebody>]: play <something> with <somebody>\n
    ['RespondTo'/'Greet', <somebody>]\n
    ['Inform', <somebody>, <something>]: inform <somebody> of <something>\n
    ['Help', <somebody>, <intention>]: help <somebody> to achieve <intention>\n
    ['RequestHelp', <somebody>, <intention>]: request help from <somebody> to achieve <intention>\n
    ['Harm', <somebody>, <intention>]: prevent <somebody> from achieving <intention>\n
    ['Na']: no intent \n
'''

ActionSpace ='''
    ['ActionMoveTo'/'ActionRotateTo'/'ActionPointTo', <somebody/something>] move/rotate to/point to <somebody> or <something>\n
    ['ActionGiveTo', <something>, <somebody>]: give <something> to <somebody>\n
    ['ActionWaveHand'/'ActionNodHead'/'ActionShakeHead', <somebody>] wave hand / nod head / shake head to <somebody>\n
    ['ActionPlay'/'ActionPutDown'/'ActionClose'/'ActionOpen'/'ActionUnlock'/'ActionGrab', <something>]\n
    ['ActionPutInto'/'ActionPutOnto', <something1>, <something2>]: put <something1> into/onto <something2>\n
    ['ActionFollowPointing', <somebody>]: follow <somebody>'s pointing\n
    ['ActionMoveToAttention', <somebody>]: move to <somebody>'s attention\n
    ['ActionPerform', 'eat'/'drink']: perform to eat or drink\n
    ['ActionSmash', 'cup']\n
    ['ActionEat', 'banana']\n
    ['ActionSpeak', 'Hello'/'Thank you']\n
     ['ActionWait']\n
'''

# ValueSpace='''
#    There are three value dimensions: "Active", "Social", "Helpful".
#    The "Active" value dimension measures the individual's energy level and preference for physical motion.
#    The possible scores of "Active" are:
#    0 (inactive) - indicates a complete absence of energy and a preference for no physical activity;
#    0.5 (neutral) - reflects a moderate energy level with no strong preference towards activity or inactivity;
#    1 (active) - signifies high energy level and a strong preference for physical motion.
#
#    The "Social" value dimension assesses the individual's inclination towards social communication and interactions with others.
#    The possible scores of "Social" are:
#    0 (unsocial) - signifies a preference for solitude and avoidance of social interactions;
#    0.5 (neutral) - indicates no strong preference towards being social or unsocial;
#    1 (social): reflects a strong preference for engaging in social communications and interactions with others.
#
#    The "Helpful" value dimension evaluates the individual's propensity to assist others.
#    The possible scores are (Note: There is no neutral value in this dimension):
#    -1 (harmful) - inclined to hinder others from achieving their goals;
#    0 (unhelpful) - shows no interest in helping others;
#    0.5 (neutral) - reflects a moderate willingness to provide help;
#    1 (helpful) - somewhat willing to provide assistance to others;
#    2 (very helpful) - demonstrates a strong willingness to provide help.
# '''

ValueSpace='''
   There are three value dimensions: "Active", "Social", "Helpful". 
   The "Active" value dimension measures the individual's energy level and preference for physical motion. 
   The possible scores of "Active" are: 0 (inactive), 0.5 (neutral), 1 (active).

   The "Social" value dimension assesses the individual's inclination towards social communication and interactions with others. 
   The possible scores of "Social" are: 0 (unsocial), 0.5 (neutral), 1 (social).

   The "Helpful" value dimension evaluates the individual's propensity to assist others. 
   The possible scores are (Note: There is no neutral value in this dimension):
   -1 (harmful) - inclined to hinder others from achieving their goals;
   0 (unhelpful) - shows no interest in helping others;
   0.5 (neutral) - reflects a moderate willingness to provide help;
   1 (helpful) - somewhat willing to provide assistance to others;
   2 (very helpful) - demonstrates a strong willingness to provide help.
'''

POSITION_ROTATE = '''
The coordinate system follows a Cartesian plane, where the x-axis is horizontal, 
pointing to the right, and the y-axis is vertical, pointing upwards. The rotation angle 
starts at the positive x-axis (0°), increases counterclockwise (positive angle).
'''

# input: observable states and actions, + self actions
# output: inferred intent
PROMPT_INTENTION_AGENT_VIEW = '''
    Imagine you and the other agent are in a room. 
    {POSITION_ROTATE}
    {AGENT_ID_INTRO}
    The intention space includes the following intentions: {IntentionSpace}
    The action space includes the following actions: {ActionSpace}
    You need to infer the other agent's intention based on your observations of the other agent's actions, your own actions, and the world states.   
    Remember that some of the other agent's actions and world states may be unobservable because of the limited field of view.
    Each inferred intention should be written in this format: "agent_i-intent" (e.g., Agent_1-PutOnto-Timer_3-Table_4). 
    Here are the given observations:
    {step_prompt}
    Let's think step by step and output the three most possible intentions and the corresponding confidences in the following format: 
    "My inferred intention of the other agent is: {{ "most_possible_intention": <intention>, "most_possible_intention_cf": <confidence>, "second_possible_intention": <intention>, "second_possible_intention_cf": <confidence>, "third_possible_intention": <intention>, "third_possible_intention_cf": <confidence>}}"
'''

PROMPT_INTENTION_WORLD_VIEW = '''
    Imagine there are two agents in a room. 
    {POSITION_ROTATE}
    {AGENT_ID_INTRO}
    The intention space includes the following intentions: {IntentionSpace}
    The action space includes the following actions: {ActionSpace}
    You need to infer the first agent's intention from a god's eye view based on the actions of the two agents as well as the world states.   
    The inferred intention should be written in this format: "agent_i-intent" (e.g., Agent_1-PutOnto-Timer_3-Table_4). 
    Here are the given observations:
    {step_prompt}
    Let's think step by step and output the three most possible intentions and the corresponding confidences in the following format: 
    "My inferred intention of the first agent is: {{ "most_possible_intention": <intention>, "most_possible_intention_cf": <confidence>, "second_possible_intention": <intention>, "second_possible_intention_cf": <confidence>, "third_possible_intention": <intention>, "third_possible_intention_cf": <confidence>}}"
'''

PROMPT_VALUE_AGENT_VIEW = '''
   Imagine you and the other agent are in a room. 
   {POSITION_ROTATE}
   {AGENT_ID_INTRO}
   The action space includes the following actions: {ActionSpace}
   The value space includes the following values: {ValueSpace}
   You need to infer the other agent's value based on your observations of the other agent's actions, your own actions, and the world states.   
   Remember that some of the other agent's actions and world states may be unobservable because of the limited field of view.
   Here are the given observations:
   {step_prompt}
   Let's think step by step and output the estimated value and the corresponding confidence in this format: 
   "My estimated value of the other agent is: {{"active": <score>, "active_cf": <confidence>, "social": <score>, "social_cf": <confidence>, "helpful": <score>, "helpful_cf": <confidence>}}." 
   '''

PROMPT_VALUE_WORLD_VIEW = '''
   Imagine there are two agents in a room. 
   {POSITION_ROTATE}
   {AGENT_ID_INTRO}
   The action space includes the following actions: {ActionSpace}
   The value space includes the following values: {ValueSpace}
   You need to infer the first agent's value from a god's eye view based on the actions of the two agents as well as the world states.   
   Here are the given observations:
   {step_prompt}
   Let's think step by step and output the estimated value and the corresponding confidence in this format: 
   "My estimated value of the first agent is: {{"active": <score>, "active_cf": <confidence>, "social": <score>, "social_cf": <confidence>, "helpful": <score>, "helpful_cf": <confidence>}}."  
   '''

PROMPT_INTENT_UPDATE_AGENT_VIEW = '''
    Imagine you and the other agent are in a room. 
    {POSITION_ROTATE}
    {AGENT_ID_INTRO}
    The intention space includes the following intentions: {IntentionSpace}
    The action space includes the following actions: {ActionSpace}
    You need to update your own intention based on your observations of the other agent's actions, your own actions, and the world states, 
    your estimation of the other agent's intention and value, your own value and your previous intents.   
    Remember that some of the other agent's actions and world states may be unobservable because of the limited field of view.
    Each updated intention should be written in this format: "agent_i-intent" (e.g., Agent_1-Putonto-Timer_3-Table_4). 
    Here are the given observations:
    {step_prompt}
    Your value is: {your_value}
    Let's think step by step and output the three most possible intentions and the corresponding confidences in the following format: 
    "My updated intention is: {{ "most_possible_intention": <intention>, "most_possible_intention_cf": <confidence>, "second_possible_intention": <intention>, "second_possible_intention_cf": <confidence>, "third_possible_intention": <intention>, "third_possible_intention_cf": <confidence>}}"
'''

PROMPT_ACTION_UPDATE_AGENT_VIEW = '''
    Imagine you and the other agent are in a room. 
    {POSITION_ROTATE}
    {AGENT_ID_INTRO}
    The intention space includes the following intentions: {IntentionSpace}
    The action space includes the following actions: {ActionSpace}
    You need to plan your action based on your observations of the other agent's actions, your own actions, and the world states, 
    your estimation of the other agent's intention and value, your own intent, and your own value.   
    Remember that some of the other agent's actions and world states may be unobservable because of the limited field of view.
    Each selected action should be written in this format: "agent_i-action" (e.g., Agent_1-Putonto-Timer_3-Table_4). 
    Here are the given observations:
    {step_prompt}
    Your value is: {your_value}
    Let's think step by step and output the three most possible actions and the corresponding confidences in the following format: 
    "My selected action is: {{ "most_possible_action": <action>, "most_possible_action_cf": <confidence>, "second_possible_action": <action>, "second_possible_action_cf": <confidence>, "third_possible_action": <action>, "third_possible_action_cf": <confidence>}}"
'''

TIME_STEP_TEMPLATE = '''
    Step {index} :
    {other_action_description}: {other_action}
    {your_action_description}: {your_action}
    {world_state_description}: agents and objects: {obj_list} , and {other_information} , {reachable} , 
'''




