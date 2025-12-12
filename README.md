## 1. Server and Client Setup
Create project directory and go into it:
```bash
mkdir BankProject
cd BankProject
```

### 1.1 Server Setup
In the first terminal open `server.py` file, paste source code and save it:
```bash
vim server.py
```

Run server:
```bash
python3 server.py
```

### 1.2 Client Setup
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



# informatikos-projektas

class Client:
   def __init__ (self, name, acc_num, acc, start_time):
        self.name = name
        self.acc_num = acc_num
        self.acc = acc #masyvas
        self.start_time = start_time
        self.end_time = None

    def __str__(self):
        return f'{self.name};{self.acc_num};{self.acc}{self.start_time};{self.end_time}'
