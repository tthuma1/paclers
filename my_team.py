import random
import threading

import requests

import flask_server  # if you moved Flask to a separate file
from contest.capture_agents import CaptureAgent
from contest.util import nearest_point
import agent_bridge

threading.Thread(target=flask_server.start_flask, daemon=True).start()

def create_team(first_index, second_index, is_red, first='DummyAgent', second='CustomUniversalAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]

class DummyAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def choose_action(self, game_state):
        return random.choice(game_state.get_legal_actions(self.index))


class CustomUniversalAgent(CaptureAgent):
    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        agent_bridge.agent_instance = self

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        actions = game_state.get_legal_actions(self.index)
        data = self.create_data(actions, game_state)

        try:
            response = requests.post(
                "http://localhost:8080/choose_action",
                json=data,
                timeout=0.05
            )

            java_action = response.text.strip()
            if java_action in actions:
                print("Received action: ", java_action)
                return java_action

            return random.choice(actions)

        except Exception as e:
            return random.choice(actions)

    def get_successor(self, game_state, action):
        successor = game_state.generate_successor(self.index, action)
        pos = successor.get_agent_state(self.index).get_position()
        if pos != nearest_point(pos):
            # Only half a grid position was covered
            return successor.generate_successor(self.index, action)
        else:
            return successor

    def evaluate(self, game_state, action):
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)
        value = features * weights
        return value

    def get_features(self, game_state, action):
        actions = game_state.get_legal_actions(self.index)
        data = self.create_data(game_state, actions)

        try:
            response = requests.post(
                "http://localhost:8080/get_features",
                json=data,
                timeout=0.05
            )

            java_features = response.text.strip()
            print("Received Features: ", java_features)
            return java_features

        except Exception as e:
            return {}

    def create_data(self, actions, game_state):
        return {
            "legalActions": actions,
            "position": game_state.get_agent_position(self.index),
            "score": self.get_score(game_state),
            "food": self.get_food(game_state).as_list(),
            "enemies": [
                {
                    "pos": s.get_position(),
                    "isPacman": s.is_pacman
                }
                for s in [
                    game_state.get_agent_state(i)
                    for i in self.get_opponents(game_state)
                ]
            ],
            #"capsules": game_state.get_capsules(game_state),
            "walls": game_state.get_walls().as_list()
        }

    # Get's the base weights for this action
    def get_weights(self, game_state, action):
        return {'distance_to_food': -1}

    def get_maze_distance(self, pos1, pos2):
        return super().get_maze_distance(pos1, pos2)

    #def get_invaders(self, successor):
    #    # Computes distance to invaders we can see
    #    enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
    #    return [a for a in enemies if a.is_pacman and a.get_position() is not None]
#
    #def get_closest_invader(self, position, invaders):
    #    distances = {}
    #    for invader in invaders:
    #        distance = self.get_maze_distance(position, invader.get_position())
    #        distances[distance] = invader.get_position()
#
    #    if len(distances) <= 0:
    #        return None
#
    #    return max(distances)