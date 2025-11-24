package data;

import com.google.gson.annotations.SerializedName;
import data.gson.EnemyData;
import entity.Position;
import enums.Direction;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

public class GameData {
    @SerializedName("legal_actions")
    private List<String> legalActions;
    private List<Integer> position;
    private int score;
    private List<List<Integer>> food;
    @SerializedName("defending_food")
    private List<List<Integer>> defendingFood;
    private List<EnemyData> enemies;
    private List<List<Integer>> walls;

    public GameData(List<String> legalActions) {
        this.legalActions = legalActions;
    }

    public List<String> getLegalActions() {
        return this.legalActions;
    }

    public int getScore() {
        return this.score;
    }

    public List<Direction> getLegalDirections() {
        return new ArrayList<>(this.legalActions.stream().map(String::toUpperCase).map(Direction::valueOf).toList());
    }

    public Position getAgentPosition() {
        return new Position(this.position.get(0), this.position.get(1));
    }

    public List<Position> getFoodPositions() {
        return this.food.stream().map((it) -> new Position(it.get(0), it.get(1))).toList();
    }

    public List<Position> getDefendingFoodPositions() {
        return this.defendingFood.stream().map((it) -> new Position(it.get(0), it.get(1))).toList();
    }

    public List<EnemyData> getEnemies() {
        return this.enemies;
    }

    public List<Position> getWallPositions() {
        return this.walls.stream().map((it) -> new Position(it.get(0), it.get(1))).toList();
    }

    public boolean isPositionValid(Position position) {
        if (position.x() >= 32 || position.y() >= 32 || position.x() < 0 || position.y() < 0) {
            return false;
        }

        return !this.getWallPositions().contains(position);
    }

    // TODO: Define based on the team color
    public boolean isPositionSafe(Position position) {
        return position.x() > 16;
    }

    public int getSpawnThreshold() {
        return 29;
    }

    @Override
    public String toString() {
        return "GameData[legalActions=%s,position=%s,score=%s,food=%s,enemies=%s,walls=%s]".formatted(
            this.legalActions,
            this.position,
            this.score,
            this.food,
            this.enemies,
            this.walls
        );
    }
}