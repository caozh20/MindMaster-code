from website import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True)
    # 存储的是密文，非明文
    # password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=func.now())


class UserValuesAssign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # whether to conduct control test (
    control_test = db.Column(db.Boolean, nullable=False, default=False)
    email = db.Column(db.String(128), nullable=False)
    initial_values = db.Column(db.String(128), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=func.now())


class UserInteraction(db.Model):
    # record id 标识这条记录的 id
    id = db.Column(db.Integer, primary_key=True)
    # game_id + scenario: 作为game级别的标识
    game_id = db.Column(db.String(64), nullable=False)
    scenario = db.Column(db.String(32), nullable=False)
    # user id 用于同 user info（from qualtrics） 关联匹配
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_uuid = db.Column(db.String(64), nullable=False)
    # user name 用于判断
    user_name = db.Column(db.String(64), nullable=False)
    # 当前用户持有的 scenario 中的 agent id
    user_agent_id = db.Column(db.Integer, nullable=False)
    # 'u2u' or 'u2m'
    mode = db.Column(db.String, nullable=False)
    # 标识一次任务
    task_id = db.Column(db.String(64), nullable=False)

    control_test = db.Column(db.Boolean, nullable=False, default=False)

    # 当前任务下的第几次迭代
    iteration = db.Column(db.Integer, nullable=False)

    # 1. label the action user select
    user_agent_action = db.Column(db.PickleType, nullable=True)

    # 当前运行状态，0 表示success，1 表示 doing，2 表示 REACH_MAX_ITER (30)
    # 参考 FinishStatus
    running_status = db.Column(db.Integer, nullable=True)

    world_agents = db.Column(db.PickleType, nullable=False)
    world_objs = db.Column(db.PickleType, nullable=False)
    world_landmarks = db.Column(db.PickleType, nullable=False)

    # 2. label the (high/low) current intent of user
    # schema: intent_desc (concat by '-')
    your_high_intent = db.Column(db.String(256), nullable=True)
    # your_low_intent = db.Column(db.String(256), nullable=True)

    # 3. label the (high/low) estimated intent of others
    # schema: other_agent_id|intent_desc (concat by '-')
    # todo
    # other_user_name = db.Column(db.String(128), nullable=True)
    other_high_intent_estimated = db.Column(db.String(1024), nullable=True)
    other_desire_estimated = db.Column(db.String(32), nullable=True)
    # other_low_intent_estimated = db.Column(db.String(1024), nullable=True)

    estimation_explanation = db.Column(db.String(2048), nullable=True)
    intention_explanation = db.Column(db.String(2048), nullable=True)
    action_explanation = db.Column(db.String(2048), nullable=True)

    # estimated_intents = db.Column(db.PickleType, nullable=True)
    # 这条记录的创建时间
    ts = db.Column(db.DateTime(timezone=True), default=func.now())

