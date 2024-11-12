from flask import Flask, jsonify, request

app = Flask(__name__)

# Example route
@app.route('/')
def home():
    return "Welcome to the Flask API!"

# API endpoint example to get data
@app.route('/api/data', methods=['GET'])
def get_data():
    sample_data = {"name": "Flask", "message": "Hello, World!"}
    return jsonify(sample_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)


