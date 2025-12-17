#daryti pervedimus į kitus acc
#fiksuoti acc numbers
#fiksuoti loan grazinimo laiko -> blokuoti acc
#prisijungimas prie banko saskaitu po kitu klientu

import socket
import os
import time
from datetime import datetime
import random

# Unix socket file

SOCKET_FILE = "./game.sock"
GAME_STATS_FILE = "./info.dat"

def format_datetime(dt):
    result = f'{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}'
    return result

def write_stats(client):
    f = open(GAME_STATS_FILE, 'a')
    f.write(f'{client}\n')
    f.close()

###############################################################################
def generate_accounts(account_num: int) -> list[dict[str, int]]:
    #“A list where each element is a dictionary, and each dictionary maps strings to integers.”
    
    accounts : list[dict[str, int]] = []
    
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

def confirm_loan(client_socket, account: dict[str, int], loan: float) -> bool:
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
        account["loan"] += loan
        account["balance"] += loan
        return True

    else:
        server_message = f"Operation canceled."
        client_socket.send(server_message.encode('utf-8'))
        return False


def take_out_a_loan(client_socket, account: dict[str, int]) -> bool:
    if account["loan"] > 0: 
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
        return False

def repay_loan(client_socket, account: dict[str, int]) -> bool:
    if account["loan"] <= 0:
        server_message = f"You do not have a loan to repay."
        client_socket.send(server_message.encode('utf-8'))
        return False
        
    server_message = f"""
Your debt is {account["loan"]}
Do you want to repay your loan?
[Y] - Yes
[N] - No
"""
    client_socket.send(server_message.encode('utf-8'))
    response = client_socket.recv(4096).decode('utf-8')

    if response == "Y" or response == "y":
        if account["balance"] < account["loan"]:
            server_message = f"Insufficient funds"
            client_socket.send(server_message.encode('utf-8'))
            return False
        else:
            account["balance"] -= account["loan"]
            account["loan"] = 0
            server_message = f"Your loan succsessfully repaid"
            client_socket.send(server_message.encode('utf-8'))
            return True
    else:
        server_message = f"Operation canceled."
        client_socket.send(server_message.encode('utf-8'))
        return False

###############################################################################

class Client:
    def __init__(self, name: str, acc_num: int, start_time: datetime):
        self.name = name
        self.acc_num = acc_num
        
        self.accounts = generate_accounts(acc_num)
        self.current = 1 
        
        self.start_time = start_time
        self.end_time = None

    def get_current_account(self) -> dict[str, int]:
        return self.accounts[self.current -1]
      
    def __str__(self):
        start = format_datetime(self.start_time) 
        end = format_datetime(self.end_time)
        return f"{self.name};{self.acc_num};{start};{end}"
      
###############################################################################
def simulation(client_socket, client: Client):
    #pasirenka pradini accounta
    while True:
        client_socket.send(
            f"You have {client.acc_num} accounts. Which account You want to access first? Choose (1-{client.acc_num}):\n".encode()
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
            
    #operaciju while        
    while True:
        acc = client.get_current_account()
        menu = (
            "\nChoose action: \n"
            "[1] Withdraw\n"
            "[2] Deposit\n"
            "[3] Take out a loan\n"
            "[4] Repay loan\n"
            "[5] Check balance\n"
            "[6] Switch account\n"
            "[7] Exit\n"
            "Choice: "
        )
        client_socket.send(menu.encode())
        choice = client_socket.recv(4096).decode().strip()
         #exit
        if choice == "7":
            server_message = f"Thank You for choosing our bank! See You next time...\n"
            client_socket.send(server_message.encode('utf-8'))
            client_socket.send(b"END\n")
            break
                
        #withdraw
        elif choice == "1":
            client_socket.send(b"Amount to withdraw: ")
            amt = client_socket.recv(4096).decode().strip()
            if amt.isdigit():
                amount = int(amt)
                if amount <= acc['balance']:
                    acc['balance'] -=amount
                    client_socket.send(f"Withdarw successful. New balance: {acc['balance']}$ \n".encode("utf-8"))
                else:
                    client_socket.send(b"Insufficient funds.Check balance by pressing [4].\n")
            else: 
                client_socket.send(b"Invalid amount.\n")
           
        #deposit
        elif choice == "2":
            server_message = "Enter amount to deposit: "
            client_socket.send(server_message.encode('utf-8'))
            amt = client_socket.recv(4096).decode("utf-8")

            amt = amt.strip()

            if amt.isdigit():
                amount = int(amt)
                acc["balance"] += amount
                client_socket.send(f"Deposit successful. New balance: {acc['balance']}$ \n".encode("utf-8"))
            else:
                client_socket.send(b"Invalid amount.\n")

        #take out a loan
        elif choice == "3":
            take_out_a_loan(client_socket=client_socket, account=acc)
        #repay a loan
        elif choice == "4":
            repay_loan(client_socket=client_socket, account=acc)
            
        #check balance   
        elif choice == "5":
            message = (
                f"Balance $: {acc['balance']}\n"
                f"Loan $: {acc['loan']}\n"
            )
            client_socket.send(message.encode("utf-8"))
            
        #swith account
        elif choice == "6":
                
            client_socket.send(f"Enter account number (1-{client.acc_num}): ".encode("utf-8"))
            response = client_socket.recv(4096).decode("utf-8")
            new_current = int(response.strip())
            
            if (new_current < 1 or new_current > client.acc_num):
                client_socket.send("Account does not exist. Choose an exsiting account.\n".encode("utf-8"))
            elif new_current == client.current:
                    client_socket.send("You are already in this account.\n".encode("utf-8"))
            else:
                client_socket.send("Enter PIN of account: ".encode("utf-8"))
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
        message += (
            f"Account {acc['account']} |"
            f"Account number: {acc['acc_num']} |"
            f"PIN: {acc['pin']} |" 
            f"Balance: {acc['balance']}\n"
        )
    client_socket.send(message.encode())

#####################################################################################
def handle_client(client_socket):
    try:
        start = datetime.now()
        server_message = "Welcome, You have connected to the $$$_Bank simulator_$$$, what is Your name?\n"
        client_socket.send(server_message.encode('utf-8')) #coverts string into bytes
        response = client_socket.recv(4096).decode('utf-8')
        if not response:  # if reading from the socket failed
            raise Exception("failed to receive response")
        name = response.strip()

        server_message = "How many accounts do You want to open? ([1],[2],[3])\n"
        client_socket.send(server_message.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        if not response:  # if reading from the socket failed
            raise Exception("failed to receive response")
        acc_str = response.strip()

        if not acc_str.isdigit():
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

        acc_num = int(acc_str)
        if acc_num not in (1, 2, 3):
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

        client = Client(name, acc_num, datetime.now()) 

        send_account_info(client_socket, client.accounts)
        simulation(client_socket, client)

        client.end_time = datetime.now()
        write_stats(client)
        
    finally:
        client_socket.close()
        print("Client disconnected")

def start_server():
    if os.path.exists(SOCKET_FILE):
        os.remove(SOCKET_FILE)

    if not os.path.exists(GAME_STATS_FILE):
        f = open(GAME_STATS_FILE, 'w')
        f.write('Name; Number of accounts; Test start time; Test end time\n')
        f.close()
        
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
