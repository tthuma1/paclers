import heapq
import random
from enum import Enum, auto

from astar import AStar

from contest.capture_agents import CaptureAgent

def create_team(first_index, second_index, is_red, first='DummyAgent', second='CustomUniversalAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]

class DummyAgent(CaptureAgent):

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def choose_action(self, game_state):
        return "Stop"

class CustomUniversalAgent(CaptureAgent):
    agent_index = 0

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None
        self.move_count = 0

        if CustomUniversalAgent.agent_index == 0:
            initial_state = GameState.FINDING_FOOD
        else:
            initial_state = GameState.DEFENDING

        self.interpreter = GameInterpreter(CustomUniversalAgent.agent_index, self, initial_state)

        CustomUniversalAgent.agent_index += 1

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        actions = game_state.get_legal_actions(self.index)

        next_move = self.interpreter.compute_next_move(GameData(
            actions,
            game_state,
            self.get_food(game_state).as_list(),
            game_state.get_agent_position(self.index),
            game_state.get_agent_state(self.index).is_pacman,
            [
                {
                    "pos": s.get_position(),
                    "isPacman": s.is_pacman
                }
                for s in [
                    game_state.get_agent_state(i)
                    for i in self.get_opponents(game_state)
                ]
            ],
            game_state.get_walls().as_list()
        ))

        if next_move is None:
            print("Next move is none?")
            return random.choice(actions)

        stringed_move = next_move.__str__().strip()
        print("Next move is ", stringed_move)
        return stringed_move

class Position:

    @staticmethod
    def from_tuple(origin):
        return Position(origin[0], origin[1])

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def to_tuple(self):
        return self.x, self.y

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
    DEPOSITING_FOOD = auto()
    OFFENSIVE_FLEEING = auto()  # When we're on the opponents side
    DEFENSIVE_FLEEING = auto()  # When we're on home territory
    DEFENDING = auto()
    ATTACKING = auto()


class GameData:

    def __init__(self, legal_moves, game_state, food_positions, current_position, is_pacman, enemies, walls):
        self.legal_moves = legal_moves
        self.game_state = game_state
        self.food_positions = food_positions
        self.current_position = Position.from_tuple(current_position)
        self.is_pacman = is_pacman
        self.enemies = enemies
        self.walls = walls

class GameInterpreter:

    def __init__(self, agent_id, parent, initial_state):
        self.agent_id = agent_id
        self.parent = parent
        self.game_data = None
        self.game_state = initial_state
        self.previous_game_state = None
        self.previous_game_data = None
        self.position_path = None
        self.last_safe_position = None
        self.starting_position = None
        self.previous_position = None
        self.collected_food = 0

    def set_game_state(self, new_state):
        self.previous_game_state = self.game_state
        self.game_state = new_state

    def set_position_path(self, path, reason):
        if path is not None:
            print("Set new position with destination '", path.destination, "' and reason ", reason)
        else:
            print("Set new position with reason ", reason)

        self.position_path = path

    def is_position_safe(self, position):
        if position is None:
            return False

        return position.x > 16  # TODO: Switch based on team color

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

    def get_distance(self, from_position, to_position):
        return self.parent.get_maze_distance(from_position.to_tuple(), to_position.to_tuple())

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

    def get_valid_defensive_enemy(self, game_data, distance_threshold):
        current_position = game_data.current_position
        enemies = game_data.enemies

        for enemy in enemies:
            enemy_position = enemy["pos"]

            if enemy_position is None or self.is_position_safe(Position.from_tuple(enemy_position)):
                continue

            distance = self.get_distance(current_position, Position.from_tuple(enemy_position))

            if distance > distance_threshold:
                continue

            return enemy

        return None

    def get_valid_offensive_enemy(self, game_data):
        enemies = game_data.enemies

        for enemy in enemies:
            enemy_position = enemy["pos"]

            if enemy_position is None or not self.is_position_safe(Position.from_tuple(enemy_position)):
                continue

            return enemy

        return None

    def get_random_close(self, game_data, origin, max_distance):
        empty_spaces = game_data.empty_spaces

        for _ in range(50):
            candidate = random.choice(empty_spaces)

            if candidate == origin:
                continue

            if not self.is_position_valid(game_data.game_state, candidate) or not self.is_position_safe(candidate):
                continue

            if candidate.x > game_data.spawn_treshold:
                continue

            distance = self.get_distance(origin, candidate)

            if distance == -1 or distance > max_distance:
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
        self.handle_finding_food()
        self.handle_deposit_food()
        self.handle_offensive_fleeing()
        self.handle_defensive_fleeing()
        self.handle_defending()
        self.handle_attacking()

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

    def handle_finding_food(self):
        remaining_food = self.game_data.food_positions
        current_position = self.game_data.current_position
        closest_food_entry = self.get_closest_food(current_position, self.game_data.food_positions)

        if self.game_state is not GameState.FINDING_FOOD and self.game_state is not GameState.DEPOSITING_FOOD:
            return

        if len(remaining_food) == 0 and (self.position_path is None or self.position_path.is_completed()):
            closest_safe = self.get_closest_safe_position(current_position)

            if closest_safe is not None:
                self.set_position_path(closest_safe, "All food has been consumed, returning home")

            return

        is_food_square = self.previous_game_data is not None and Position.to_tuple(current_position) in self.previous_game_data.food_positions
        if is_food_square:
            self.collected_food += 1

        if self.collected_food >= 5 and (closest_food_entry is not None and closest_food_entry[1] >= 2):
            self.set_game_state(GameState.DEPOSITING_FOOD)
            return

        if self.position_path is not None and not self.position_path.is_completed or closest_food_entry is None:
            return

        self.set_position_path(PositionPath(self.game_data, current_position, Position.from_tuple(closest_food_entry[0])), "New food found")

    def handle_deposit_food(self):
        current_position = self.game_data.current_position

        if self.collected_food > 0 and self.is_position_safe(current_position):
            self.collected_food = 0

        if self.game_state is not GameState.DEPOSITING_FOOD:
            return

        if self.position_path is None:
            closest_safe = self.get_closest_safe_position(current_position)

            if closest_safe is not None:
                self.set_position_path(closest_safe, "Depositing food")

            return

        if not self.position_path.is_completed():
            return

        self.set_position_path(None, "Clearing position path, deposited food")
        self.set_game_state(GameState.FINDING_FOOD)

    def handle_offensive_fleeing(self):
        current_position = self.game_data.current_position

        if self.game_state is GameState.OFFENSIVE_FLEEING and (self.position_path is None or self.position_path.is_completed()):
            self.set_game_state(self.previous_game_state)
            return

        valid_enemy = self.get_valid_defensive_enemy(self.game_data, 3)
        print(valid_enemy)

        if valid_enemy is not None and not valid_enemy["isPacman"] and self.game_data.is_pacman:
            self.set_position_path(PositionPath(self.game_data, current_position, Position.from_tuple(valid_enemy["pos"])), "Pursuing enemy due to becoming a pacman")
            self.set_game_state(GameState.ATTACKING)
            return

        if valid_enemy is None or self.game_state is GameState.OFFENSIVE_FLEEING or self.game_state is GameState.DEFENDING:
            return

        closest_safe = self.get_closest_safe_position(current_position)
        if closest_safe is not None:
            self.set_position_path(closest_safe, "Enemy found, fleeing (Offensive)")

        self.set_game_state(GameState.OFFENSIVE_FLEEING)

    def handle_defensive_fleeing(self):
        current_position = self.game_data.current_position
        if self.game_state is GameState.DEFENSIVE_FLEEING and self.position_path is None:
            self.set_game_state(self.previous_game_state)
            return

        valid_enemy = self.get_valid_offensive_enemy(self.game_data)
        if valid_enemy is None or valid_enemy["isPacman"]:
            return

        closest_safe = self.get_closest_safe_position(current_position)
        if closest_safe is not None:
            self.set_position_path(closest_safe, "Enemy found, fleeing (Defensive)")

        self.set_game_state(GameState.DEFENSIVE_FLEEING)

    def handle_defending(self):
        if self.game_state is not GameState.DEFENDING:
            return

        current_position = self.game_data.current_position
        if not self.is_position_safe(current_position):
            self.set_position_path(PositionPath(self.game_data, current_position, self.last_safe_position), "Moving to defense")

        if self.position_path is not None and not self.position_path.is_completed():
            updated_valid_enemy = self.get_valid_offensive_enemy(self.game_data)

            if updated_valid_enemy is not None and not updated_valid_enemy["isPacman"]:
                self.set_position_path(PositionPath(self.game_data, current_position, Position.from_tuple(updated_valid_enemy.pos)), "Moving to chase")

            return

        nearby_enemy = self.get_valid_offensive_enemy(self.game_data)
        if nearby_enemy is not None:
            self.set_position_path(PositionPath(self.game_data, current_position, Position.from_tuple(nearby_enemy.pos)), "Chasing enemy in home territory")
            return

        random_defending_position = self.get_random_close(self.game_data, current_position, 15)
        if random_defending_position is None:
            return

        self.set_position_path(PositionPath(self.game_data, current_position, random_defending_position), "Moving to a new defensive position")

    def handle_attacking(self):
        if self.game_state is not GameState.ATTACKING:
            return

        current_position = self.game_data.current_position
        valid_enemy = self.get_valid_defensive_enemy(self.game_data, 15)
        if valid_enemy is None:
            self.set_game_state(self.previous_game_state)
            return

        self.set_position_path(PositionPath(self.game_data, current_position, Position.from_tuple(valid_enemy["pos"])), "Attacking enemy in home terrority")