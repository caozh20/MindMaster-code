PROMPT_INTENT_MATCH = '''
    Summarize the input text and return a structured dictionary: {{"most_possible_intention": <intention>, "most_possible_intention_cf": <confidence>, "second_possible_intention": <intention>, "second_possible_intention_cf": <confidence>, "third_possible_intention": <intention>, "third_possible_intention_cf": <confidence>}}. Only output the dictionary without explanations.
    The <intention> should be written in this format: "agent_i-intent" (e.g., Agent_1-PutOnto-Timer_3-Table_4).
    The <confidence> should be a float between 0 and 1, representing the confidence level of the intention. If the confidence is ambiguous, use 0.9 for high confidence, 0.5 for medium confidence, and 0.1 for low confidence.
    Input text: {text}
    Output format example: {{"most_possible_intention": "Agent_1-PutOnto-Timer_3-Table_4", "most_possible_intention_cf": 0.9, "second_possible_intention": "Agent_1-Na", "second_possible_intention_cf": 0.3, "third_possible_intention": "Agent_1-RequestHelp-Agent_2-find-cup_1", "third_possible_intention_cf": 0.1}}.
    Output:
'''

PROMPT_ACTION_MATCH = '''
    Summarize the input text and return a structured dictionary: {{ "most_possible_action": <action>, "most_possible_action_cf": <confidence>, "second_possible_action": <action>, "second_possible_action_cf": <confidence>, "third_possible_action": <action>, "third_possible_action_cf": <confidence>}}. Only output the dictionary without explanations.
    The <action> should be written in this format: "agent_i-action" (e.g., Agent_1-Putonto-Timer_3-Table_4).
    The <confidence> should be a float between 0 and 1, representing the confidence level of the intention. If the confidence is ambiguous, use 0.9 for high confidence, 0.5 for medium confidence, and 0.1 for low confidence.
    Input text: {text}
    Output format example: {{ "most_possible_action": "Agent_1-ActionGrab-chessboard_1", "most_possible_action_cf": 0.9, "second_possible_action": "Agent_1-ActionWait", "second_possible_action_cf": 0.3, "third_possible_action": Agent_1-ActionPlay-chessboard_1, "third_possible_action_cf": 0.1}}.
    Output:
'''

PROMPT_VALUE_MATCH = '''
    Summarize the input text and return a structured dictionary: {{"active": <score>, "active_cf": <confidence>, "social": <score>, "social_cf": <confidence>, "helpful": <score>, "helpful_cf": <confidence>}}. Only output the dictionary without explanations.
    The <confidence> should be a float between 0 and 1, representing the confidence level of the intention. If the confidence is ambiguous, use 0.9 for high confidence, 0.5 for medium confidence, and 0.1 for low confidence.
    Input text: {text}
    Output format example: {{"active": 0, "active_cf": 0.9, "social": 0, "social_cf": 0.8, "helpful": 0, "helpful_cf": 0.9}}.
    Output:
'''