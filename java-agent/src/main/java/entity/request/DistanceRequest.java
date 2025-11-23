package entity.request;

import entity.Position;

public class DistanceRequest {
    private final Position position1;
    private final Position position2;

    public DistanceRequest(Position position1, Position position2) {
        this.position1 = position1;
        this.position2 = position2;
    }

    public Position getPosition1() {
        return this.position1;
    }

    public Position getPosition2() {
        return this.position2;
    }
}