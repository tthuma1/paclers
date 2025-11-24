from contest.capture_agents import CaptureAgent

def create_team(first_index, second_index, is_red, first='DummyAgent', second='DummyAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]


class DummyAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def choose_action(self, game_state):
        return "Stop"