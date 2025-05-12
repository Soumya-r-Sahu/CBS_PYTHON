class SupportChat:
    def __init__(self):
        self.chat_history = []

    def send_message(self, user, message):
        self.chat_history.append({"user": user, "message": message})
        print(f"{user}: {message}")

    def receive_message(self, message):
        self.chat_history.append({"user": "Support", "message": message})
        print(f"Support: {message}")

    def view_chat_history(self):
        for chat in self.chat_history:
            print(f"{chat['user']}: {chat['message']}")