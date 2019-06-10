from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)

    @app.route("/hello")
    def hello():
        return "hello world"

    @app.route("/mirror", methods=['POST'])
    def mirror():
        return jsonify(request.json)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, threaded=True, host="0.0.0.0")
