import random
import threading

import requests

import agent_bridge
import flask_server
from contest.capture_agents import CaptureAgent

threading.Thread(target=flask_server.start_flask, daemon=True).start()

def create_team(first_index, second_index, is_red, first='CustomUniversalAgent', second='CustomUniversalAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]


class DummyAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def choose_action(self, game_state):
        return "Stop"


class CustomUniversalAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.move_count = 0
        self.agent_index = agent_bridge.agent_index
        agent_bridge.agent_instance[self.agent_index] = self
        agent_bridge.agent_index += 1

        print(agent_bridge.agent_index, agent_bridge.agent_instance)

    def final(self, game_state):
        print("Agent ", self.agent_index, " made ", self.move_count, " moves")

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
                timeout=2.00
            )

            self.move_count += 1
            java_action = response.json()["response"].strip()
            if java_action in actions:
                print("Received action: ", java_action)
                return java_action

            return random.choice(actions)

        except Exception as e:
            return random.choice(actions)

    def create_data(self, actions, game_state):
        return {
            "agent_index": self.agent_index,
            "legal_actions": actions,
            "position": game_state.get_agent_position(self.index),
            "score": self.get_score(game_state),
            "food": self.get_food(game_state).as_list(),
            "defending_food": self.get_food_you_are_defending(game_state).as_list(),
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
            # "capsules": game_state.get_capsules(game_state),
            "walls": game_state.get_walls().as_list()
        }

    def get_maze_distance(self, pos1, pos2):
        try:
            return super().get_maze_distance(pos1, pos2)
        except Exception as e:
            return -1