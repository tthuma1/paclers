package entity;

import java.util.List;

public class EnemyData {
    private List<Integer> pos;
    private boolean isPacman;

    public EnemyData(List<Integer> pos, boolean isPacman) {
        this.pos = pos;
        this.isPacman = isPacman;
    }

    public List<Integer> getPos() {
        return this.pos;
    }

    public boolean isPacman() {
        return this.isPacman;
    }

    @Override
    public String toString() {
        return "EnemyData[pos=%s,isPacman=%s]".formatted(this.pos, this.isPacman);
    }
}