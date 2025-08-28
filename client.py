import socket
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import logging
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

_WIDTH = 800
_HIGEHT = 1000
logging.basicConfig(filename="client_log.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

class QuizClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quiz Time")
        self.timer = False
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((HOST, PORT))
        logging.info(f"Connected to server at {HOST}:{PORT}")
        self.display_ui_window()

    def center_ui_window(self):
        window = self.root
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (_WIDTH // 2)
        y = (window.winfo_screenheight() // 2) - (_HIGEHT // 2)
        window.geometry(f'{_WIDTH}x{_HIGEHT}+{x}+{y}')  # width x height + x_offset + y_offset - to make it in the center of the screen

    def display_ui_window(self):
        self.root_frame = tk.Frame(self.root)
        self.root_frame.pack(pady=80)

        self.image = Image.open("./quiz_photo.png")
        self.image = self.image.resize((384, 192))
        self.photo = ImageTk.PhotoImage(self.image)

        self.image_label = tk.Label(self.root, image=self.photo)
        self.image_label.pack(pady=10)

        self.pin_label = tk.Label(self.root_frame, text="Welcome To Quiz Time !", font=('Verdana', 24, "bold"))
        self.pin_label.pack(pady=10)

        self.pin_label = tk.Label(self.root_frame, text="Joining a room?", font=('Verdana', 16, "bold"))
        self.pin_label.pack(pady=10)

        self.pin_label = tk.Label(self.root_frame, text="Enter room pin:", font=('Verdana', 14))
        self.pin_label.pack(pady=10)

        self.pin_entry = tk.Entry(self.root_frame, font=('Verdana', 14))
        self.pin_entry.pack(pady=10)
        self.pin_entry.bind("<Return>", lambda event: self.room_joining())

        self.join_room_btn = tk.Button(
            self.root_frame,
            text="Join Quiz",
            fg="#2c3e50",
            bd=2,
            padx=10,
            pady=5,
            relief='raised',
            font=('Verdana', 12),
            command=self.room_joining
        )
        self.join_room_btn.pack(pady=10)
        self.error_label = tk.Label(self.root, text="", fg="red")
        self.error_label.pack()
 
        self.pin_label = tk.Label(self.root_frame, text="Else:",  font=('Verdana', 16, 'bold'))
        self.pin_label.pack(pady=10)
        self.create_room_btn = tk.Button(
            self.root_frame,
            text="New Game",
            fg="#2c3e50",
            bd=2,
            padx=10,
            pady=5,
            relief='raised',
            font=('Verdana', 12),
            command=self.create_new_room
            )
        self.create_room_btn.pack(pady=10)

        self.center_ui_window()

    def create_new_room(self):
        threading.Thread(target=self.create_room, daemon=True).start()

    def send_message(self, m):
        logging.info(f"Sending message: {m}")
        self.client.send(m.encode())

    def receive_message(self):
        try:
            message = self.client.recv(MAX_SIZE).decode()
            logging.info(f"Received message: {message}")
            return message
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    def create_room(self):
        self.send_message(f"{CREATE}")
        time.sleep(0.1)
        logging.info("Creating a new room")

        response = self.receive_message()

        if response.startswith(CATEGORIES):
            self.root.after(0, lambda: self.choose_category(response.split("|")[1:]))


    def room_joining(self):
        threading.Thread(target=self.join_room, daemon=True).start()

    def show_error(self, m):
        logging.error(f"Error: {m}")
        self.error_label.config(text=m)

    def join_room(self):
        self.room_pin = self.pin_entry.get()

        if not self.room_pin:
            self.show_error("Room pin is required to join, Please enter a valid room pin.")
            return

        self.send_message(f"{JOIN}|{self.room_pin}")
        res = self.receive_message()

        if res.startswith(f"{ER_JOIN}|"):
            self.show_error(res.split("|")[1])  # show the error message (not vaild pin)
            return

        self.enter_game()

    def choose_category(self, all_categories):
        logging.info(f"Categories: {all_categories}")
        choose_category_frame = tk.Toplevel(self.root)

        choose_category_frame.title("Choose Quiz Category")
        choose_category_frame.geometry("400x500")

        self.center_window(choose_category_frame)

        self.category_label = tk.Label(choose_category_frame, text="Select the quiz category", font=('Verdana', 20, 'bold'))
        self.category_label.pack(pady=30)

        self.quiz_category = tk.StringVar()
        self.quiz_category.set(all_categories[0])   # set the default value as the first category

        for c in all_categories:
            radio = tk.Radiobutton(
                choose_category_frame,
                text=c,
                variable=self.quiz_category,
                value=c,
                font=('Verdana', 16),
                height=2
            )
            radio.pack(anchor="center", padx=50, pady=10)

        submit_btn = tk.Button(
            choose_category_frame,
            text="Confirm",
            fg="#2c3e50",
            bd=2,
            padx=10,
            pady=5,
            relief='raised',
            font=('Verdana', 12),
            command=lambda: self.start_after_choose_category(choose_category_frame)
        )
        submit_btn.pack(pady=10)

    def start_after_choose_category(self, choose_category_frame):
        selected_category = self.quiz_category.get()
        self.send_message(f"{CREATE}|{selected_category}")
        choose_category_frame.destroy()
        logging.info(f"Starting quiz in category: {selected_category}")
        response = self.receive_message()
        if response.startswith(f"{ROOM}|"):
            self.room_pin = response.split("|")[1]

        self.enter_game()

    def enter_game(self):
        self.root.after(0, self.fill_username)
        self.root.after(0, self.start_quiz_game, self.room_pin)

    def fill_username(self):
        self.username_window = tk.Toplevel(self.root)
        self.username_window.title("Enter Username")
        self.username_window.geometry("300x170")
        self.center_window_up(self.username_window)

        self.name_label = tk.Label(self.username_window, text="Enter Username", font=('Verdana', 16, "bold"))
        self.name_label.pack(pady=10)
        self.username_entry = tk.Entry(self.username_window, font=('Verdana', 14))
        self.username_entry.pack(pady=10)

        submit_button = tk.Button(
            self.username_window,
            text="Submit",
            fg="#2c3e50",
            bd=2,
            padx=10,
            pady=5,
            relief='raised',
            font=('Verdana', 12),
            command=self.submit_username
        )
        submit_button.pack(pady=10)

    def submit_username(self):
        self.username = self.username_entry.get()
        if not self.username:
            messagebox.showerror("Error", "Please enter a username.")
            return

        if self.client:
            logging.info(f"Sending username: {self.username}")
            self.send_message(self.username)

        self.username_window.destroy()

    def start_quiz_game(self, pin: str = None):
        logging.info(f"Starting quiz game with pin: {pin}")
        self.root_frame.destroy()
        self.start_quiz_btn()

        self.prompt_label = tk.Label(self.root, text="Click the button to start the quiz, or wait for more participants", font=('Verdana', 14))
        self.prompt_label.pack(pady=10)

        self.quiz_options = []

        for i in range(4):
            btn = tk.Button(self.root, text=f"Option {i+1}", font=('Verdana', 14),
                            command=lambda i=i: self.answer_handler(i))
            self.quiz_options.append(btn)
            btn.pack_forget()

        self.timer_label = tk.Label(self.root, text="", font=('Verdana', 14), bg='lightblue')
        self.timer_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Loading...", anchor="w", bg='lightblue')
        self.status_label.place(x=10, y=self.root.winfo_height() - 350)

        self.players_label = tk.Label(self.root, text="Quiz Scores:", font=('Verdana', 16, 'bold'))
        self.players_label.place(x=10, y=self.root.winfo_height() - 300)

        self.leaderboard = tk.Text(self.root, state='disabled', height=6, wrap='word', bg='lightgray')
        self.leaderboard.place(x=10, y=self.root.winfo_height() - 260)

        self.players_label = tk.Label(self.root, text="Quiz Participants:", font=('Verdana', 16, 'bold'))
        self.players_label.place(x=10, y=self.root.winfo_height() - 130)

        self.participants_label = tk.Text(self.root, state='disabled', height=10, width=30)
        self.participants_label.place(x=10, y=self.root.winfo_height() - 110)

        self.room_pin_label = tk.Label(self.root, text=f"PIN: {pin}", font=('Verdana', 12, 'bold'))
        self.room_pin_label.place(x=10, y=self.root.winfo_height() - 25)

        threading.Thread(target=self.client_handler, daemon=True).start()

    def start_quiz_btn(self):
        self.start_quiz_button = tk.Button(
            self.root,
            text="Start",
            fg="#2c3e50",
            bd=2,
            padx=15,
            pady=10,
            relief='raised',
            font=('Verdana', 16, 'bold'),
            command=self.start_quiz
        )
        self.start_quiz_button.pack(pady=10)

    def start_quiz(self):
        self.send_message(START)
        self.start_quiz_button.pack_forget()

    def close_client(self):
        logging.info("Closing connection.")
        self.send_message(EXIT)
        self.root.destroy()

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (self.root.winfo_x() + self.root.winfo_width() // 2) - (width // 2)
        y = (self.root.winfo_y() + self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def center_window_up(self, window, offset_n=50):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (self.root.winfo_x() + self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + offset_n
        window.geometry(f'{width}x{height}+{x}+{y}')

    def client_handler(self):
        # switch case on the recived message
        while True:
            try:
                m = self.receive_message()
                if m.startswith(QUESTION):                        # getting question case
                    self.root.after(0, self.present_quiz_question, m)
                elif m.startswith(UPDATE):                        # update the players case
                    participant_info = m.split("|")[1:]
                    self.root.after(0, self.players_update, participant_info)
                elif m.startswith(NEW):                           # new player added case
                    joining_participant = m.split("|")[1]
                    self.root.after(0, self.status_label.config, {"text": f"New player -{joining_participant}- joined the game"})
                elif m == ACK:                                    # end of questions case
                    self.timer = False
                elif m.startswith(CORRECT):                       # display the correct answer case
                    valid_choice = m.split("|")[1]
                    self.root.after(0, self.status_label.config, {"text": f"The Correct Answer Is: {valid_choice}"})
                elif m.startswith(SCORES):                        # update scores case
                    self.root.after(0, self.game_board_update, m)
                elif m.startswith(RESULT):                        # getting the final results case
                    res = m.split("|")[1:]
                    res.sort(key=lambda x: int(x.split(": ")[1]), reverse=True)
                    summary_scores = "\n".join(res)
                    messagebox.showinfo("Game Over", f"Game Over\n\n{summary_scores}")
                    self.close_client()
                    break
            except Exception as e:
                print(f"Error: {e}")
                self.root.destroy()
                break

    def present_quiz_question(self, data):
        self.question_start_time = time.time()
        elements = data.split("|")
        quiz_question = elements[1]
        quiz_choices = elements[2:]

        self.root.after(0, lambda: self.prompt_label.config(text=quiz_question))

        for i, option in enumerate(quiz_choices):
            self.root.after(0, lambda i=i, option=option: self.quiz_options[i].config(text=option, width=60))
            self.root.after(0, lambda i=i: self.quiz_options[i].pack(pady=10))

        self.root.after(0, self.timer_handler)

    def game_board_update(self, m):
        # clears and updated scores received from server
        self.leaderboard.config(state='normal')
        self.leaderboard.delete(1.0, tk.END)

        game_board_scores = m.split("|")[1:]

        for score in game_board_scores:
            self.leaderboard.insert(tk.END, score + "\n")
        self.leaderboard.config(state='disabled')

        logging.info(f"Game board updated: {game_board_scores}")

    def players_update(self, participant_info):
        self.participants_label.config(state='normal')
        self.participants_label.delete(1.0, tk.END)
        for participant in participant_info:
            self.participants_label.insert(tk.END, participant + "\n")
        self.participants_label.config(state='disabled')

    def timer_handler(self):
        threading.Thread(target=self.timer_handler_thread, daemon=True).start()

    def timer_handler_thread(self):
        self.start_quiz_button.pack_forget()
        self.timer = True
        self.curr_time = T_TIME
        self.timer_display()

    def timer_display(self):
        if self.curr_time > 0 and self.timer:
            self.root.after(0, lambda: self.timer_label.config(text=f"Timer: {self.curr_time}"))
            self.curr_time -= 1
            self.root.after(1000, self.timer_display)

    def answer_handler(self, idx):
        time_ended = time.time()
        duration = time_ended - self.question_start_time
        self.send_message(f"{ANSWER}|{idx}|{duration}")
        for btn in self.quiz_options:
            btn.pack_forget()
        self.root.after(0, lambda: self.status_label.config(text="Loading ..."))

def main():
    app = QuizClient()
    app.root.mainloop()

if __name__ == "__main__":
    main()
