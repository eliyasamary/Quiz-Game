import socket
import threading
import time
import random
import logging
from quiz import data, categories
from consts import (
    HOST,
    PORT,
    MAX_SIZE,
    T_TIME,
    CREATE,
    CATEGORIES,
    EXIT,
    START,
    QUESTION,
    ACK,
    SCORES,
    CORRECT,
    NEW,
    UPDATE,
    RESULT,
    ROOM,
    JOIN,
    ER_JOIN,
    ANSWER,
    ER_ROOM,
    FULL_ROOM,
    STARTED
)

logging.basicConfig(filename="server_log.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
lock = threading.Lock()
all_game_rooms = {}

def send_message(m, c):
    logging.info(f"Sending message: {m}")
    c.send(m.encode())

def receive_message(c):
    try:
        message = c.recv(MAX_SIZE).decode()
        logging.info(f"Received message: {message}")
        return message
    except Exception as e:
        logging.error(f"Error receiving message: {e}")
        return None

def quiz_server(client):
    try:
        while True:
            m = receive_message(client)
            logging.info(f"Received message: {m} from {client}")
            if m == EXIT:
                close_connection(client)
                return
            elif m == CREATE:
                send_categories(client)
            elif m.startswith(f"{CREATE}|"):
                room_pin = generate_unique_room_pin()
                create_room(m, client, room_pin)
                break
            elif m.startswith(f"{JOIN}|"):
                room_pin = m.split("|")[1]
                with lock:
                    if room_pin not in all_game_rooms:
                        send_message(f"{ER_JOIN}|{ER_ROOM}", client)
                    elif len(all_game_rooms[room_pin]["participants"]) >= 4:
                        send_message(f"{ER_JOIN}|{FULL_ROOM}", client)
                    elif all_game_rooms[room_pin]["start_game"]:
                        send_message(f"{ER_JOIN}|{STARTED}", client)
                    else:
                        send_message(f"{ROOM}|{all_game_rooms[room_pin]['PIN']}", client)
                    break

        client_username = receive_message(client)
        logging.info(f"Client username: {client_username} joined room {room_pin}")
        room = all_game_rooms[room_pin]
        room["participants"].append((client_username, client))
        room["scores"][client_username] = 0
        update_participants(room_pin)

        for _, c in room["participants"]:
            if c != client:
                send_message(f"{NEW}|{client_username}", c)

        while True:
            try:
                m = receive_message(client)
                logging.info(f"Received message: {m} from {client_username}")
                if m == START and not room["start_game"]:
                    start_game(room_pin)
                elif room["start_game"] and m.startswith(f"{ANSWER}|"):
                    handel_client_answer(room_pin, client_username, m)
                    send_message(f"{ACK}", client)
                elif m == EXIT:
                    room["participants"] = [(u, s) for u, s in room["participants"] if s != client]
                    del room["scores"][client_username]
                    remove_participant_from_room(room_pin, client, room, client_username)
                    update_participants(room_pin)
                    close_connection(client)
            except Exception as e:
                logging.error(f"Error handling client: {e}")
                remove_participant_from_room(room_pin, client, room, client_username)
                break
    except ConnectionResetError:
            logging.warning(f"Client {client_username} has disconnected unexpectedly.")
            remove_participant_from_room(room_pin, client, room, client_username)
    except Exception as e:
        logging.error(f"Internal Server Error: {e}")
        close_connection(client)

def send_categories(client):
    logging.info("Sending categories to client.")
    send_message(f"{CATEGORIES}|{'|'.join(categories)}", client)

def close_connection(client):
    logging.info(f"Closing connection with {client}.")
    client.close()

def generate_unique_room_pin():
    if len(all_game_rooms) >= 10000:  # If all room PINs are used
        logging.error("Cannot generate more room pins. All possible combinations are in use.")
        return None
    room_pin = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    while room_pin in all_game_rooms:
        room_pin = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    logging.info(f"Generated room pin: {room_pin}")
    return room_pin

def create_room(message, client, room_pin):
    category = message.split("|")[1]
    all_game_rooms[room_pin] = {
        "participants": [],
        "scores": {},
        "start_game": False,
        "PIN": room_pin,
        "category": category
    }
    logging.info(f"Creating room with PIN: {room_pin} and category: {category}")
    send_message(f"{ROOM}|{room_pin}", client)

def start_game(room_pin):
    logging.info(f"Starting game in room: {room_pin}")
    threading.Thread(target=start_game_session, args=(room_pin,), daemon=True).start()

def handel_client_answer(room_pin, client_username, message):
    _, answer, time_answer_took = message.split("|")
    logging.info(f"Handling answer {answer} from {client_username} in room {room_pin}")
    handel_answer(room_pin, client_username, answer, time_answer_took)
    time.sleep(0.1)

def update_participants(room_pin):
    room = all_game_rooms[room_pin]
    participants = "|".join([f"{client[0]}" for client in room["participants"]])
    logging.info(f"Updating participants in room {room_pin}: {participants}")

    for _, client in room["participants"]:
        send_message(f"{UPDATE}|{participants}", client)

def remove_participant_from_room(room_pin, client, room, client_username):
    logging.info(f"Removing {client_username} from room {room_pin}")
    room["participants"] = [(c_username, c_socket) for c_username, c_socket in room["participants"] if c_socket != client]
    del room["scores"][client_username]
    update_participants(room_pin)
    close_connection(client)

def start_game_session(room_pin):
    logging.info(f"Game session started for room {room_pin}")
    room = all_game_rooms[room_pin]
    room["start_game"] = True       # flag to start the game
    all_questions = random.sample(data[room["category"]], 5)

    for q in all_questions:
        question = q["question"]
        question_options = q["options"]
        question_correct_answer = q["correct_answer"]

        announce_question(room_pin, question, question_options)

        room["current_question"] = {"question": question, "correct_answer": question_correct_answer}
        room["answered_participants"] = set()

        start_time = time.time()
        while time.time() - start_time < T_TIME:
            if len(room["answered_participants"]) == len(room["participants"]):
                break
            time.sleep(0.1)

        scores_handler(room_pin, question_options[question_correct_answer])

    room["start_game"] = False
    announce_final_scores(room_pin)

def announce_final_scores(room_pin):
    logging.info(f"Announcing final scores for room {room_pin}")
    room = all_game_rooms[room_pin]
    time.sleep(0.1)
    m = f"{RESULT}|" + "|".join(f"{player[0]}: {room['scores'].get(player[0], 0)}" for player in room["participants"])
    for _, client in room["participants"]:
        send_message(m, client)

def announce_question(room_pin, question, question_options):
    time.sleep(0.1)
    message = f"{QUESTION}|{question}|" + "|".join(question_options)
    logging.info(f"Announcing question: {question} to room {room_pin}")
    for _, client in all_game_rooms[room_pin]["participants"]:
        send_message(message, client)

def scores_handler(room_pin, correct_answer):
    room = all_game_rooms[room_pin]
    scores_message = f"{SCORES}|" + "|".join(
        f"{player[0]}: {room['scores'].get(player[0], 0)}" for player in room["participants"])
    logging.info(f"Sending scores to room {room_pin}")

    for _, client in room["participants"]:
        send_message(scores_message, client)
        time.sleep(0.1)
        send_message(f"{CORRECT}|{correct_answer}", client)

def handel_answer(room_pin, client_username, answer, time_answer_took):
    room = all_game_rooms[room_pin]
    question_ = room["current_question"]
    correct_answer = question_["correct_answer"]
    time_answer_took = int(float(time_answer_took))
    logging.info(f"{client_username} answered in room {room_pin}, time took: {time_answer_took}")
    # points calculation
    if int(answer) == correct_answer:
        base_points = 1000
        points = max(base_points - (time_answer_took * 50), 0)
        room["scores"][client_username] += points

    room["answered_participants"].add(client_username)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listning on port: {PORT}")
    logging.info(f"Server listening on port: {PORT}")

    while True:
        try:
            client, client_address = server.accept()
            logging.info(f"New client connected from {client_address}")
            threading.Thread(target=quiz_server, args=(client,), daemon=True).start()
        except Exception as e:
            logging.error(f"Error accepting client: {e}")

if __name__ == "__main__":
    main()
