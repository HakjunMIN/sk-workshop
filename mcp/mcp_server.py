from flask import Flask, request, jsonify

app = Flask(__name__)

# MCP 서버에서 제공할 도구 목록
tools = [
    {"name": "echo", "description": "Echoes the input text."},
    {"name": "reverse", "description": "Reverses the input text."}
]

@app.route('/tools', methods=['GET'])
def list_tools():
    return jsonify({"tools": tools})

@app.route('/execute', methods=['POST'])
def execute_tool():
    data = request.json
    tool_name = data.get("tool")
    input_text = data.get("input")

    if tool_name == "echo":
        return jsonify({"result": input_text})
    elif tool_name == "reverse":
        return jsonify({"result": input_text[::-1]})
    else:
        return jsonify({"error": "Tool not found"}), 404

if __name__ == '__main__':
    app.run(port=5000)
