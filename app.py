from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "chatapp123"
socketio = SocketIO(app)

# Store last 20 messages in memory
messages = []

@app.route("/")
def index():
    return render_template("index.html")

# When a user connects
@socketio.on("connect")
def handle_connect():
    # Send existing messages to the new user
    for msg in messages:
        emit("message", msg)

# When a user sends a message
@socketio.on("send_message")
def handle_message(data):
    msg = {
        "username": data["username"],
        "text": data["text"],
        "color": data["color"]
    }
    messages.append(msg)
    if len(messages) > 20:      # keep only last 20
        messages.pop(0)

    # Broadcast to ALL connected users
    emit("message", msg, broadcast=True)

# When a user joins the room
@socketio.on("user_joined")
def handle_join(data):
    emit("notification", {
        "text": f"{data['username']} joined the chat 👋"
    }, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000, debug=True, allow_unsafe_werkzeug=True)
