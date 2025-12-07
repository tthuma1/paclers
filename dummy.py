from contest.capture_agents import CaptureAgent


def create_team(first_index, second_index, is_red, first='DummyAgent', second='DummyAgent', num_training=1):
    print("Agent 1: ", first_index, " Type: ", first)
    print("Agent 2: ", second_index, " Type: ", second)

    return [eval(first)(first_index, 0, is_red), eval(second)(second_index, 1, is_red)]


class DummyAgent(CaptureAgent):

    def __init__(self, index, agent_index, is_red, time_for_computing=1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.agent_index = agent_index
        self.is_red = is_red

    def choose_action(self, game_state):
        return "Stop"