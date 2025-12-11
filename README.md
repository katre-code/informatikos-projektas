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
