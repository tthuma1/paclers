package entity;

import data.GameData;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

public class PositionPath {
    private final List<Position> positions;

    private int currentStep = 0;

    public PositionPath(GameData gameData, Position starting, Position ending) {
        this.positions = this.generatePositions(gameData, starting, ending);
    }

    public Position step() {
        if (this.currentStep > this.positions.size() - 1) {
            return null; // We've already completed the path
        }

        final Position position = this.positions.get(this.currentStep);
        this.currentStep++;
        return position;
    }

    private List<Position> generatePositions(GameData gameData, Position start, Position end) {
        final Set<Position> walls = new HashSet<>(gameData.getWallPositions());
        final List<Position> result = new ArrayList<>();

        // A* open and closed lists
        final PriorityQueue<Node> open = new PriorityQueue<>(Comparator.comparingInt(n -> n.fCost));
        final Map<Position, Node> allNodes = new HashMap<>();
        final Set<Position> closed = new HashSet<>();

        // Create start node
        final Node startNode = new Node(start, null, 0, this.manhattan(start, end));
        open.add(startNode);
        allNodes.put(start, startNode);

        while (!open.isEmpty()) {
            final Node current = open.poll();
            closed.add(current.position);

            // If we reached the end, reconstruct the path
            if (current.position.equals(end)) {
                Node node = current;
                while (node != null) {
                    result.add(0, node.position);
                    node = node.parent;
                }
                return result;
            }

            // Explore neighbors
            for (final Position neighborPos : this.getNeighbors(current.position)) {
                // Ignore walls and visited positions
                if (walls.contains(neighborPos) || closed.contains(neighborPos)) {
                    continue;
                }

                final int g = current.gCost + 1;
                Node neighborNode = allNodes.get(neighborPos);

                if (neighborNode == null) {
                    neighborNode = new Node(
                        neighborPos,
                        current,
                        g,
                        this.manhattan(neighborPos, end)
                    );
                    allNodes.put(neighborPos, neighborNode);
                    open.add(neighborNode);

                } else if (g < neighborNode.gCost) {
                    // Found a shorter path to this node
                    neighborNode.parent = current;
                    neighborNode.gCost = g;
                    neighborNode.fCost = g + neighborNode.hCost;

                    // Must re-insert to update position in priority queue
                    open.remove(neighborNode);
                    open.add(neighborNode);
                }
            }
        }

        // No path found
        return result;
    }

    private int manhattan(Position a, Position b) {
        return Math.abs(a.x() - b.x()) + Math.abs(a.y() - b.y());
    }

    private List<Position> getNeighbors(Position pos) {
        return List.of(
            new Position(pos.x() + 1, pos.y()),
            new Position(pos.x() - 1, pos.y()),
            new Position(pos.x(), pos.y() + 1),
            new Position(pos.x(), pos.y() - 1)
        );
    }

    private static class Node {
        Position position;
        Node parent;
        int gCost;
        int hCost;
        int fCost;

        Node(Position position, Node parent, int g, int h) {
            this.position = position;
            this.parent = parent;
            this.gCost = g;
            this.hCost = h;
            this.fCost = g + h;
        }
    }
}