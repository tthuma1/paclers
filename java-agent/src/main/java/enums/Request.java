package enums;

public enum Request {

    DISTANCE_REQUEST("distance");

    private final String identifier;

    Request(String identifier) {
        this.identifier = identifier;
    }

    public String getIdentifier() {
        return this.identifier;
    }

}