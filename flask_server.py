from flask import Flask, request, jsonify

import agent_bridge

import logging
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)

@app.route("/distance", methods=["POST"])
def compute_distance():
    data = request.get_json()
    agent_index = data["agent_index"]

    if agent_bridge.agent_instance[agent_index] is None:
        return jsonify({"error": "Agent not initialized"}), 400

    positionData = data["value"]

    pos1 = (positionData["position1"]["x"], positionData["position1"]["y"])
    pos2 = (positionData["position2"]["x"], positionData["position2"]["y"])

    dist = agent_bridge.agent_instance[agent_index].get_maze_distance(pos1, pos2)
    return jsonify({"distance": dist})


def start_flask():
    app.run(host="127.0.0.1", port=5001)