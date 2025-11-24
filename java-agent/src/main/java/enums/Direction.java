package enums;

import entity.Position;
import java.util.Arrays;
import java.util.function.UnaryOperator;

public enum Direction {

    NORTH((position) -> position.add(0, 1)),
    SOUTH((position) -> position.add(0, -1)),
    EAST((position) -> position.add(1, 0)),
    WEST((position) -> position.add(-1, 0)),
    STOP(($) -> $);

    public static final Direction[] VALUES = Arrays.stream(values()).filter((it) -> it != STOP).toList().toArray(new Direction[0]);

    private final UnaryOperator<Position> modifier;

    Direction(UnaryOperator<Position> modifier) {
        this.modifier = modifier;
    }

    public static Direction fromPosition(Position from, Position to) {
        for (Direction direction : Direction.VALUES) {
            final Position directional = direction.applyModifier(from);
            System.out.println("Direction: " + direction + ", Directional: " + directional);

            if (directional.equals(to)) {
                return direction;
            }
        }

        return null;
    }

    public Position applyModifier(Position position) {
        return this.modifier.apply(position);
    }

    public String toString() {
        final StringBuilder builder = new StringBuilder();
        int index = 0;
        for (char character : this.name().toLowerCase().toCharArray()) {
            if (index == 0) {
                builder.append(String.valueOf(character).toUpperCase());
                index++;
                continue;
            }

            builder.append(character);
            index++;
        }


        return builder.toString();
    }

}