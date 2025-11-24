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
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

public class GameInterpreter {
    private final Interpreter interpreter;
    private final Map<GameState, Consumer<GameData>> registeredGameStates;

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

        this.registeredGameStates = new ConcurrentHashMap<>() {{
            this.put(GameState.FINDING_FOOD, GameInterpreter.this::handleFindingFood);
            this.put(GameState.DEPOSITING_FOOD, GameInterpreter.this::handleDepositFood);
            this.put(GameState.FLEEING, GameInterpreter.this::handleFleeing);
            this.put(GameState.DEFENDING, GameInterpreter.this::handleDefending);
            this.put(GameState.ATTACKING, GameInterpreter.this::handleAttacking);
        }};
    }

    private void setGameState(GameState gameState) {
        if (!this.registeredGameStates.containsKey(gameState)) {
            return;
        }

        this.previousGameState = this.gameState;
        this.gameState = gameState;
    }

    private void setPositionPath(PositionPath positionPath, String reason) {
        this.positionPath = positionPath;
        System.out.println("Set new position with reason '" + reason + "'");
    }

    public Direction handleMove(GameData gameData) {
        final List<Direction> legalMoves = gameData.getLegalDirections();
        final Position currentPosition = gameData.getAgentPosition();
        if (this.startingPosition == null) {
            this.startingPosition = currentPosition;
        }

        if (gameData.isPositionSafe(currentPosition) && !currentPosition.equals(this.lastSafePosition)) {
            this.lastSafePosition = currentPosition;
        }

        // Handles resetting of goals if we died
        this.handleDeath(gameData);

        for (final Map.Entry<GameState, Consumer<GameData>> entry : this.registeredGameStates.entrySet()) {
            final Consumer<GameData> stateConsumer = entry.getValue();
            stateConsumer.accept(gameData);
        }

        if (!this.registeredGameStates.containsKey(this.gameState)) {
            throw new RuntimeException("Tried to use a game state which is not registered? " + this.gameState);
        }

        if (this.positionPath != null) {
            final Position nextStep = this.positionPath.step();
            if (nextStep != null) {
                final Direction move = Direction.fromPosition(currentPosition, nextStep);
                if (move != null && legalMoves.contains(move)) {

                    this.previousPosition = currentPosition;
                    this.previousData = gameData;
                    return move;
                }
            }

            this.setPositionPath(null, "Current finished, clearing");
        }

        // Fallback
        this.previousPosition = currentPosition;
        this.previousData = gameData;
        System.out.println("Fallback move (State=" + this.gameState + ")");
        return Direction.STOP;
    }

    private void handleFindingFood(GameData gameData) {
        final int remainingFood = gameData.getFoodPositions().size();
        final int remainingDefendingFood = gameData.getDefendingFoodPositions().size();

        final Pair<Position, Integer> closestFoodEntry = this.getClosestFood(gameData);
        if (this.gameState != GameState.FINDING_FOOD && this.gameState != GameState.DEPOSITING_FOOD) {
            return;
        }

        // When we're winning, and we have more food than the enemy, move to defense
        // TODO: Currently just start defending once we have some points
        if (gameData.getScore() > 0 && gameData.isPositionSafe(gameData.getAgentPosition()) /*&& remainingDefendingFood > remainingFood*/) {
            if (this.registeredGameStates.containsKey(GameState.DEFENDING)) {
                //this.registeredGameStates.remove(GameState.FINDING_FOOD);
                //this.registeredGameStates.remove(GameState.DEPOSITING_FOOD);

                this.setGameState(GameState.DEFENDING);
                return;
            }
        }

        if (remainingFood == 0 && (this.positionPath == null || this.positionPath.isCompleted())) {
            final PositionPath closestSafe = this.getClosestSafePosition(gameData);
            if (closestSafe != null) {
                this.setPositionPath(closestSafe, "All food has been consumed, returning home");
            }

            return;
        }

        final Position currentPosition = gameData.getAgentPosition();
        final boolean isFoodSquare = this.previousData != null && this.previousData.getFoodPositions().contains(currentPosition);
        if (isFoodSquare) {
            this.collectedFood++;
        }

        // If we've collected 5 food, and we don't have any new food directly next to us (gluttony is a sin)
        if (this.collectedFood >= 5 && (closestFoodEntry != null && closestFoodEntry.getSecond() >= 2)) {
            this.setGameState(GameState.DEPOSITING_FOOD);
            return;
        }

        if (this.positionPath != null && !this.positionPath.isCompleted() || closestFoodEntry == null) {
            return;
        }

        final Position closestFood = closestFoodEntry.getFirst();
        this.setPositionPath(new PositionPath(gameData, currentPosition, closestFood), "New food found (" + closestFood + ")");
        this.previousFoodPosition = closestFood;
    }

    private void handleDepositFood(GameData gameData) {
        final Position currentPosition = gameData.getAgentPosition();

        // When our goal isn't explicitly a deposit, however we still return food
        if (this.collectedFood > 0 && gameData.isPositionSafe(currentPosition)) {
            this.collectedFood = 0;
        }

        if (this.gameState != GameState.DEPOSITING_FOOD) {
            return;
        }

        // Deposit the food to the last safe position; TODO: Find the closest safe position instead
        if (this.positionPath == null) {
            final PositionPath closestSafe = this.getClosestSafePosition(gameData);
            if (closestSafe != null) {
                this.setPositionPath(closestSafe, "Depositing food");
            }
            return;
        }

        if (!this.positionPath.isCompleted()) {
            return;
        }

        this.setPositionPath(null, "Clearing position path, deposited food");
        this.collectedFood = 0;
        this.setGameState(GameState.FINDING_FOOD);
    }

    private void handleFleeing(GameData gameData) {
        final Position currentPosition = gameData.getAgentPosition();
        if (this.gameState == GameState.FLEEING) {
            if (this.positionPath == null) {
                this.setGameState(this.previousGameState);
            }
            return;
        }

        final EnemyData validEnemy = this.getValidDefensiveEnemy(gameData, currentPosition);
        if (validEnemy == null || this.gameState == GameState.FLEEING) {
            return;
        }

        if (this.gameState == GameState.DEFENDING) {
            return;
        }

        // TODO: Find the enemies path and avoid it
        final PositionPath closestSafe = this.getClosestSafePosition(gameData);
        if (closestSafe != null) {
            this.setPositionPath(closestSafe, "Enemy found, fleeing");
        }

        this.setGameState(GameState.FLEEING);
    }

    private void handleDefending(GameData gameData) {
        if (this.gameState != GameState.DEFENDING) {
            return;
        }

        final Position currentPosition = gameData.getAgentPosition();
        // If we're not on our side of the map, we want to return to base
        if (!gameData.isPositionSafe(currentPosition)) {
            this.setPositionPath(new PositionPath(gameData, currentPosition, this.lastSafePosition), "Moving to defense");
            return;
        }

        // Already have an active goal
        if (this.positionPath != null && !this.positionPath.isCompleted()) {
            return;
        }

        final EnemyData nearbyEnemy = this.getValidOffensiveEnemy(gameData);
        System.out.println("Nearby enemy in home territory: " + nearbyEnemy);

        if (nearbyEnemy != null) {
            final PositionPath pathToEnemy = new PositionPath(gameData, currentPosition, nearbyEnemy.getPosition());
            this.setPositionPath(pathToEnemy, "Chasing enemy in home territory");
            return;
        }

        final Position randomDefendingPosition = this.getRandomClose(gameData, currentPosition, 15);
        if (randomDefendingPosition == null) {
            System.out.println("Random defending position is null");
            return;
        }

        this.setPositionPath(new PositionPath(gameData, currentPosition, randomDefendingPosition), "Moving to a new defensive position");
    }

    private void handleAttacking(GameData gameData) {

    }

    private EnemyData getValidDefensiveEnemy(GameData gameData, Position currentPosition) {
        final List<EnemyData> enemies = gameData.getEnemies();
        for (final EnemyData enemy : enemies) {
            final Position enemyPosition = enemy.getPosition();
            // Enemy position is unknown
            if (enemyPosition == null || gameData.isPositionSafe(enemyPosition)) {
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

    private EnemyData getValidOffensiveEnemy(GameData gameData) {
        final List<EnemyData> enemies = gameData.getEnemies();
        for (final EnemyData enemy : enemies) {
            final Position enemyPosition = enemy.getPosition();
            if (enemyPosition == null || !gameData.isPositionSafe(enemyPosition)) {
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

        System.out.println("Agent got munched");
        this.gameState = GameState.FINDING_FOOD;
        this.setPositionPath(null, "Agent died, clearing");
        this.lastSafePosition = null;
        this.previousPosition = null;
        this.previousData = null;
        this.collectedFood = 0;
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

        final Optional<Map.Entry<Position, Integer>> closest = mappedPositions.entrySet().stream().min(Comparator.comparingInt(Map.Entry::getValue));
        if (closest.isEmpty()) {
            return null;
        }

        final Map.Entry<Position, Integer> closestFoodEntry = closest.get();
        return new Pair<>(closestFoodEntry.getKey(), closestFoodEntry.getValue());
    }

    private int getDistance(Position first, Position second) {
        final DistanceRequest request = new DistanceRequest(first, second);
        final Integer distance = this.interpreter.callPython(Request.DISTANCE_REQUEST, request);
        return distance == null ? -1 : distance;
    }

    private PositionPath getClosestSafePosition(GameData gameData) {
        if (this.lastSafePosition == null) {
            return null;
        }

        final Position currentPosition = gameData.getAgentPosition();
        PositionPath closest = null;
        for (int y = 0; y < 32; y++) {
            final Position position = this.lastSafePosition.setY(y);
            if (!gameData.isPositionSafe(position) || !gameData.isPositionValid(position)) {
                continue;
            }

            final PositionPath positionPath = new PositionPath(gameData, currentPosition, position);
            if (positionPath.isEmpty()) {
                continue;
            }

            if (closest == null) {
                closest = positionPath;
                continue;
            }

            if (closest.getNeededSteps() > positionPath.getNeededSteps()) {
                closest = positionPath;
            }
        }

        System.out.println("Found closest safe position path: " + closest);
        return closest;
    }

    private Position getRandomClose(GameData gameData, Position origin, int maxDistance) {
        for (int i = 0; i < 20; i++) {
            final int dx = ThreadLocalRandom.current().nextInt(-maxDistance, maxDistance + 1);
            final int dy = ThreadLocalRandom.current().nextInt(-maxDistance, maxDistance + 1);
            if (dx == 0 && dy == 0) {
                continue;
            }

            final Position candidate = new Position(origin.x() + dx, origin.y() + dy);
            if (!gameData.isPositionValid(candidate) || !gameData.isPositionSafe(candidate)) {
                continue;
            }

            // Don't stay at direct spawn
            if (candidate.x() > gameData.getSpawnThreshold()) {
                continue;
            }

            final int distance = this.getDistance(origin, candidate);
            if (distance == -1 || distance > maxDistance) {
                continue;
            }

            return candidate;
        }

        return null;
    }
}