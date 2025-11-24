package interpreter;

import data.GameData;
import data.gson.EnemyData;
import entity.Pair;
import entity.Position;
import entity.PositionPath;
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

    private GameState gameState = GameState.FINDING_FOOD;
    private GameState previousGameState;
    private GameData previousData;
    private PositionPath positionPath;
    private Position lastSafePosition;
    private Position startingPosition;
    private Position previousPosition;
    private Position previousFoodPosition;
    private int collectedFood;

    public GameInterpreter(Interpreter interpreter) {
        this.interpreter = interpreter;
    }

    private void setGameState(GameState gameState) {
        this.previousGameState = this.gameState;
        System.out.println("Setting GameState to '" + gameState + "' (Previous = " + this.previousGameState + ")");
        this.gameState = gameState;
    }

    public Direction handleMove(GameData gameData) {
        final List<Direction> legalMoves = gameData.getLegalDirections();
        final Position currentPosition = gameData.getAgentPosition();
        if (this.startingPosition == null) {
            this.startingPosition = currentPosition;
        }

        // Handles resetting of goals if we died
        this.handleDeath(gameData);

        // Handles the case when we care about dying
        final Pair<Direction, Integer> fleeingHandle = this.handleFleeing(gameData, legalMoves);
        if (fleeingHandle != null) {
            this.previousPosition = currentPosition;
            this.previousData = gameData;
            return fleeingHandle.getFirst();
        }

        // Handles the case when we're finding food
        final Pair<Direction, Integer> findingFoodHandle = this.handleFindingFood(gameData, legalMoves);
        if (findingFoodHandle != null) {
            this.previousPosition = currentPosition;
            this.previousData = gameData;
            return findingFoodHandle.getFirst();
        }

        // Handles the case when we're depositing food
        final Pair<Direction, Integer> depositingHandle = this.handleDeposit(gameData, legalMoves);
        if (depositingHandle != null) {
            this.previousPosition = currentPosition;
            this.previousData = gameData;
            return depositingHandle.getFirst();
        }

        final PositionPath currentPath = this.positionPath;
        if (currentPath != null) {
            final Position nextStep = currentPath.step();
            // The path was completed, set it to null
            if (nextStep == null) {
                this.positionPath = null;
            }


        }



        final Direction defaultMove = legalMoves.get(ThreadLocalRandom.current().nextInt(legalMoves.size()));
        this.previousPosition = currentPosition;
        this.previousData = gameData;
        return defaultMove;
    }

    private Pair<Direction, Integer> handleFindingFood(GameData gameData, List<Direction> legalMoves) {
        if (this.gameState != GameState.FINDING_FOOD) {
            return null;
        }

        final Position currentPosition = gameData.getAgentPosition();
        if (this.distanceToPosition <= 0) {
            if (this.previousData != null && this.previousData.getFoodPositions().contains(currentPosition)) {
                this.collectedFood++;
                System.out.println("Collected food at '" + currentPosition + "' (total = " + this.collectedFood + ")");
            }

            this.targetPosition = null;
            this.distanceToPosition = 0;
        }

        if (this.collectedFood >= 5) {
            this.setGameState(GameState.DEPOSITING_FOOD);
            return null;
        }

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
            this.previousFoodPosition = closestFood;
        }

        return this.getNextLegalMove(gameData, currentPosition, legalMoves);
    }

    private Pair<Direction, Integer> handleDeposit(GameData gameData, List<Direction> legalMoves) {
        if (this.gameState != GameState.DEPOSITING_FOOD) {
            return null;
        }

        final Position currentPosition = gameData.getAgentPosition();
        if (this.targetPosition == null) {
            this.targetPosition = this.lastSafePosition;
            this.distanceToPosition = this.getDistance(gameData.getAgentPosition(), this.targetPosition);
        }

        if (this.distanceToPosition <= 0) {
            this.targetPosition = null;
            this.distanceToPosition = 0;
            this.collectedFood = 0;

            this.setGameState(GameState.FINDING_FOOD);
            return null;
        }

        return this.getNextLegalMove(gameData, currentPosition, legalMoves);
    }

    private Pair<Direction, Integer> handleFleeing(GameData gameData, List<Direction> legalMoves) {
        final Position currentPosition = gameData.getAgentPosition();
        if (currentPosition.x() > 16 && !currentPosition.equals(this.lastSafePosition)) { // TODO: No magic numbers
            this.lastSafePosition = currentPosition;
            return null;
        }

        final EnemyData validEnemy = this.getValidEnemy(gameData, currentPosition);
        if (validEnemy != null && this.gameState != GameState.FLEEING) {
            this.targetPosition = this.lastSafePosition;
            this.distanceToPosition = this.getDistance(gameData.getAgentPosition(), this.targetPosition);
            this.setGameState(GameState.FLEEING);
        }

        if (this.gameState == GameState.FLEEING && this.distanceToPosition == 0) {
            this.setGameState(this.previousGameState);
            return null;
        }

        return this.getNextLegalMove(gameData, currentPosition, legalMoves);
    }

    private EnemyData getValidEnemy(GameData gameData, Position currentPosition) {
        final List<EnemyData> enemies = gameData.getEnemies();
        for (final EnemyData enemy : enemies) {
            final Position enemyPosition = enemy.getPosition();
            // Enemy position is unknown
            if (enemyPosition == null || enemyPosition.x() > 16) { // TODO: No magic numbers
                continue;
            }

            final int distance = this.getDistance(currentPosition, enemyPosition);
            // If it's more than 3 squares away, ignore it
            if (distance > 3) {
                continue;
            }

            return enemy;
        }

        return null;
    }

    private void handleDeath(GameData gameData) {
        final Position currentPosition = gameData.getAgentPosition();
        if (this.previousPosition == null) {
            return;
        }

        // We moved a valid amount of distance from previous
        if (currentPosition.distance(this.previousPosition) <= 1) {
            return;
        }

        this.targetPosition = null;
        this.previousPosition = null;
        this.previousMove = null;
        this.previousData = null;
        this.distanceToPosition = 0;
        this.collectedFood = 0;
    }

    private Pair<Direction, Integer> getNextLegalMove(GameData gameData, Position currentPosition, List<Direction> legalMoves) {
        Pair<Direction, Integer> towardsTargetEntry = null;
        for (final Direction direction : Direction.VALUES) {
            if (!legalMoves.contains(direction)) {
                continue;
            }

            final Position updatedPosition = direction.applyModifier(currentPosition);
            if (!gameData.isPositionValid(updatedPosition)) {
                continue;
            }

            final int distance = this.getDistance(updatedPosition, this.targetPosition);
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

        return towardsTargetEntry;
    }

    private Pair<Position, Integer> getClosestFood(GameData gameData) {
        final Position agentPosition = gameData.getAgentPosition();
        final Map<Position, Integer> mappedPositions = new HashMap<>();

        for (final Position position : gameData.getFoodPositions()) {
            if (this.previousFoodPosition != null && this.previousFoodPosition.equals(position)) {
                continue; // If we've already targeted this position, move to a different one instead
            }

            final int distance = this.getDistance(agentPosition, position);
            mappedPositions.put(position, distance);
        }

        final Optional<Map.Entry<Position, Integer>> closest = mappedPositions.entrySet()
            .stream().min(Comparator.comparingInt(Map.Entry::getValue));
        if (closest.isEmpty()) {
            return null;
        }

        final Map.Entry<Position, Integer> closestFoodEntry = closest.get();
        return new Pair<>(closestFoodEntry.getKey(), closestFoodEntry.getValue());
    }

    private int getDistance(Position first, Position second) {
        final DistanceRequest request = new DistanceRequest(first, second);
        final Integer distance = this.interpreter.callPython(Request.DISTANCE_REQUEST, request);
        return distance == null ? Integer.MAX_VALUE : distance;
    }
}