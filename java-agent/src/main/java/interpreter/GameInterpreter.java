package interpreter;

import data.GameData;
import entity.Position;
import entity.request.DistanceRequest;
import enums.Direction;
import enums.Request;

public class GameInterpreter {
    private final Interpreter interpreter;

    public GameInterpreter(Interpreter interpreter) {
        this.interpreter = interpreter;
    }

    public String handleMove(GameData gameData) {
        final DistanceRequest request = new DistanceRequest(new Position(0, 0), new Position(1, 1));
        System.out.println(this.interpreter.callPython(Request.DISTANCE_REQUEST, request));

        //System.out.println(gameData.toString());
        return Direction.NORTH.toString();
    }

    /**
     * features = util.Counter()
     * successor = self.get_successor(game_state, action)
     * print("Successor ", successor)
     * <p>
     * features['successor_score'] = self.get_score(successor)
     * <p>
     * agent_position = game_state.get_agent_position(self.index)
     * <p>
     * invaders = self.get_invaders(successor)
     * features['invader_count'] = len(invaders)
     * <p>
     * closest_invader = self.get_closest_invader(agent_position, invaders)
     * if closest_invader is not None:
     * features['flee_factor'] = -10
     * <p>
     * food_list = self.get_food(successor).as_list()
     * if len(food_list) > 0:
     * my_pos = successor.get_agent_state(self.index).get_position()
     * min_distance = min([self.get_maze_distance(my_pos, food) for food in food_list])
     * features['distance_to_food'] = min_distance
     */

    public String handleGetFeatures(GameData gameData) {
        final DistanceRequest request = new DistanceRequest(new Position(0, 0), new Position(1, 1));
        final String response = this.interpreter.callPython(Request.DISTANCE_REQUEST, request);
        System.out.println("Response from python: " + response);

        return "";
    }
}