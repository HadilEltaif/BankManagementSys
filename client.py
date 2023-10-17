# Imports
import os
import socket
clear = lambda: os.system('cls')

# Allowed actions for the server for each client

# 1-
def consultAccount(client):
  clear()
  print("Enter the account reference to consult the account:", end="")
  ref = input()
  client.sendall(bytes("ConsultAccount,{}".format(ref), 'UTF-8'))

# 2-
def consultTransaction(client):
  clear()
  print("Enter the account reference to consult the transaction:")
  ref = input()
  client.sendall(bytes("ConsultTransaction,{}".format(ref), 'UTF-8'))

# 3-
def consultBill(client):
  clear()
  print("Enter the account reference to consult the bill:")
  ref = input()
  client.sendall(bytes("ConsultBill,{}".format(ref), 'UTF-8'))

# One of the client's actions: transaction, which involves adding and withdrawing money from the account
# while making the necessary updates

def accountTransaction():
  clear()
  print("1- Add money")
  print("2- Withdraw money")
  print("3- Quit")
  rsp = input()
  while(int(rsp) not in [1, 2, 3]):
    print("Your choice is invalid, try again [1, 2, 3]!")
    rsp = input()
  msg = ""
  if int(rsp) == 1:
    print("Enter your reference code")
    ref = input()
    print("Enter the amount to add")
    amount = input()
    msg = "Add,{},{}".format(ref, amount)
    client.sendall(bytes(msg, 'UTF-8'))

  if int(rsp) == 2:
    print("Enter your reference code")
    ref = input()
    print("Enter the amount to withdraw")
    amount = input()
    msg = "Withdraw,{},{}".format(ref, amount)
    client.sendall(bytes(msg, 'UTF-8'))

  if int(rsp) == 3:
    clientAction(client)

# Actions performed for a client

def clientAction(client):
  clear()
  response = 0
  print("1- Consult account balance")
  print("2- Consult transaction history")
  print("3- Consult bill to pay")
  print("4- Establish a transaction")
  print("Action choice:", end="")
  response = input()
  while int(response) not in [1, 2, 3, 4]:
    print("Your choice is invalid, try again [1, 2, 3, 4]!")
    response = input()
  if(int(response) == 1):
    consultAccount(client)
  if(int(response) == 2):
    consultTransaction(client)
  if(int(response) == 3):
    consultBill(client)
  if(int(response) == 4):
    accountTransaction()

# Socket type: SOCK_STREAM for TCP protocol
# Socket type: SOCK_DGRAM for UDP protocol

SERVER = "127.0.0.1"
PORT = 8084
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))
client.sendall(bytes("Hello", 'UTF-8'))
in_data = client.recv(30720)
while True:
  clientAction(client)
  in_data = client.recv(5072)
  if(in_data.decode() != "Hello"):
    clear()
    print("From Server:", in_data.decode())
    input("Press Enter to continue...")

  if(in_data.decode() == "exit"):
    break
client.close()
