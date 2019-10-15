import os
import json
import glob

from flask import Flask, jsonify
from flask_cors import cross_origin

from skedulord.common import HEARTBEAT_PATH, SKEDULORD_PATH


def create_app():
    app = Flask(__name__, static_folder='templates', static_url_path='')

    @app.route('/')
    def static_file():
        return app.send_static_file("index.html")

    @app.route('/logo.png')
    def logo():
        return app.send_static_file("logo.png")

    @app.route("/api/heartbeats")
    @cross_origin()
    def grab():
        with open(HEARTBEAT_PATH, "r") as f:
            jobs = sorted([json.loads(_) for _ in f.readlines()], key=lambda d: d['start'], reverse=True)
            names = set([_['name'] for _ in jobs])
            return jsonify([{"name": n,
                             "id": i,
                             "jobs": [j for j in jobs if j['name'] == n]} for i, n in enumerate(names)])

    @app.route("/api/test_heartbeats")
    def grab_test():
        # the @cross_origin is messing up the tests =(
        with open(HEARTBEAT_PATH, "r") as f:
            jobs = sorted([json.loads(_) for _ in f.readlines()], key=lambda d: d['start'], reverse=True)
            names = set([_['name'] for _ in jobs])
            return jsonify([{"name": n,
                             "id": i,
                             "jobs": [j for j in jobs if j['name'] == n]} for i, n in enumerate(names)])

    @app.route("/api/jobs/<job>/<datetime>")
    @cross_origin()
    def fetch_logs(job, datetime):
        path = os.path.join(SKEDULORD_PATH, "jobs", job, datetime)
        with open(path) as f:
            return f"<pre>{f.read()}</pre>"

    @app.route("/api/glob_logs")
    @cross_origin()
    def glob_logs():
        return jsonify([_.replace(SKEDULORD_PATH, "") for _ in glob.glob(f"{SKEDULORD_PATH}/jobs/*/*.txt")])

    return app


if __name__ == "__main__":
    web = create_app()
    web.run(debug=True, threaded=True, host="0.0.0.0")
