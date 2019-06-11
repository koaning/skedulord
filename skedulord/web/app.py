import os
import json
import glob

from flask import Flask, jsonify, request

from skedulord.common import HEARTBEAT_PATH, SETTINGS_PATH


def create_app():
    app = Flask(__name__)

    @app.route("/heartbeats")
    def grab():
        with open(HEARTBEAT_PATH, "r") as f:
            return jsonify([json.loads(_) for _ in f.readlines()])

    @app.route("/logs/<job>/<datetime>")
    def fetch_logs(job, datetime):
        path = os.path.join(SETTINGS_PATH, "logs", job, datetime)
        with open(path) as f:
            return f.read()

    @app.route("/glob_logs")
    def glob_logs():
        return jsonify(glob.glob(f"{SETTINGS_PATH}/logs/*/*.txt"))

    @app.route("/mirror", methods=['POST'])
    def mirror():
        return jsonify(request.json)

    return app


if __name__ == "__main__":
    web = create_app()
    web.run(debug=True, threaded=True, host="0.0.0.0")
