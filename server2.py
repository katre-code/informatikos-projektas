import socket
import os
import time
from datetime import datetime
from typing import List, Dict
import random

# Unix socket file

SOCKET_FILE = "./game.sock"

def format_datetime(dt):
    result = f'{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}'
    return result

###############################################################################
def generate_accounts(account_num: int) -> List[Dict[str, int]]:
    #“A list where each element is a dictionary, and each dictionary maps strings to integers.”
    
    accounts : List[Dict[str, int]] = []
    
    for i in range (account_num):
        acc_num = random.randint(100000, 999999)
        pin = random.randint(1000, 9999)
        balance = random.randint(500, 2000) 
        account = {
                    "account": i+1,
                    "acc_num": acc_num,
                    "pin": pin,
                    "balance": balance,
                    "loan" : 0
            }
        accounts.append(account)
        
    return accounts

###############################################################################

class Client:
    def __init__(self, name: str, acc_num: int, start_time: datetime):
        self.name = name
        self.acc_num = acc_num
        
        self.accounts = generate_accounts(acc_num)
        self.current = 1 #the account that the client is at right now is the first one
        
        self.start_time = start_time
        self.end_time = None

    def get_current_account(self) -> Dict[str, int]:
        return self.accounts[self.current -1]
      
    def __str__(self):
        return f'{self.name};{self.acc_num};{self.start_time};{self.end_time}'
      
###############################################################################
#def simulation(client_socket, client)?
def simulation(client_socket, client: Client):
    while True:
        client_socket.send(
            f"You have {client.acc_num} accounts. Choose (1-{client.acc_num})".encode()
        )
        choice = client_socket.recv(4096).decode().strip() #pasirenka pradini accounta kuriame klientas atliks operacijas

        if not choice.isdigit():
            client_socket.send(b"Invalid input.\n")
            continue

        acc_index = int(choice)
        if not (1 <= acc_index <= client.acc_num):
            client_socket.send(b"Account does not exist.\n")
            continue

       # paklausia pin
        client_socket.send(b"Enter PIN: ")
        pin = client_socket.recv(4096).decode().strip()

        if pin.isdigit() and int(pin) == client.accounts[acc_index - 1]["pin"]:
            client.current = acc_index
            client_socket.send(f"Account {client.current} selected.\n".encode())
            break
        else:
            client_socket.send(b"Wrong PIN. Try again.\n")
            
    while True:
        acc = client.get_current_account()
        menu = (
            "\nChoose action: \n"
            "1. Withdraw\n"
            "2. Deposit\n"
            "3. Loan\n"
            "4. Check balance\n"
            "5. Switch account\n"
            "6. Exit\n"
            "Choice: "
        )
        client_socket.send(menu.encode())
        choice = client_socket.recv(4096).decode().strip()
         #exit
        if choice == "6":
            client_socket.send(b"END\n")
            break
                
        #withdraw
        elif choice == "1":
            client_socket.send(b"Amount to withdraw: ")
            amt = client_socket.recv(4096).decode()
            if amt.isdigit():
                amount = int(amt)
                if amount <= acc['balance']:
                    acc['balance'] -=amount
                    client_socket.send(b"Withdrawal successful.\n")
                else:
                    client_socket.send(b"Insufficient funds.\n")
            else: 
                client_socket.send(b"Invalid amount.\n")
           
        #deposit
        elif choice == "2":
            client_socket.send("Enter amount to deposit:".encode("utf-8"))
            amount = int(client_socket.recv(4096).decode("utf-8"))
            acc["balance"] += amount
            client_socket.send(f"New balance: {acc[current]["balance"]}\n".encode("utf-8"))

        #loan
        elif choice == "3":
            
        #check balance   
        elif choice == "4":
            message = (
                f"Balance: {acc['balance']}\n"
                f"Loan: {acc['loan']}\n"
            )
            client_socket.send(message.encode())
            
        #swith account
        elif choice == "5":
                
            client_socket.send(f"Enter account number (1-{client.acc_num}):\n".encode("utf-8"))
            response = client_socket.recv(4096).decode("utf-8")
            new_current = int(response.strip())
            
            if (new_current < 1 or new_current > client.acc_num):
                client_socket.send("Account does not exist. Choose an exsiting account.\n".encode("utf-8"))
            elif new_current == client.current:
                    client_socket.send("You are already in this account.\n".encode("utf-8"))
            else:
                client_socket.send("Enter PIN of account:\n".encode("utf-8"))
                response = client_socket.recv(4096).decode("utf-8")
                pin = int(response.strip())

                target_acc = client.accounts[new_current - 1]
                if pin != target_acc["pin"]:
                    client_socket.send("Wrong pin. Account not switched.\n".encode("utf-8"))
                    continue

                client.current = new_current
                client_socket.send(f"Switched to account {client.current}\n".encode("utf-8"))
                    
         else:
            server_message = "Ivalid option. Enter 1-6.\n"
            client_socket.send(server_message.encode('utf-8'))
                
#################################################################################
#sita funkcija tiesiog kliento informacija atsiuncia
def send_account_info(client_socket, accounts):
    message = "Your accounts have been created:\n"
    for acc in accounts:
        message = f"Account {acc['account']} | Account number: {acc['acc_num']} | PIN: {acc['pin']} | Balance: {acc['balance']}\n"
    client_socket.send(message.encode())

#####################################################################################
def handle_client(client_socket):
    try:
        start = datetime.now()
        server_message = "Welcome, You have connected to the Bank simulator, what is Your name?\n"
        client_socket.send(server_message.encode('utf-8')) #coverts string into bytes
        response = client_socket.recv(4096).decode('utf-8')
        if not response:  # if reading from the socket failed
            raise Exception("failed to receive response")
        name = response.strip()

        server_message = "How many account do You want to open? ([1],[2],[3])\n"
        client_socket.send(server_message.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        if not response:  # if reading from the socket failed
            raise Exception("failed to receive response")
        acc_str = int(response.strip())

        if not acc_str.isdigit():
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

        acc_num = int(acc_str)
        if acc_num not in (1, 2, 3):
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

       client = Client(name, acc_num, datetime.now()) #creates the client class

       send_account_info(client_socket, client.accounts)
       simulation(client_socket, client)

       client_socket.send(f"Hello {client.name}! Active account: {current}\n".encode("utf-8"))
       client.end_time = datetime.now()

       #gal čia reikia įdėti klausimą dėl pradinio accounto, ir settinti jį kaip current?
        # server_message = f"Which account You want to start with?? (1-)\n"
        #client_socket.send(server_message.encode('utf-8'))
        #response = client_socket.recv(4096).decode('utf-8')

      #klausimas apie pradini accounta yra simuliacijoje tai kai iskvieciame simuliacija issikviecia ir pats klausimas

def start_server():
    if os.path.exists(SOCKET_FILE):
        os.remove(SOCKET_FILE)
        
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_FILE)
    server_socket.listen() 
    print(f"Server started:    {SOCKET_FILE}")

    try:
        while True:
            client_socket, _= server_socket.accept()
            print("New client")
            handle_client(client_socket)
            
    except KeyboardInterrupt:
        print("\nServer shutting down")
        
    finally:
        server_socket.close()
        if os.path.exists(SOCKET_FILE):
            os.remove(SOCKET_FILE)
        print("Server stopped")

if __name__ == "__main__":
    start_server()

