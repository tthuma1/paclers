package data;

import data.gson.EnemyData;
import entity.Position;
import enums.Direction;
import java.util.ArrayList;
import java.util.List;

public class GameData {
    private List<String> legalActions;
    private List<Integer> position;
    private int score;
    private List<List<Integer>> food;
    private List<EnemyData> enemies;
    private List<List<Integer>> walls;

    public GameData(List<String> legalActions) {
        this.legalActions = legalActions;
    }

    public List<String> getLegalActions() {
        return this.legalActions;
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

    public List<EnemyData> getEnemies() {
        return this.enemies;
    }

    public List<Position> getWallPositions() {
        return this.walls.stream().map((it) -> new Position(it.get(0), it.get(1))).toList();
    }

    public boolean isPositionValid(Position position) {
        return !this.getWallPositions().contains(position);
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