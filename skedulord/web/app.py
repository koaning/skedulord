import os
import json
import glob

from flask import Flask, jsonify, request, render_template
from flask_cors import cross_origin

from skedulord.common import HEARTBEAT_PATH, SETTINGS_PATH


def create_app():
    app = Flask(__name__, static_folder='templates', static_url_path='')

    def all_data():
        with open(HEARTBEAT_PATH, "r") as f:
            data = [json.loads(_) for _ in f.readlines()]
            blob = {}
            keys = set(_['command'] for _ in data)
            for k in keys:
                blob[k] = [_ for _ in data if _['command'] == k]
            return blob

    @app.route('/')
    def static_file():
        print(f"{app.static_folder}")
        return app.send_static_file("index.html")

    @app.route("/api/heartbeats")
    @cross_origin()
    def grab():
        with open(HEARTBEAT_PATH, "r") as f:
            jobs = [json.loads(_) for _ in f.readlines()]
            commands = set([_['command'] for _ in jobs])
            return jsonify([{'command': c, "jobs": [j for j in jobs if j['command'] == c]} for c in commands])

    @app.route("/api/logs/<job>/<datetime>")
    @cross_origin()
    def fetch_logs(job, datetime):
        path = os.path.join(SETTINGS_PATH, "logs", job, datetime)
        with open(path) as f:
            return f"<pre>{f.read()}</pre>"

    @app.route("/api/glob_logs")
    @cross_origin()
    def glob_logs():
        return jsonify(glob.glob(f"{SETTINGS_PATH}/logs/*/*.txt"))

    @app.route("/api/mirror", methods=['POST'])
    @cross_origin()
    def mirror():
        return jsonify(request.json)

    return app


if __name__ == "__main__":
    web = create_app()
    web.run(debug=True, threaded=True, host="0.0.0.0")