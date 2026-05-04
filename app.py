from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room as socket_leave

app = Flask(__name__)
app.config["SECRET_KEY"] = "chatapp123"
socketio = SocketIO(app)

GLOBAL_ROOM = "GLOBAL"
rooms      = { GLOBAL_ROOM: [] }
room_users = {}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join_room")
def handle_join(data):
    username  = data["username"]
    room_code = data["room_code"].upper().strip()
    color     = data["color"]
    sid       = data["sid"]

    if room_code not in rooms:
        rooms[room_code] = []
    if room_code not in room_users:
        room_users[room_code] = {}

    room_users[room_code][sid] = username
    join_room(room_code)

    for msg in rooms[room_code]:
        emit("message", msg)

    emit("notification", {
        "text": f"{username} joined {'the global chat' if room_code == GLOBAL_ROOM else 'room #' + room_code} 👋"
    }, room=room_code)

@socketio.on("leave_room")
def handle_leave(data):
    username  = data["username"]
    room_code = data["room_code"].upper().strip()

    socket_leave(room_code)

    emit("notification", {
        "text": f"{username} left the chat 🚪"
    }, room=room_code)

@socketio.on("send_message")
def handle_message(data):
    username  = data["username"]
    text      = data["text"]
    color     = data["color"]
    room_code = data["room_code"].upper().strip()

    msg = {"username": username, "text": text, "color": color}

    if room_code not in rooms:
        rooms[room_code] = []

    rooms[room_code].append(msg)
    if len(rooms[room_code]) > 50:
        rooms[room_code].pop(0)

    emit("message", msg, room=room_code)

# ── WebRTC Signaling ─────────────────────────────────────────

@socketio.on("call_request")
def handle_call_request(data):
    emit("incoming_call", {
        "from_user": data["username"],
        "from_sid":  request.sid,
        "room_code": data["room_code"]
    }, room=data["room_code"], include_self=False)

@socketio.on("call_accepted")
def handle_call_accepted(data):
    emit("call_accepted", {
        "from_user": data["username"],
        "from_sid":  request.sid
    }, to=data["to_sid"])

@socketio.on("call_rejected")
def handle_call_rejected(data):
    emit("call_rejected", {
        "from_user": data["username"]
    }, to=data["to_sid"])

@socketio.on("call_ended")
def handle_call_ended(data):
    for sid in data.get("peer_sids", []):
        emit("call_ended", {
            "from_user": data["username"],
            "from_sid":  request.sid
        }, to=sid)

@socketio.on("call_participant_joined")
def handle_participant_joined(data):
    for sid in data.get("notify_sids", []):
        emit("call_participant_joined", {
            "peer_sid":  data["peer_sid"],
            "peer_user": data["peer_user"]
        }, to=sid)

@socketio.on("webrtc_offer")
def handle_offer(data):
    emit("webrtc_offer", {
        "offer":     data["offer"],
        "from_user": data["username"],
        "from_sid":  request.sid
    }, to=data["to_sid"])

@socketio.on("webrtc_answer")
def handle_answer(data):
    emit("webrtc_answer", {
        "answer":    data["answer"],
        "from_sid":  request.sid
    }, to=data["to_sid"])

@socketio.on("webrtc_ice")
def handle_ice(data):
    emit("webrtc_ice", {
        "candidate": data["candidate"],
        "from_sid":  request.sid
    }, to=data["to_sid"])

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000,
                 debug=True, allow_unsafe_werkzeug=True)
