# daryti pervedimus i kitus acc +
# fiksuoti acc numbers +
# fiksuoti loan grazinimo laiko -> blokuoti acc
# prisijungimas prie banko saskaitu po kitu klientu +

import socket
import os
import time
from datetime import datetime
import random

# Unix socket file
SOCKET_FILE = "./game.sock"
GAME_STATS_FILE = "./info.dat"
CLIENTS: dict[str, "Client"] = {}
USED_ACC_NUMS = []

# Loan timing rules (seconds)
WARNING_AFTER = 120   # 2 minutes
BLOCK_AFTER = 180     # 3 minutes (2 min + 1 min)

def format_datetime(dt):
    result = f"{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}"
    return result

def write_stats(client):
    f = open(GAME_STATS_FILE, "a")
    f.write(f"Client name: {client.name}\n")

    for acc in client.accounts:
        f.write(
            f"Account {acc['account']} | "
            f"Account number: {acc['acc_num']} | "
            f"PIN: {acc['pin']} | "
            f"Balance: {acc['balance']} | "
            f"Loan: {acc['loan']}\n"
        )
    f.write("\n")
    f.close()

###############################################################################
def generate_accounts(account_num: int) -> list[dict[str, int]]:
    # A list where each element is a dictionary, and each dictionary maps strings to integers
    accounts: list[dict[str, int]] = []

    for i in range(account_num):
        acc_num = random.randint(100000, 999999)
        while acc_num in USED_ACC_NUMS:  # checks uniqueness
            acc_num = random.randint(100000, 999999)
        USED_ACC_NUMS.append(acc_num)

        pin = random.randint(1000, 9999)
        balance = random.randint(500, 2000)
        account = {
            "account": i+1,
            "acc_num": acc_num,
            "pin": pin,
            "balance": balance,
            "loan": 0,

            # loan timer fields
            "loan_start": None,      # time.time() when loan taken
            "loan_warned": False,    # whether warning already sent
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
    client_socket.send(server_message.encode("utf-8"))
    response = client_socket.recv(4096).decode("utf-8")

    if response == "Y" or response == "y":
        server_message = f"""
Your balance is succsessfully updated!\n
"""
        client_socket.send(server_message.encode("utf-8"))
        account["loan"] += loan
        account["balance"] += loan

        # start loan timer
        account["loan_start"] = time.time()
        account["loan_warned"] = False

        return True
    else:
        server_message = "Operation canceled."
        client_socket.send(server_message.encode("utf-8"))
        return False


def take_out_a_loan(client_socket, account: dict[str, int]) -> bool:
    if account["loan"] > 0:
        server_message = """
You already took out a loan. Please repay your previous loan, 
before taking out a new one.
"""
        client_socket.send(server_message.encode("utf-8"))
        return False

    server_message = """
Your salary is:
[1] <= 1500 EUR
[2] > 1500 EUR
"""
    client_socket.send(server_message.encode("utf-8"))
    response = client_socket.recv(4096).decode("utf-8")
    if not response:
        raise Exception("failed to receive response")
    choise = int(response.strip())

    if choise == 1:
        return confirm_loan(client_socket=client_socket, account=account, loan=500)
    if choise == 2:
        return confirm_loan(client_socket=client_socket, account=account, loan=1000)
    else:
        server_message = "Operation canceled."
        client_socket.send(server_message.encode("utf-8"))
        return False


def repay_loan(client_socket, account: dict[str, int]) -> bool:
    if account["loan"] <= 0:
        server_message = "You do not have a loan to repay."
        client_socket.send(server_message.encode("utf-8"))
        return False

    now = time.time()
    elapsed = now - account["loan_start"]
    account["loan"] = int( account["loan"] + 1.002 ** elapsed)

    server_message = f"""
Your debt is {account["loan"]}
Do you want to repay your loan?
[Y] - Yes
[N] - No
"""
    client_socket.send(server_message.encode("utf-8"))
    response = client_socket.recv(4096).decode("utf-8")

    if response == "Y" or response == "y":
        if account["balance"] < account["loan"]:
            server_message = "Insufficient funds"
            client_socket.send(server_message.encode("utf-8"))
            return False
        else:
            account["balance"] -= account["loan"]
            account["loan"] = 0

            # clear loan timer
            account["loan_start"] = None
            account["loan_warned"] = False

            server_message = "Your loan succsessfully repaid"
            client_socket.send(server_message.encode("utf-8"))
            return True
    else:
        server_message = "Operation canceled."
        client_socket.send(server_message.encode("utf-8"))
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

        #  block flag
        self.blocked = False

    def get_current_account(self) -> dict[str, int]:
        return self.accounts[self.current -1]

    def __str__(self):
        start = format_datetime(self.start_time)
        end = format_datetime(self.end_time)
        return f"{self.name};{self.accounts};{self.acc_num};{start};{end}"

###############################################################################

def check_loan_deadlines(client_socket, client: Client):
    """
    If any account has an unpaid loan:
    - after 2 min: send warning once
    - after 3 min: block all accounts (client.blocked = True)
    """
    if client.blocked:
        return

    now = time.time()

    for acc in client.accounts:
        if acc["loan"] > 0 and acc["loan_start"] is not None:
            elapsed = now - acc["loan_start"]

            # warning after 2 minutes (only once)
            if elapsed >= WARNING_AFTER and not acc["loan_warned"]:
                acc["loan_warned"] = True
                client_socket.send(
                    b"\nWARNING: 2 minutes passed and the loan is not repaid.\n"
                    b"In 1 minute your accounts will be BLOCKED if you don't repay!\n\n"
                )

            # block after 3 minutes
            if elapsed >= BLOCK_AFTER:
                client.blocked = True
                client_socket.send(
                    b"\nBLOCKED: Loan was not repaid in time. All your accounts are now blocked.\n"
                    b"Contact bank support to unlock.\n\n"
                )
                return

###############################################################################

def transfer_money(client_socket, client: Client):
    if client.blocked:
        client_socket.send(b"Blocked. Transfers are disabled.\n")
        return

    source_acc = client.get_current_account()

    client_socket.send(
        f"Enter target account number (1-{client.acc_num}): ".encode("utf-8")
    )
    response = client_socket.recv(4096).decode("utf-8").strip()

    if not response.isdigit():
        client_socket.send(b"Invalid account number.\n")
        return

    target_index = int(response)

    if target_index < 1 or target_index > client.acc_num:
        client_socket.send(b"Account does not exist.\n")
        return

    if target_index == client.current:
        client_socket.send(b"Cannot transfer to the same account.\n")
        return

    target_acc = client.accounts[target_index - 1]

    # PIN verification
    client_socket.send(b"Enter PIN of target account: ")
    pin = client_socket.recv(4096).decode("utf-8").strip()

    if not pin.isdigit() or int(pin) != target_acc["pin"]:
        client_socket.send(b"Wrong PIN.\n")
        return

    # Amount
    client_socket.send(b"Enter amount to transfer: ")
    amt = client_socket.recv(4096).decode("utf-8").strip()

    if not amt.isdigit():
        client_socket.send(b"Invalid amount.\n")
        return

    amount = int(amt)

    if amount <= 0:
        client_socket.send(b"Amount must be positive.\n")
        return

    if amount > source_acc["balance"]:
        client_socket.send(b"Insufficient funds.\n")
        return

    # Transfer
    source_acc["balance"] -= amount
    target_acc["balance"] += amount

    client_socket.send(
        f"Transfer successful! {amount}$ transferred to account {target_index}.\n".encode("utf-8")
        )

###############################################################################
def simulation(client_socket, client: Client):
    # choose initial account
    while True:
        check_loan_deadlines(client_socket, client)
        if client.blocked:
            client_socket.send(b"Your accounts are BLOCKED. Access denied.\n")
            client_socket.send(b"END\n")
            client.end_time = datetime.now()
            write_stats(client)
            return

        client_socket.send(
            f"You have {client.acc_num} accounts. Which account You want to access? Choose (1-{client.acc_num}):\n".encode()
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

            # if blocked (just in case)
            if client.blocked:
                client_socket.send(b"Your accounts are BLOCKED. Access denied.\n")
                continue
            break
        else:
            client_socket.send(b"Wrong PIN. Try again.\n")

    #operaciju while        
    while True:
        check_loan_deadlines(client_socket, client)

        if client.blocked:
            client_socket.send(
                b"\nYour accounts are BLOCKED. Only option is [8] Exit.\n"
                b"[8] Exit\nChoice: "
            )
            choice = client_socket.recv(4096).decode().strip()
            if choice == "8":
                client_socket.send(b"Goodbye.\n")
                client_socket.send(b"END\n")
                client.end_time = datetime.now()
                write_stats(client)
                break
            else:
                continue

        acc = client.get_current_account()

        menu = (
            "\nChoose action: \n"
            "[1] Withdraw\n"
            "[2] Deposit\n"
            "[3] Take out a loan\n"
            "[4] Repay loan\n"
            "[5] Check balance\n"
            "[6] Switch account\n"
            "[7] Money transfer\n"
            "[8] Exit\n"
            "Choice: "
        )
        client_socket.send(menu.encode())
        choice = client_socket.recv(4096).decode().strip()

        # exit
        if choice == "8":
            server_message = "Thank You for choosing our bank! See You next time...\n"
            client_socket.send(server_message.encode("utf-8"))
            client_socket.send(b"END\n")
            break

        # withdraw
        elif choice == "1":
            client_socket.send(b"Amount to withdraw: ")
            amt = client_socket.recv(4096).decode().strip()
            if amt.isdigit():
                amount = int(amt)
                if amount <= acc['balance']:
                    acc['balance'] -=amount
                    client_socket.send(f"Withdarw successful. New balance: {acc['balance']}$ \n".encode("utf-8"))
                else:
                    client_socket.send(b"Insufficient funds. Check balance by pressing [5].\n")
            else:
                client_socket.send(b"Invalid amount.\n")

        # deposit
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

        # take out a loan
        elif choice == "3":
            take_out_a_loan(client_socket=client_socket, account=acc)

        # repay a loan
        elif choice == "4":
            repay_loan(client_socket=client_socket, account=acc)

        # check balance
        elif choice == "5":
            message = (
                f"Balance $: {acc['balance']}\n"
                f"Loan $: {acc['loan']}\n"
            )
            client_socket.send(message.encode("utf-8"))

        # switch account
        elif choice == "6":
            check_loan_deadlines(client_socket, client)
            if client.blocked:
                client_socket.send(b"Blocked. Cannot switch accounts.\n")
                continue

            client_socket.send(f"Enter account number (1-{client.acc_num}): ".encode("utf-8"))
            response = client_socket.recv(4096).decode("utf-8").strip()

            if not response.isdigit():
                client_socket.send(b"Invalid input.\n")
                continue

            new_current = int(response)

            if (new_current < 1 or new_current > client.acc_num):
                client_socket.send("Account does not exist. Choose an exsiting account.\n".encode("utf-8"))
            elif new_current == client.current:
                    client_socket.send("You are already in this account.\n".encode("utf-8"))
            else:
                client_socket.send("Enter PIN of account: ".encode("utf-8"))
                response = client_socket.recv(4096).decode("utf-8")
                if not response.isdigit():
                    client_socket.send(b"Invalid PIN.\n")
                    continue
                
                pin = int(response)
                target_acc = client.accounts[new_current - 1]
                if pin != target_acc["pin"]:
                    client_socket.send("Wrong pin. Account not switched.\n".encode("utf-8"))
                    continue

                client.current = new_current
                client_socket.send(f"Switched to account {client.current}\n".encode("utf-8"))

        # money transfer
        elif choice == "7":
            check_loan_deadlines(client_socket, client)
            if client.blocked:
                client_socket.send(b"Blocked. Transfers disabled.\n")
                continue
            transfer_money(client_socket, client)

        else:
            server_message = "Invalid option. Enter 1-8.\n"
            client_socket.send(server_message.encode("utf-8"))

#################################################################################
#sita funkcija tiesiog kliento informacija atsiuncia
def send_account_info(client_socket, accounts):
    message = "Your account information:\n"
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

        if name in CLIENTS:
            client = CLIENTS [name]
            client_socket.send(f"Welcome back, {name}! We have loaded your account infomation.\n".encode("utf-8"))

        else:
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
            CLIENTS[name] = client

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
