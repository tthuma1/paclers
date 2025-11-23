agent_instance = None

import random
import threading

import requests

import flask_server  # if you moved Flask to a separate file
from contest.capture_agents import CaptureAgent
from contest.util import nearest_point

threading.Thread(target=flask_server.start_flask, daemon=True).start()

def create_team(first_index, second_index, is_red, first='DummyAgent', second='CustomUniversalAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]

class DummyAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def choose_action(self, game_state):
        actions = game_state.get_legal_actions(self.index)
        return random.choice(actions)


class CustomUniversalAgent(CaptureAgent):
    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        global agent_instance
        agent_instance = self

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        actions = game_state.get_legal_actions(self.index)

        data = {
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
            "walls": game_state.get_walls().as_list()
        }

        try:
            response = requests.post(
                "http://localhost:8080/choose_action",
                json=data,
                timeout=0.05
            )

            java_action = response.text.strip()
            if java_action in actions:
                return java_action

            return random.choice(actions)

        except Exception as e:
            return random.choice(actions)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        # values = [self.evaluate(game_state, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

        # max_value = max(values)
        # best_actions = [a for a, v in zip(actions, values) if v == max_value]

        # food_left = len(self.get_food(game_state).as_list())

        # if food_left <= 2:
        #     best_dist = 9999
        #     best_action = None
        #     for action in actions:
        #         successor = self.get_successor(game_state, action)
        #         pos2 = successor.get_agent_position(self.index)
        #         dist = self.get_maze_distance(self.start, pos2)
        #         if dist < best_dist:
        #             best_action = action
        #             best_dist = dist
        #     return best_action

        # return random.choice(best_actions)

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
        data = {
            "action": action
        }

        try:
            response = requests.post(
                "http://localhost:8080/get_features",
                json=data,
                timeout=0.05
            )

            java_action = response.text.strip()
            return {}

        except Exception as e:
            return {}

    # Get's the base weights for this action
    def get_weights(self, game_state, action):
        return {'distance_to_food': -1}

    def get_maze_distance(self, pos1, pos2):
        print("Getting maze distance: ", pos1, pos2)
        return super().get_maze_distance(pos1, pos2)

    def get_invaders(self, successor):
        # Computes distance to invaders we can see
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        return [a for a in enemies if a.is_pacman and a.get_position() is not None]

    def get_closest_invader(self, position, invaders):
        distances = {}
        for invader in invaders:
            distance = self.get_maze_distance(position, invader.get_position())
            distances[distance] = invader.get_position()

        if len(distances) <= 0:
            return None

        return max(distances)