import heapq
import random
from collections import defaultdict
from enum import Enum, auto
from typing import override

from contest.capture_agents import CaptureAgent
from contest.graphics_utils import circle, format_color


def create_team(first_index, second_index, is_red, first='CustomUniversalAgent', second='CustomUniversalAgent', num_training=1):
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


class CustomUniversalAgent(CaptureAgent):
    mapped_moves = defaultdict(list)
    mapped_decisions = defaultdict(list)

    def __init__(self, index, agent_index, is_red, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.agent_index = agent_index
        self.is_red = is_red
        self.start = None
        self.move_count = 0
        self.interpreter = GameInterpreter(agent_index, self)

    def final(self, game_state):
        print("Agent ", self.agent_index, " made ", self.move_count, " moves")
        # print("Mapped Moves:", CustomUniversalAgent.mapped_moves[self.agent_index])
        # print("Mapped Decisions", CustomUniversalAgent.mapped_decisions[self.agent_index])

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        actions = game_state.get_legal_actions(self.index)

        next_move = self.interpreter.compute_next_move(GameData(
            self.is_red,
            actions,
            game_state,
            self.get_food(game_state).as_list(),
            game_state.get_agent_position(self.index),
            game_state.get_agent_state(self.index).is_pacman,
            [
                {
                    "pos": s.get_position(),
                    "isPacman": s.is_pacman,
                    "scaredTimer": s.scared_timer
                }
                for s in [game_state.get_agent_state(i) for i in self.get_opponents(game_state)]
            ],
            game_state.get_capsules(),
            game_state.get_walls().as_list()
        ))

        if next_move is None:
            actual_move = random.choice(actions)
        else:
            actual_move = next_move.__str__().strip()

        self.move_count += 1
        CustomUniversalAgent.mapped_moves[self.index].append(actual_move)
        return actual_move

class GameData:

    def __init__(self, is_red, legal_moves, game_state, food_positions, current_position, is_pacman, enemies, capsules, walls):
        self.legal_moves = legal_moves
        self.game_state = game_state
        self.food_positions = food_positions
        self.current_position = Position.from_tuple(current_position)
        self.is_pacman = is_pacman
        self.enemies = enemies
        self.walls = walls

        if is_red:
            self.agent_color = RedAgentColor("red")
        else:
            self.agent_color = BlueAgentColor("blue")

        self.capsule = Capsule(self.agent_color, capsules)

class Capsule:

    def __init__(self, color, capsules):
        self.consumed = False
        self.position = None
        self.capsule_active_time = 40

        for capsule in capsules:
            capsule_position = Position.from_tuple(capsule)

            if color.is_position_on_safe_side(capsule_position):
                continue

            self.position = capsule_position
            break

    def eat_capsule(self, interpreter):
        self.consumed = True
        interpreter.set_game_state(GameState.ATTACKING)
        print("capsule was eaten")

    def decrease_time(self, interpreter):
        self.capsule_active_time -= 1
        print("Time decreased to", self.capsule_active_time)

        if self.capsule_active_time <= 0:
            interpreter.set_game_state(interpreter.previous_game_state)
            print("Nazaj na prej")

class AgentColor:

    def __init__(self, color):
        self.color = color

    def is_position_on_safe_side(self, position):
        return False

    def get_defensive_treshold(self):
        return None

    def get_spawn_treshold(self):
        return None


class RedAgentColor(AgentColor):

    @override
    def is_position_on_safe_side(self, position):
        return position.x <= 15

    @override
    def get_defensive_treshold(self):
        return 11, 14

    @override
    def get_spawn_treshold(self):
        return 0, 4


class BlueAgentColor(AgentColor):

    @override
    def is_position_on_safe_side(self, position):
        return position.x >= 16

    @override
    def get_defensive_treshold(self):
        return 17, 21

    @override
    def get_spawn_treshold(self):
        return 27, 31

class GameInterpreter:

    def __init__(self, agent_index, parent):
        self.agent_index = agent_index
        self.parent = parent
        self.game_data = None
        self.previous_game_state = None
        self.previous_game_data = None
        self.position_path = None
        self.last_safe_position = None
        self.starting_position = None
        self.previous_position = None
        self.collected_food = 0
        self.encounter_counter = 0
        self.capsule = None

        if self.agent_index == 0:
            self.path_color = format_color(0, 0.4, 0.4)
            initial_state = GameState.FINDING_FOOD
            allowed_goals = [
                FindingFoodGoal(self),
                DepositingFoodGoal(self),
                OffensiveFleeingGoal(self),
                AttackingGoal(self),
                CapsuleFindGoal(self)
            ]
        else:
            self.path_color = format_color(0.4, 0.4, 0)
            initial_state = GameState.DEFENDING
            allowed_goals = [
                DefendingGoal(self),
                DefensiveFleeingGoal(self)
            ]

        self.game_state = initial_state
        self.allowed_goals = allowed_goals

    def set_game_state(self, new_state):
        self.previous_game_state = self.game_state
        self.game_state = new_state

        print("[", self.agent_index, "] New Game State: ", self.game_state, " (", self.previous_game_state, ")")

    def set_position_path(self, path, reason):
        if path is not None:
            print("[", self.agent_index, "] Set new position with destination '", path.destination, "' and reason ", reason)
        else:
            print("[", self.agent_index, "] Set new position with reason ", reason)
    
        #if self.position_path is not None:
        #    self.display_path(self.position_path.positions, format_color(0.0, 0.0, 0.0))
        
        #if path is not None:
        #    self.display_path(path.positions, self.path_color)
        
        self.position_path = path
        
    def display_path(self, positions, color):
        for position in positions:
            point = Position.to_tuple(position)

            circle(self.parent.display.to_screen(point=point), 3,  outline_color=color, fill_color=color, width=1)

    def is_position_safe(self, position):
        if position is None:
            return False

        return self.game_data.agent_color.is_position_on_safe_side(position)

    @staticmethod
    def is_position_valid(game_state, position):
        if position.x >= 32 or position.y >= 32 or position.x < 0 or position.y < 0:
            return False

        return position not in game_state.get_walls().as_list()

    def handle_death(self):
        if self.previous_position is None:
            return

        if self.game_data.current_position.distance(self.previous_position) <= 1:
            return

        self.game_state = GameState.FINDING_FOOD
        self.set_position_path(None, "Agent died, clearing")
        self.last_safe_position = None
        self.previous_position = None
        self.previous_game_data = None
        self.collected_food = 0
        
    def handle_capsule_state(self):
        if self.capsule is None:
            self.capsule = self.game_data.capsule

        if self.game_data.capsule.position is not None:
            return

        if self.get_distance(self.capsule.position, self.game_data.current_position) > 2:
            return

        if self.capsule.capsule_active_time <= 0:
            return

        if not self.capsule.consumed:
            self.capsule.eat_capsule(self)
            return

        self.capsule.decrease_time(self)


    def get_distance(self, from_position, to_position):
        if from_position.x > 32 and to_position.x > 32 and from_position.y < 0 and to_position.y < 0:
            return 1_000  # Out of bounds distance

        try:
            return self.parent.get_maze_distance(from_position.to_tuple(), to_position.to_tuple())
        except Exception:
            return 1_000

    def get_empty_spaces(self, min_x=0, max_x=32, min_y=0, max_y=32):
        empty_spaces = []
        for x in range(32):
            for y in range(32):
                position = Position(x, y)
                if not self.is_position_valid(self.game_data.game_state, position):
                    continue

                if position.x < min_x or position.x > max_x:
                    continue

                if position.y < min_y or position.y > max_y:
                    continue

                empty_spaces.append(position)

        return empty_spaces

    def get_closest_food(self, current_position, remaining_food):
        mapped_positions = {
            pos: self.get_distance(current_position, Position.from_tuple(pos))
            for pos in remaining_food
        }

        if not mapped_positions:
            return None

        closest_position, closest_distance = min(
            mapped_positions.items(),
            key=lambda item: item[1]
        )

        return closest_position, closest_distance

    def get_closest_safe_position(self, current_position):
        if self.last_safe_position is None:
            return None

        closest = None
        for y in range(32):
            position = self.last_safe_position.__set_y__(y)

            if not self.is_position_safe(position) or not self.is_position_valid(self.game_data.game_state, position):
                continue

            position_path = PositionPath(self.game_data, current_position, position)

            if position_path.is_empty():
                continue

            if closest is None:
                closest = position_path
                continue

            if closest.needed_steps > position_path.needed_steps:
                closest = position_path

        return closest

    # Returns an enemy in attacker territory (other)
    def get_valid_defensive_enemy(self, game_data, distance_threshold):
        current_position = game_data.current_position
        enemies = game_data.enemies

        valid_enemies = list()
        for enemy in enemies:
            enemy_position = enemy["pos"]
            if enemy_position is None or self.is_position_safe(Position.from_tuple(enemy_position)):
                continue

            distance = self.get_distance(current_position, Position.from_tuple(enemy_position))
            if distance > distance_threshold:
                continue

            valid_enemies.append(enemy)

        if len(valid_enemies) <= 0:
            return None

        current_position = game_data.current_position
        return min(
            valid_enemies,
            key=lambda item: self.get_distance(current_position, item["pos"])
        )

    # Returns an enemy in home territory (self)
    def get_valid_offensive_enemy(self, game_data):
        enemies = game_data.enemies

        valid_enemies = list()
        for enemy in enemies:
            enemy_position = enemy["pos"]

            if enemy_position is None or not self.is_position_safe(Position.from_tuple(enemy_position)):
                continue
            
            valid_enemies.append(enemy)
            
        if len(valid_enemies) <= 0:
            return None

        current_position = game_data.current_position
        return min(
            valid_enemies,
            key=lambda item: self.get_distance(current_position, item["pos"])
        )

    def get_random_defensive_position(self, game_data, origin, max_distance):
        defensive_treshold = self.game_data.agent_color.get_defensive_treshold()
        empty_spaces = self.get_empty_spaces(min_x=defensive_treshold[0], max_x=defensive_treshold[1])

        for _ in range(50):
            candidate = random.choice(empty_spaces)

            if candidate == origin:
                continue

            if not self.is_position_valid(game_data.game_state, candidate) or not self.is_position_safe(candidate):
                continue

            distance = self.get_distance(origin, candidate)
            if distance >= 1_000 or distance > max_distance:
                continue
                
            return candidate

        return None

    def compute_next_move(self, game_data):
        self.game_data = game_data

        legal_directions = game_data.legal_moves
        current_position = game_data.current_position

        if self.starting_position is None:
            self.starting_position = current_position

        if self.is_position_safe(current_position) and current_position is not self.last_safe_position:
            self.last_safe_position = current_position

        self.handle_death()
        self.handle_capsule_state()

        detailed_move = defaultdict()
        for goal in self.allowed_goals:
            compute_result = goal.compute()
            detailed_move[goal.__class__] = compute_result

        CustomUniversalAgent.mapped_decisions[self.agent_index].append(detailed_move)

        if self.position_path is not None:
            next_step = self.position_path.step()

            if next_step is not None:
                move = Direction.from_position(current_position, next_step)

                if move is not None and move.__str__() in legal_directions:
                    self.previous_position = current_position
                    self.previous_game_data = game_data
                    return move

            self.set_position_path(None, "Current finished, clearing")

        self.previous_position = current_position
        self.previous_game_data = game_data

        return Direction.STOP


class AgentGoal:

    def __init__(self, parent):
        self.parent = parent

    def compute(self) -> str:
        return "None"


class FindingFoodGoal(AgentGoal):

    @override
    def compute(self):
        remaining_food = self.parent.game_data.food_positions
        current_position = self.parent.game_data.current_position
        closest_food_entry = self.parent.get_closest_food(current_position, self.parent.game_data.food_positions)

        if self.parent.game_state is not GameState.FINDING_FOOD and self.parent.game_state is not GameState.DEPOSITING_FOOD and self.parent.game_state is not GameState.ATTACKING:
            return "Different goal active"

        if self.parent.game_state is GameState.ATTACKING and self.parent.position_path is not None:
            return "Attacking an enemy already"

        if len(remaining_food) == 0 and (self.parent.position_path is None or self.parent.position_path.is_completed()):
            closest_safe = self.parent.get_closest_safe_position(current_position)

            if closest_safe is not None:
                self.parent.set_position_path(closest_safe, "All food has been consumed, returning home")

            return "All food has been collected, returning home"

        is_food_square = self.parent.previous_game_data is not None and Position.to_tuple(current_position) in self.parent.previous_game_data.food_positions
        if is_food_square:
            self.parent.collected_food += 1

        if self.parent.collected_food >= 5 and self.parent.game_state is not GameState.DEPOSITING_FOOD and self.parent.game_state is not GameState.ATTACKING and (closest_food_entry is not None and closest_food_entry[1] >= 2):
            self.parent.set_game_state(GameState.DEPOSITING_FOOD)
            return "Collected at least 5 food, returning home to deposit"

        if self.parent.position_path is not None and not self.parent.position_path.is_completed() or closest_food_entry is None:
            return "Already executing food collection"

        self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, Position.from_tuple(closest_food_entry[0])), "New food found")
        return "Executing new food collection"


class DepositingFoodGoal(AgentGoal):

    @override
    def compute(self):
        current_position = self.parent.game_data.current_position

        if self.parent.collected_food > 0 and self.parent.is_position_safe(current_position):
            self.parent.collected_food = 0

        if self.parent.game_state is not GameState.DEPOSITING_FOOD:
            return "Different goal active"

        if self.parent.position_path is None:
            closest_safe = self.parent.get_closest_safe_position(current_position)

            if closest_safe is not None:
                self.parent.set_position_path(closest_safe, "Depositing food")

            return "Returning home to deposit food"

        if not self.parent.position_path.is_completed():
            return "Already executing food deposit"

        self.parent.set_position_path(None, "Clearing position path, deposited food")
        self.parent.set_game_state(GameState.FINDING_FOOD)
        return "Deposited food, switching back to finding food"


class OffensiveFleeingGoal(AgentGoal):

    @override
    def compute(self):
        if self.parent.game_state is GameState.ATTACKING:
            return "Attacking, no need to flee"

        current_position = self.parent.game_data.current_position

        if self.parent.game_state is GameState.OFFENSIVE_FLEEING and (self.parent.position_path is None or self.parent.position_path.is_completed()):
            self.parent.set_game_state(self.parent.previous_game_state)
            return "Already fleeing or resetting to previous state due to completed goal"

        valid_enemy = self.parent.get_valid_defensive_enemy(self.parent.game_data, 3)
        if self.parent.is_position_safe(current_position) and (valid_enemy is None or valid_enemy is not None and not valid_enemy["isPacman"]):
            return "No valid enemy found"

        # TODO: This is incorrect
        # if valid_enemy is not None and not valid_enemy["isPacman"] and self.parent.game_data.is_pacman:
        #     print("Enemy: ", valid_enemy, " Are we a pacman?: ", self.parent.game_data.is_pacman)
#
        #     self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, Position.from_tuple(valid_enemy["pos"])), "Pursuing enemy due to becoming a pacman")
        #     self.parent.set_game_state(GameState.ATTACKING)
        #     return "Switching to attack enemy as we've become a pacman"

        if valid_enemy is None or self.parent.game_state is GameState.OFFENSIVE_FLEEING or self.parent.game_state is GameState.DEFENDING:
            return "No valid enemy found (second)"

        if self.parent.encounter_counter >= 2:
            random_position = self.parent.get_random_defensive_position(self.parent.game_data, current_position, 1_000)

            self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, random_position), "Executed the same encounter 10 times, moving to a random position")
            return "Done the same shit 10 times already, do something else"

        closest_safe = self.parent.get_closest_safe_position(current_position)
        if closest_safe is not None:
            self.parent.set_position_path(closest_safe, "Enemy found, fleeing (Offensive)")
            self.parent.encounter_counter += 1

        self.parent.set_game_state(GameState.OFFENSIVE_FLEEING)
        return "Found a valid enemy, fleeing"


class DefensiveFleeingGoal(AgentGoal):

    @override
    def compute(self):
        current_position = self.parent.game_data.current_position
        if self.parent.game_state is GameState.DEFENSIVE_FLEEING and self.parent.position_path is None:
            self.parent.set_game_state(self.parent.previous_game_state)
            return "Already fleeing or resetting to previous state due to completed goal"

        valid_enemy = self.parent.get_valid_offensive_enemy(self.parent.game_data)
        if valid_enemy is None or valid_enemy["isPacman"]:
            return "No valid enemy or pacman"

        closest_safe = self.parent.get_closest_safe_position(current_position)
        if closest_safe is not None:
            self.parent.set_position_path(closest_safe, "Enemy found, fleeing (Defensive)")

        self.parent.set_game_state(GameState.DEFENSIVE_FLEEING)
        return "Found a valid enemy, fleeing"


class DefendingGoal(AgentGoal):

    @override
    def compute(self):
        if self.parent.game_state is not GameState.DEFENDING:
            return "Different goal active"
    
        current_position = self.parent.game_data.current_position
        # Initial movement to starting defense position
        if current_position.is_x_between(self.parent.game_data.agent_color.get_spawn_treshold()) and self.parent.position_path is None:
            random_defending_position = self.parent.get_random_defensive_position(self.parent.game_data, current_position, 1_000)
            
            self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, random_defending_position), "Initial defending position")
            return "Moving to initial defending position"
    
        # If we're in enemy territory, move to our side
        if not self.parent.is_position_safe(current_position):
            self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, self.parent.last_safe_position), "Moving to defense")

        # Actively pursue enemy in home territory
        if self.parent.position_path is None or (self.parent.position_path is not None and not self.parent.position_path.is_completed()):
            updated_valid_enemy = self.parent.get_valid_offensive_enemy(self.parent.game_data)

            if updated_valid_enemy is not None: #and not updated_valid_enemy["isPacman"]:
                self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, Position.from_tuple(updated_valid_enemy["pos"])), "Updating chase position in home territory")
                return "Updating chase position"

        nearby_enemy = self.parent.get_valid_offensive_enemy(self.parent.game_data)
        if nearby_enemy is not None:
            if not nearby_enemy["isPacman"]:
                self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, Position.from_tuple(nearby_enemy["pos"])), "Chasing enemy in home territory")
                return "Chasing enemy in home territory"
            #else:
            #    # TODO: Find a random close position which moves away from the pursuing enemy
            #    
            #    self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, ))
            #    return "Fleeing from the enemy in home territory"

        if self.parent.position_path is not None and not self.parent.position_path.is_completed():
            return "Already pursuing an active goal"

        # Find a random defending position (reposition)
        random_defending_position = self.parent.get_random_defensive_position(self.parent.game_data, current_position, 6)
        if random_defending_position is None:
            return "Invalid random defending position"
        
        self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, random_defending_position), "Moving to a new defensive position")
        return "Moving to a new defensive position"


class AttackingGoal(AgentGoal):

    @override
    def compute(self):
        current_position = self.parent.game_data.current_position
        valid_enemy = self.parent.get_valid_defensive_enemy(self.parent.game_data, 4)

        print("[", self.parent.agent_index, "]", valid_enemy)

        if self.parent.game_state is not GameState.ATTACKING:
            return "Not attacking"

        if valid_enemy is None:
            return "No valid enemy found"

        if valid_enemy["scaredTimer"] <= 0:
            self.parent.set_game_state(GameState.OFFENSIVE_FLEEING)
            return "Found enemy that was already eaten, run"
        
        target_pos = Position.from_tuple(valid_enemy["pos"])
        self.parent.set_position_path(
            PositionPath(self.parent.game_data, current_position, target_pos),
            "Attacking visible enemy"
        )

        print("Attacking visible enemy")
        return "Attacking visible enemy"


class CapsuleFindGoal(AgentGoal):
    @override
    def compute(self):
        if self.parent.game_state is GameState.FINDING_CAPSULE or self.parent.capsule.consumed:
            return "Already finding capsule or eaten"

        capsule_position = self.parent.capsule.position
        current_position = self.parent.game_data.current_position
        distance = self.parent.get_distance(capsule_position, current_position)

        if distance <= 3:
            self.parent.set_game_state(GameState.FINDING_CAPSULE)
            self.parent.set_position_path(PositionPath(self.parent.game_data, current_position, capsule_position), "Moving to the capsule position")
            return "Finding Capsule"

        return "Capsule is not close enough, ignoring"

class Position:

    @staticmethod
    def from_tuple(origin):
        return Position(origin[0], origin[1])

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def clone(self):
        return Position(self.x, self.y)

    def distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def to_tuple(self):
        return self.x, self.y

    def is_x_between(self, treshold):
        return treshold[0] <= self.x <= treshold[1]

    def __set_x__(self, x):
        return Position(self.x + x, self.y)

    def __set_y__(self, y):
        return Position(self.x, self.y + y)

    def __add__(self, x, y):
        return Position(self.x + x, self.y + y)

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Position(x={self.x}, y={self.y})"

    def __hash__(self):
        return hash((self.x, self.y))


class PositionPath:
    def __init__(self, game_data, starting, ending):
        self.origin = starting
        self.destination = ending
        self.positions = self._generate_positions(game_data, starting, ending)

        if self.positions and self.positions[0] == starting:
            self.positions.pop(0)

        self.current_step = 0

    def is_empty(self):
        return len(self.positions) == 0

    @property
    def needed_steps(self):
        return len(self.positions)

    @property
    def goal(self):
        return self.positions[-1] if self.positions else None

    @property
    def current_step_index(self):
        return self.current_step

    def is_completed(self):
        return self.current_step == len(self.positions)

    def step(self):
        if self.current_step > len(self.positions) - 1:
            return None  # already completed

        pos = self.positions[self.current_step]
        self.current_step += 1
        return pos

    def _generate_positions(self, game_data, start, end):
        walls = set(game_data.walls)
        result = []

        open_heap = []
        all_nodes = {}
        closed = set()

        start_node = self.Node(start, None, 0, self._manhattan(start, end))
        heapq.heappush(open_heap, start_node)
        all_nodes[start] = start_node

        while open_heap:
            current = heapq.heappop(open_heap)
            closed.add(current.position)

            if current.position == end:
                node = current
                while node:
                    result.insert(0, node.position)
                    node = node.parent
                return result

            for neighbor_pos in self._get_neighbors(current.position):
                if Position.to_tuple(neighbor_pos) in walls or neighbor_pos in closed:
                    continue

                g = current.g_cost + 1
                neighbor_node = all_nodes.get(neighbor_pos)

                if neighbor_node is None:
                    neighbor_node = self.Node(
                        neighbor_pos,
                        current,
                        g,
                        self._manhattan(neighbor_pos, end)
                    )
                    all_nodes[neighbor_pos] = neighbor_node
                    heapq.heappush(open_heap, neighbor_node)

                elif g < neighbor_node.g_cost:
                    neighbor_node.parent = current
                    neighbor_node.g_cost = g
                    neighbor_node.f_cost = g + neighbor_node.h_cost

                    open_heap.remove(neighbor_node)
                    heapq.heapify(open_heap)
                    heapq.heappush(open_heap, neighbor_node)

        return result

    @staticmethod
    def _manhattan(a, b):
        return abs(a.x - b.x) + abs(a.y - b.y)

    @staticmethod
    def _get_neighbors(pos):
        return [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1)
        ]

    def __str__(self):
        if not self.positions:
            return "Path[empty]"

        return f"Path[start={self.positions[0]}, end={self.positions[-1]}, steps={len(self.positions)}]"

    class Node:
        def __init__(self, position, parent, g_cost, h_cost):
            self.position = position
            self.parent = parent
            self.g_cost = g_cost
            self.h_cost = h_cost
            self.f_cost = g_cost + h_cost

        def __lt__(self, other):
            return self.f_cost < other.f_cost


class Direction(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()
    STOP = auto()

    def apply_modifier(self, position) -> Position:
        if self is Direction.NORTH:
            return position.__add__(0, 1)
        if self is Direction.SOUTH:
            return position.__add__(0, -1)
        if self is Direction.EAST:
            return position.__add__(1, 0)
        if self is Direction.WEST:
            return position.__add__(-1, 0)
        else:
            return position

    @staticmethod
    def valid_directions():
        return [d for d in Direction if d is not Direction.STOP]

    @staticmethod
    def from_position(current_position, next_step):
        for direction in Direction.valid_directions():
            directional = direction.apply_modifier(current_position)

            if directional.__eq__(next_step):
                return direction

        return None

    def __str__(self):
        name = self.name.lower()
        return name[0].upper() + name[1:]


class GameState(Enum):
    FINDING_FOOD = auto()
    FINDING_CAPSULE = auto()
    DEPOSITING_FOOD = auto()
    OFFENSIVE_FLEEING = auto()  # When we're on the opponents side
    DEFENSIVE_FLEEING = auto()  # When we're on home territory
    DEFENDING = auto()
    ATTACKING = auto()
    WANDER = auto()