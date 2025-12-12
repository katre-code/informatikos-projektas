from http import server
import socket
import os
import time
from datetime import datetime
import random

# Unix socket file

SOCKET_FILE = "./game.sock"
GAME_STATS_FILE = "./scores.dat"
NUM_QUESTIONS = 2


def format_datetime(dt):
    result = f'{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}'
    return result


###############################################################################
def write_stats(client):
    f = open(GAME_STATS_FILE, 'a')
    f.write(f'{client}\n')
    f.close()


###############################################################################

class BankAccount:
    def __init__(self, name, balance):
        self.name: str = name
        self.balance: float = balance
        self.loan: float = 0

class Client:
    def __init__(self, name):
        self.name: str = name
        self.accounts: list[BankAccount] = []

###############################################################################

def confirm_loan(client_socket, account: BankAccount, loan: float) -> bool:
    server_message = f"""
According to your salary, our bank could offer you {loan} EUR.
Do you want to confirm?
[Y] - Yes
[N] - No
"""
    client_socket.send(server_message.encode('utf-8'))
    response = client_socket.recv(4096).decode('utf-8')

    if response == "Y" or response == "y":
        server_message = f"""
Your balance is succsessfully updated!\n
"""
        client_socket.send(server_message.encode('utf-8'))
        account.loan += loan
        account.balance += loan
        return True

    else:
        server_message = f"Operation canceled."
        client_socket.send(server_message.encode('utf-8'))
        return False


def take_out_a_loan(client_socket, account: BankAccount) -> bool:
    if account.loan > 0: 
        server_message = f"""
You already took out a loan. Please repay your previous loan, 
before taking out a new one.
"""
        client_socket.send(server_message.encode('utf-8'))
        return False

    server_message = f"""
Your salary is:
[1] <= 1500 EUR
[2] > 1500 EUR
"""
    client_socket.send(server_message.encode('utf-8'))
    response = client_socket.recv(4096).decode('utf-8')
    if not response:
        raise Exception("failed to receive response")
    choise = int(response.strip())

    if choise == 1: 
        return confirm_loan(client_socket=client_socket, account=account, loan=500)
    if choise == 2: 
        return confirm_loan(client_socket=client_socket, account=account, loan=1000)
    else:
        server_message = f"Operation canceled."
        client_socket.send(server_message.encode('utf-8'))
        return False;


###############################################################################

def handle_client(client_socket):
    try:
        # Authorization (username, password)
        client: Client = Client(
            name="John Doe"
        )
        # Choose bank account.
        account: BankAccount = BankAccount(
            name="account1",
            balance=550
        )
        client.accounts.append(account)

        while True:
            server_message = f"""
Choose the option:
[1] Take out a loan
[2] Repay loan
Current balance: {account.balance} EUR | Current loan: {account.loan} EUR\n
"""
            client_socket.send(server_message.encode('utf-8'))
            response = client_socket.recv(4096).decode('utf-8')
            if not response:
                raise Exception("failed to receive response")
            choise = int(response.strip())
            # is_valid_response(response)
            match choise:
                case 1:
                    take_out_a_loan(client_socket=client_socket, account=account)
                    print(account.loan)
                case 2:
                    #repay_loan()
                    pass

    except Exception as e:
        print(f"Error while handling client socket: {e}")
    finally:
        print("Client disconnected...")
        client_socket.close()


###############################################################################

def start_server():
    if os.path.exists(SOCKET_FILE):
        os.remove(SOCKET_FILE)

    if not os.path.exists(GAME_STATS_FILE):
        f = open(GAME_STATS_FILE, 'w')
        f.write('Name;level;score;Test start time;Test end time\n')
        f.close()

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_FILE)
    server_socket.listen()

    print(f"Server started:  {SOCKET_FILE}")
    try:
        while True:
            client_socket, _ = server_socket.accept()
            print("New client")
            handle_client(client_socket)
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server_socket.close()
        os.remove(SOCKET_FILE)


if __name__ == "__main__":
    start_server()
