package data;

import entity.EnemyData;
import entity.Position;
import enums.Direction;
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
        return this.legalActions.stream().map(String::toUpperCase).map(Direction::valueOf).toList();
    }

    public List<Position> getFoodPositions() {
        return this.walls.stream().map((it) -> new Position(it.get(0), it.get(1))).toList();
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