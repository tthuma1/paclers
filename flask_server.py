from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/distance", methods=["POST"])
def compute_distance():
    global agent_instance
    if agent_instance is None:
        return jsonify({"error": "Agent not initialized"}), 400

    data = request.get_json()
    pos1 = data["pos1"]
    pos2 = data["pos2"]

    dist = agent_instance.get_maze_distance(pos1, pos2)
    print("Returning distance: " + dist)
    return jsonify({"distance": dist})


def start_flask():
    app.run(host="127.0.0.1", port=5001)