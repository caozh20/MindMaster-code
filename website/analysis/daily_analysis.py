"""
db: in the NonverbalGame/instance/database.db
database schemas definition in: NonverbalGame/website/models.py
    table User, UserValuesAssign, UserInteraction
"""
from typing import List
import pandas as pd
import sqlite3
import pickle
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from website.models import User, UserValuesAssign, UserInteraction
from website import db

# stats:
# data quality;
# steps, goal finished;
# value consistency: by other estimated, by metrics our design
    # user_1, user_2, user_1_values, user_2_estimated_values, user_2_values, user_1_estimated_values
    # user_1, user_2, user_1_init_intention, user_1_updated_intention, user_2_values, user_1_estimated_values
# intention action policy sequences;


# model:
# intent estimation
# action planning


def interaction_stats(users: List[User], interactions: List[UserInteraction]):
    """
    interaction stats
    :param interactions:
    :return:
    """
    flat_list = []
    for interaction in interactions:
        # todo 0731
        world_agents = interaction.world_agents

        this_agent, other_agent = None, None
        for agent in world_agents:
            if agent.id == interaction.user_agent_id:
                this_agent = agent
            else:
                other_agent = agent

        flat_list.append([
            interaction.id, interaction.mode, interaction.scenario, interaction.control_test,
            interaction.user_id, interaction.user_name, interaction.user_agent_id, interaction.iteration,
            interaction.running_status,
            interaction.your_high_intent,
            interaction.other_high_intent_estimated,
            other_agent.initial_intent.print() if hasattr(other_agent.initial_intent, 'print') else None,
            interaction.other_desire_estimated, other_agent.desire.to_list(),
            interaction.user_agent_action.name() if interaction.user_agent_action else None,
            interaction.ts
        ])

    flat_df = pd.DataFrame(flat_list,
                           columns=['id', 'mode', 'scenario', 'control_test',
                                    'user_id', 'user_name', 'user_agent_id',
                                    'iteration', 'running_status', 'your_high_intent', 'other_high_intent_estimated',
                                    'other_high_intent', 'other_desire_estimated', 'other_desire', 'user_agent_action',
                                    'ts'])
    now = datetime.now().strftime("%Y%m%d_%H%M")
    flat_df.to_excel(f'{now}_flat.xlsx', index=False)


if __name__ == '__main__':

    # by sql
    # conn = sqlite3.connect('../../instance/database.db')
    # c = conn.cursor()
    # rows = c.execute('select * from user_interaction')
    # for row in rows:
    #     # interaction = UserInteraction(*row)
    #     print(pickle.loads(row[9]))
    #     break

    # by orm
    db_url = 'sqlite:///../../instance/database.db'
    engine = create_engine(db_url)
    session = sessionmaker(bind=engine)()

    # only on the non-control test
    user_values = session.query(UserValuesAssign).all()

    users = session.query(User).all()
    interactions = session.query(UserInteraction).all()
    interaction_stats(users, interactions)
