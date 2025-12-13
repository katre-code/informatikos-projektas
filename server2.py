import socket
import os
import time
from datetime import datetime
import random

# Unix socket file

SOCKET_FILE = "./game.sock"

def format_datetime(dt):
    result = f'{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}'
    return result

###############################################################################
def generate_accounts(account_num: int, randomize_balance: bool = True) -> List[Dict[str, int]]:

    #“A list where each element is a dictionary, and each dictionary maps strings to integers.”

    if account_num not in (1, 2, 3):
        raise ValueError("account_num must be 1, 2, 3")
    
    accounts : List[Dict[str, int]] = []
    n = account_num
    for i in range (n):
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
        
        self.accounts = generate_accounts (acc_num, randomize_balance = False)
        self.current = 1 #the account that the client is at right now is the first one
        
        self.start_time = start_time
        self.end_time = None

    def _acc(self) -> Dict[str, int]:
        return self.accounts[self.current -1]
      
#šis metodas iš chat gbt ar biški not sure ar jis reikalingas bus išviso
    def swith_accounts(self, account index: int) -> None:
        if not (1 <= account_index <= self.acc_num):
            raise ValueError("Invalid account number")
        self.current = account_index
      
    def __str__(self):
        return f'{self.name};{self.acc_num};{self.accounts};{self.start_time};{self.end_time}'
      
###############################################################################
def simulation(client_socket, accounts):
    while True:
        client_socket.send(
            f"You have {client.acc_num} accounts. Choose (1-{client.acc_num})".encode()
        )
        choice = client_socket.recv(4096).decode().strip() #pasirenka pradini accounta kuriame klientas atliks operacijas

        while True:
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

            acc = client.get_current_account()
            #exit
            if choice == "6":
                client_socket.send(b"END\n")
                break
                
            #withdraw
            if choice == "1":
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

            #check balance   
            elif choice == "4":
                message = (
                    f"Account {acc['account']}\n"
                    f"Balance: {acc['balance']}\n"
                    f"Loan: {acc['loan']}\n"
                )
                client_socket.send(message.encode())
#################################################################################
def handle_client(client_socket):

    try:
        server_message = "Welcome, You have connected to the bank simulator, what is Your name?\n"
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
        account_num = int(response.strip())

        if not acc_num_str.isdigit():
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

        acc_num = int(acc_num_str)
        if acc_num not in (1, 2, 3):
            client_socket.send("Invalid input. Must be 1/2/3.\n".encode("utf-8"))
            return

       client = Client(name, acc_num, datetime.now())  # your class
       client.accounts = generate_accounts(acc_num)
       current = 1

      """
       client_socket.send(f"Hello {client.name}! Active account: {current}\n".encode("utf-8"))

       server_message = ("\n Menu:\n"
                          "Withdraw [1]\n"
                          "Deposit [2]\n"
                          "Loan\n [3]\n"
                          "Check balance [4]\n"
                          "Switch account [5]\n"
                          "Exit [6]\n"
                          "Choose: "
                          )
        client_socket.send(server_message.encode('utf-8'))
        choice = client_socket.recv(4096).decode('utf-8')
        if not response:  # if reading from the socket failed
            raise Exception("failed to receive response")
        choice = int(response.strip())
        
        if not choice_str.isdigit():
            client_socket.send("Invalid option. Enter a number 1-6.\n".encode("utf-8"))
            continue

        choice = int(choice_str)
        acc = client.accounts[current - 1]
##############################################################
        
        if choice == 1:        # Withdraw
           amount = int(input("Enter amount to withdraw: "))
        if accounts[current-1]["balance"] >= amount:
           accounts[current-1]["balance"] -= amount
           print(f"Withdrawal successful. New balance: {accounts[current-1]['balance']}")
        else:
         print("Not enough funds.")

##############################################################

        elif choice == 2:      # Deposit

         server_message = "Enter amount to deposit:\n"
         client_socket.send(server_message.encode('utf-8'))
         response = client_socket.recv(4096).decode('utf-8')
         if not response:  # if reading from the socket failed
             raise Exception("failed to receive response")

         if not amount_str.isdigit():
             client_socket.send("Invalid amount.\n".encode("utf-8"))
             continue

            amount = int(amount_str)
            acc["balance"] += amount
            client_socket.send(f"OK. New balance in the current account: {acc['balance']}\n".encode("utf-8"))

########################################

        elif choice == 3:      # Loan
               //reik prideti dar klausima apie uzdarbi
             amount = int(input("Enter loan amount: "))
             accounts[current-1]["loan"] += amount
             accounts[current-1]["balance"] += amount
             print(f"Loan granted. New balance: {accounts[current-1]['balance']} (loan={accounts[current-1]['loan']})")

         elif choice == 4:      # Check balance
           print(f"Account {current} → Balance: {accounts[current-1]['balance']}  Loan: {accounts[current-1]['loan']}")

########################################

         elif choice == 5:      # Switch account
            new_acc = int(input(f"Enter account number (1-{num_accounts}): "))
         if 1 <= new_acc <= num_accounts:
            current = new_acc
        else:
            print("Invalid account number.")

            server_message = "Enter aaccount number\n"
            client_socket.send(server_message.encode('utf-8'))
            response = client_socket.recv(4096).decode('utf-8')
            if not response:  # if reading from the socket failed
                raise Exception("failed to receive response")

            if not 

########################################
        elif choice == 6:
    print("Exiting simulator...")
    running = False

else:
    print("Invalid option.")


        client.end_time = datetime.now()
        client.score = score
        write_stats(client)
        server_message = f'END: Thank you... You scored {score}\n'
        client_socket.send(server_message.encode('utf-8'))

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
#this runs firts and creates a socket file, the server now waits for a client
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_FILE)#./game.sock
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
"""

