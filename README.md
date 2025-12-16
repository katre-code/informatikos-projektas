# Bank simulation
Team members: Maciulevičiūtė Elena, Roenko Vitaliya, Šukytė Kotryna.

---

## 1. Project problem


The aim of the project is to show a simulation of a bank in which the player, 
acting as a customer, can perform various actions, such as withdrawing money, 
depositing money into an account and obtaining loans. 

---

## 2. Server and Client Setup
Create project directory and go into it:
```bash
mkdir BankProject
cd BankProject
```

### 2.1 Server Setup
In the first terminal open `server.py` file, paste source code and save it:
```bash
vim server.py
```

Run server:
```bash
python3 server.py
```

### 2.2 Client Setup
Open second terminal, go to project directory. Next, open `client.c` file, paste source code and save it:
```bash
vim client.c
gcc client.c
```

Run client:
```bash
./a.out
```

---
## 3. Architecture (client–server interaction)
The system consists of two parts: client and server.
The client sends a request to the server, which processes it and sends a response. 
Communication occurs using the game.sock file and *Unix Domain Socket*.
![Architecture diagram](diagrams/Architecture.png)
 
 ---

## 4. Data structures
Two classes are used:
- Client  ( User's personal account );
   - storing information of the clients name, number of accounts (which can be from 1 to 3), information of all the accounts (listed below, class BankAccount), the current account number (the account that the client can make operations in at the moment), start time and end time of the session.  
- BankAccount ( Banking information: accounts, loans );
   - storing information of each bank account (the account number, randomized six digit number; account PIN, randomized four digit number; balance in the account; loan in the account).
A client may have several bank accounts.

![Class diagram](diagrams/Database.png)

---

## 5. Game logic
Before authorization, the player is anonymous and has only two options:
- Autorization
- Exit

During the authorization the player is asked to put in their name and the number of accounts they want to open. The server generates the account numbers, pins for accounts and randomized starting balance in the accounts. 
After authorization, the player becomes a customer and all other options become available:
1. Withdraw money
2. Deposit money
3. Take out a loan
4. Repay a loan
5. Check balance
6. Switch bank account
7. Exit

Depending on the input number of the client, they are given certain questions, like how much money they want to withdraw, deposit, if they want to switch account: they choose to which account and are asked to put in the pin of the account.

After choosing option 7, the session ends and the data of the client is printed into a data file called "info.dat". In this file we can see the name of the client, the number of accouts they opened, start time and end time of their session.

![Use case diagram](diagrams/UseCaseDiagram.png)

---
