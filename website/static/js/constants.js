
// 每多少次迭代显示一次 value 标注进度条
SHOW_VALUE_BARS_PER_ITERATION = 5;

// 是否接受鼠标输入
MOUSE_INPUT_ENABLED = true;

 // 将动作名字映射为选项名字
var action_name_dict = {
    'ActionMoveTo': "MoveTo",
    'ActionRotateTo': "RotateTo",
    'ActionOpen': "Open",
    'ActionUnlock': 'Unlock',
    'ActionGrab': "Grab",
    'ActionGiveTo': "Give..To..",
    'ActionWaveHand': "WaveHand",
    'ActionMoveToAttention': "MoveToAttention",
    'ActionPointTo': "PointTo",
    'ActionWait': "Wait",
    'ActionNodHead': "NodeHead",
    'ActionShakeHead': "ShakeHead",
    'ActionPlay': "Play",
    'ActionPutInto': "Put..Into..",
    'ActionPutOnto': "Put..Onto..",
    'ActionPutDown': "Put..Down",
    'ActionFollowPointing': "FollowPointing",
    "ActionEat": "Eat",
    "ActionSmash": "Smash",
    "ActionSpeak": "Speak",
    "ActionPerform": "Perform",
    "ActionClose": "Close",
    // 'ActionExplore': "Explore",
    // 'ActionCheckWaving': "CheckWaving",
    // 'ActionHit': "Hit",
    // 'ActionObserveAgent': "ObserveAgent",
    // 'ActionFollowGaze': "FollowGaze",
};

// fix the order of (action options)
// remove action checkwaving, putDown, Hit
var action_name_array = Object.keys(action_name_dict);

// intent 意图描述
// consist with sel_other_high_intent1-0
// consist with sel_your_high_intent-0
var intent_desc_dict = {
    'Get': 'Get..From..',
    'Give': 'Give..To..',
    'Find': 'Find',
    'Open': 'Open',
    'PutInto': 'Put..Into..',
    'PutOnto': 'Put..Onto..',
    'PlayWith': 'Play..With..',
    'RespondTo': 'RespondTo',
    'Inform': 'Inform',
    'Observe': 'Observe',
    'Greet': 'Greet',
    'Harm': 'Harm',
    'Help': 'Help',
    'RequestHelp': 'RequestHelp',
    // 'Refer': 'Refer..To..',
    //'Explore': 'Explore',
    //'Check': 'Check',
    //'Follow': 'Follow',
    //'ObserveAgent': 'ObserveAgent',
}