from flask import Flask, request, jsonify

import agent_bridge

app = Flask(__name__)


@app.route("/distance", methods=["POST"])
def compute_distance():
    if agent_bridge.agent_instance is None:
        return jsonify({"error": "Agent not initialized"}), 400

    data = request.get_json()

    pos1 = (data["position1"]["x"], data["position1"]["y"])
    pos2 = (data["position2"]["x"], data["position2"]["y"])

    dist = agent_bridge.agent_instance.get_maze_distance(pos1, pos2)
    return jsonify({"distance": dist})


def start_flask():
    app.run(host="127.0.0.1", port=5001)