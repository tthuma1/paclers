package interpreter;

import data.GameData;
import entity.Pair;
import entity.Position;
import entity.request.DistanceRequest;
import enums.Direction;
import enums.GameState;
import enums.Request;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ThreadLocalRandom;

public class GameInterpreter {
    private final Interpreter interpreter;

    private GameState gameState = GameState.ATTACKING;
    private Direction previousMove;
    private Position targetPosition;
    private int distanceToPosition;

    public GameInterpreter(Interpreter interpreter) {
        this.interpreter = interpreter;
    }

    public String handleMove(GameData gameData) {
        System.out.println("Handle Move was called, parsing (moves till goal '" + this.distanceToPosition + "')");
        final List<Direction> legalMoves = gameData.getLegalDirections();

        // Handles the case when we're attacking
        final Pair<Direction, Integer> attackingHandle = this.handleAttack(gameData, legalMoves);
        if (attackingHandle != null) {
            System.out.println("Attacking handle wasn't null, returning (" +  attackingHandle + ")");

            this.distanceToPosition = attackingHandle.getSecond();
            this.previousMove = attackingHandle.getFirst();
            return attackingHandle.getFirst().toString();
        }

        final Direction optimalMove = this.getMostOptimalDirection(legalMoves);
        System.out.println("Returning move '" + optimalMove + "'");
        this.previousMove = optimalMove;
        return optimalMove.toString();
    }

    // Returns the current states direction, and required moves for it
    private Pair<Direction, Integer> handleAttack(GameData gameData, List<Direction> legalMoves) {
        if (this.gameState != GameState.ATTACKING) {
            return null;
        }

        if (this.distanceToPosition <= 0) {
            this.targetPosition = null;
            this.distanceToPosition = 0;
        }

        final Position currentPosition = gameData.getAgentPosition();

        // Go towards the closest food
        if (this.targetPosition == null) {
            final Pair<Position, Integer> closestFoodEntry = this.getClosestFood(gameData);
            if (closestFoodEntry == null) {
                throw new RuntimeException("No closed food found");
            }

            final Position closestFood = closestFoodEntry.getFirst();
            final int distanceToFood = closestFoodEntry.getSecond();

            this.targetPosition = closestFood;
            this.distanceToPosition = distanceToFood;
        }

        Pair<Direction, Integer> towardsTargetEntry = null;
        for (final Direction direction : Direction.VALUES) {
            if (!legalMoves.contains(direction)) {
                System.out.println("Direction " + direction + " not in legalMoves");
                continue;
            }

            final Position updatedPosition = direction.applyModifier(currentPosition);
            if (!gameData.isPositionValid(updatedPosition)) {
                System.out.println("Position " + updatedPosition + " is invalid");
                continue;
            }

            final int distance = this.getDistance(updatedPosition, this.targetPosition);
            // If the distance is more than the previous one, it's a bad move
            if (distance > this.distanceToPosition) {
                continue;
            }

            if (towardsTargetEntry == null) {
                towardsTargetEntry = new Pair<>(direction, distance);
                continue;
            }

            if (towardsTargetEntry.getSecond() > distance) {
                continue;
            }

            towardsTargetEntry = new Pair<>(direction, distance);
        }

        System.out.println("Next Move: " + towardsTargetEntry);
        return towardsTargetEntry;
    }

    /**
     * features = util.Counter()
     * successor = self.get_successor(game_state, action)
     * print("Successor ", successor)
     * <p>
     * features['successor_score'] = self.get_score(successor)
     * <p>
     * agent_position = game_state.get_agent_position(self.index)
     * <p>
     * invaders = self.get_invaders(successor)
     * features['invader_count'] = len(invaders)
     * <p>
     * closest_invader = self.get_closest_invader(agent_position, invaders)
     * if closest_invader is not None:
     * features['flee_factor'] = -10
     * <p>
     * food_list = self.get_food(successor).as_list()
     * if len(food_list) > 0:
     * my_pos = successor.get_agent_state(self.index).get_position()
     * min_distance = min([self.get_maze_distance(my_pos, food) for food in food_list])
     * features['distance_to_food'] = min_distance
     */

    public String handleGetFeatures(GameData gameData) {
        System.out.println("Get Features was called, parsing");
        final Pair<Position, Integer> closestFood = this.getClosestFood(gameData);

        return Interpreter.GSON.toJson(Map.of(
            "distance_to_food", closestFood == null ? 0 : closestFood.getSecond(),
            "closest_food_position", closestFood == null ? "null" : closestFood.getFirst()
        ));
    }

    private Direction getMostOptimalDirection(List<Direction> legalMoves) {
        legalMoves.remove(Direction.STOP); // Remove stop since we want to actually move right now

        if (this.previousMove != null && legalMoves.contains(this.previousMove)) {
            return this.previousMove;
        }

        if (legalMoves.isEmpty()) {
            return Direction.STOP;
        }

        return legalMoves.get(ThreadLocalRandom.current().nextInt(legalMoves.size()));
    }

    private Pair<Position, Integer> getClosestFood(GameData gameData) {
        final Position agentPosition = gameData.getAgentPosition();
        final Map<Position, Integer> mappedPositions = new HashMap<>();

        for (final Position position : gameData.getFoodPositions()) {
            final int distance = this.getDistance(agentPosition, position);
            mappedPositions.put(position, distance);
        }

        final Optional<Map.Entry<Position, Integer>> closest = mappedPositions.entrySet().stream().min(Comparator.comparingInt(Map.Entry::getValue));
        if (closest.isEmpty()) {
            return null;
        }

        final Map.Entry<Position, Integer> closestFoodEntry = closest.get();
        return new Pair<>(closestFoodEntry.getKey(), closestFoodEntry.getValue());
    }

    private int getDistance(Position first, Position second) {
        final DistanceRequest request = new DistanceRequest(first, second);
        return this.interpreter.callPython(Request.DISTANCE_REQUEST, request);
    }
}