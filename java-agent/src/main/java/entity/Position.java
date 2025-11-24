package entity;

public record Position(int x, int y) {

    public Position setY(int y) {
        return new Position(this.x(), y);
    }

    public Position add(int x, int y) {
        return new Position(this.x() + x, this.y() + y);
    }

    public int distance(Position other) {
        return Math.abs(this.x - other.x) + Math.abs(this.y - other.y);
    }

    @Override
    public boolean equals(Object other) {
        if (!(other instanceof Position position)) {
            return false;
        }

        return this.x == position.x() && this.y == position.y();
    }
}