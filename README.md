# Quiz Game

A multiplayer quiz game implemented in Python using **socket programming** for networking and **Tkinter** for the graphical user interface.  
It allows players to host or join quiz rooms, answer questions in real time, and compete for the highest score.

---

## 📂 Project Structure

```
quiz-game/
├─ server.py        # Quiz game server: manages rooms, players, questions, scores
├─ client.py        # Client with GUI: allows users to join or host games
├─ consts.py        # Shared constants for consistency
├─ quiz.py          # Quiz questions and categories
├─ doc/
│  ├─ Quiz Game.pdf # Project documentation  
├─ quiz_photo.png   # Image used in the GUI
└─ README.md        
```

---

## 🚀 Features

- Host or join multiplayer quiz rooms using a **room PIN**.  
- Choose from multiple quiz categories.  
- Real-time updates for questions, answers, scores, and participants.  
- Logging on both client and server for debugging and monitoring.  
- GUI built with Tkinter for an easy and interactive experience.

---

## 🔧 Requirements

- Python 3.8+  
- Tkinter (bundled with Python on most systems)  

Install dependencies if required:
```bash
pip install -r requirements.txt
```

> If no `requirements.txt` is provided, Python's standard library (including Tkinter and socket) is sufficient.

---

## ▶️ How to Run

1. **Start the server**  
   ```bash
   python server.py
   ```
   Once running, the server will listen on the specified port and wait for clients.

2. **Run the client(s)**  
   Distribute `client.py` to each player. Run it with:
   ```bash
   python client.py
   ```

3. **Create or join a game**  
   - To **create a new game**, click *New Game*, choose a category, enter your username, and wait for players.  
   - To **join a game**, click *Join Quiz*, enter the provided room PIN and your username.  

4. **Play the game**  
   - When the host starts the quiz, questions will appear with multiple-choice answers.  
   - A timer, participant list, and score board will be shown.  
   - The game lasts five rounds. At the end, a final scoreboard is displayed.

---

## 📖 Logs

- **server_log.log** – records server activity and errors.  
- **client_log.log** – records client actions and errors.  

These logs help monitor activity and debug issues.

---

## 📖 Documentation

- [Project Documentation (PDF)](docs/Quiz_Game.pdf)


## 📌 Credits

Developed as a final project by **Eliya Samary**.  
The project demonstrates skills in **Python networking, multithreading, GUI development, and client-server systems**.
