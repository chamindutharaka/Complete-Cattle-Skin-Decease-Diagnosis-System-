# dl_service/simple_flask_test.py
from flask import Flask, jsonify

app = Flask(__name__)
PORT = 5001 # Using a different port

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello from simple Flask server!"})

if __name__ == '__main__':
    print(f"Simple Flask server starting on port {PORT}...")
    app.run(host='127.0.0.1', port=PORT, debug=False)
