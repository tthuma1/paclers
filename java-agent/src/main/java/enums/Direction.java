package enums;

public enum Direction {

    NORTH,
    SOUTH,
    EAST,
    WEST,
    STOP;

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