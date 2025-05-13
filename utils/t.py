# The dimension of State is:
# [[pos, towards, holding, pointing][pos, towards, holding, pointing][pos, towards, holding, pointing]]
# The dimension of Action is the same as in Demo:
# [move, towards, holding, pointing]

import os,sys
# sys.path.append("./src")
import gym
import matplotlib.pyplot as plt
from numpy import ndarray, positive
# import scenarios as scenarios
from world.agent import Agent
from action import *
import argparse
from envwrapper import DemoWrapper
from env import CommunicationEnv
import random
from const import NONE

def env_set(env, agent, states):
    env.current_agent = agent
    if len(states) != len(env.world.entities):
        raise ValueError("Wrong state")
    for i in range(len(env.world.agents)):
        state = states[i]
        env.world.entities[i].state.p_pos = np.array(state[0])
        env.world.entities[i].state.attention = state[1]
        env.world.entities[i].state.hold = state[2]
        env.world.entities[i].state.pointing = state[3]
    for i in range(len(env.world.objects)):
        state = states[i+len(env.world.agents)]
        env.world.entities[i+len(env.world.agents)].state.p_pos = np.array(state[0])
        env.world.entities[i+len(env.world.agents)].state.hold = state[1]

def gen_states(env):
    states = []
    for i in range(len(env.world.agents)):
        state = []
        state.append(env.world.entities[i].state.p_pos)
        state.append(env.world.entities[i].state.attention)
        state.append(env.world.entities[i].state.hold)
        state.append(env.world.entities[i].state.pointing)
        states.append(state)
    for i in range(len(env.world.objects)):
        state = []
        state.append(env.world.entities[i+len(env.world.agents)].state.p_pos)
        state.append(env.world.entities[i+len(env.world.agents)].state.hold)
        states.append(state)
    return states

def t(env, agent, states, actions):
    env_set(env.env, agent, states)
    env.step(actions)
    return gen_states(env)

# # only for test
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description=None)
#     parser.add_argument('-s', '--scenario', default='classroom.py', help='Path of the scenario Python script.')
#     args = parser.parse_args()
#     scenario = scenarios.load(args.scenario).Scenario()
#     world = scenario.make_world()
#     env = DemoWrapper(CommunicationEnv(world=world, reset_callback=scenario.reset_world, reward_callback=scenario.reward))
#     agent = 1
#     states = [[[0, 600], 1.3, NONE, NONE], [[0, -600], 1, NONE, NONE], [[600, 0], 1, NONE, NONE],[[620, 0], NONE]]
#     actions = [NONE, NONE, 0, NONE]
#     t(env, agent, states, actions)
#     while 1:
#         env.render()