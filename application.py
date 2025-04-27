from flask import Flask, render_template, request, jsonify
import shabbos_web_class
from ai_chat import SabbathAI

app = Flask(__name__)
chatbot = SabbathAI()

@app.route("/")
@app.route("/home")
def index():
    sabbath_info = shabbos_web_class.get_sabbath_info()
    return render_template(
        'index.html',
        sabbath_info=sabbath_info
    )

@app.route("/api/chat", methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    response = chatbot.get_response(data['message'])
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)