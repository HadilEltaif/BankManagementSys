# Necessary imports
from fileinput import close
from platform import release
import socket, threading
import math

# Mutex to ensure mutual exclusion
bank_mutex = threading.Lock()

# List of allowed actions by the server for the client
allowed_actions = []
allowed_actions.append("ConsultAccount")
allowed_actions.append("ConsultTransaction")
allowed_actions.append("ConsultBill")
allowed_actions.append("Add")
allowed_actions.append("Withdraw")
current_threads = []
msg_size = 1024
bill = "bills.txt"
account = "accounts.txt"
history = "history.txt"

# Managing clients through threads
class threadClients(threading.Thread):

    # Get the client's address and socket
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.csocket = client_socket
        print("New connection added:", client_address)

    # Get the allowed action for the connected client to execute
    def run(self):
        print("Connected to:", client_address)
        self.csocket.send(bytes("hello", 'utf-8'))
        rsp = ''
        while True:
            try:
                data = self.csocket.recv(3072)
            except socket.error as e:
                print("Socket disconnected!")
                break
            rsp = data.decode()
            if rsp != "Hello":
                print("Communication from client requires an action:", rsp.split(",")[0])
                keyword = rsp.split(",")[0]
                if keyword in allowed_actions:
                    ServerNotification(client_address, rsp, self.csocket)
                elif rsp == 'exit':
                    break
                else:
                    msg = "Not recognized as an action!"
                    self.csocket.send(bytes(msg, 'UTF-8'))

        print("Client with address:", client_address, "disconnected...")

# End of the class

# Notify the server each time an action is taken by the client(s) to continue the process done by each client
def ServerNotification(ip, message, csock):
    elements = message.split(",")
    if elements[0] == "ConsultAccount":
        msg = ConsultAccountBalance(elements[1])
        csock.send(bytes(msg, 'UTF-8'))
    if elements[0] == "ConsultTransaction":
        msg = ConsultAccountTransactions(elements[1])
        csock.send(bytes(msg, 'UTF-8'))
    if elements[0] == "ConsultBill":
        msg = ConsultAccountBill(elements[1])
        csock.send(bytes(msg, 'UTF-8'))
    if elements[0] == "Add":
        bank_mutex.acquire()
        if AddAmount(int(elements[1]), int(elements[2])):
            msg = "Added successfully!"
            csock.send(bytes(msg, 'UTF-8'))
        else:
            msg = "Invalid reference, please check!"
            csock.send(bytes(msg, 'UTF-8'))
        bank_mutex.release()
    if elements[0] == "Withdraw":
        bank_mutex.acquire()
        if WithdrawAmount(int(elements[1]), int(elements[2])):
            msg = "Withdrawn successfully!"
            csock.send(bytes(msg, 'UTF-8'))
        else:
            msg = "Withdrawal failed!"
            csock.send(bytes(msg, 'UTF-8'))
        bank_mutex.release()

# Consult the details of a specific account
def ConsultAccountBalance(ref):
    accounts = open(account, 'r')
    account_lines = accounts.readlines()
    for line in account_lines:
        columns = line.split(',')
        if int(columns[0]) == int(ref):
            sign = -1 if columns[2] == "Negative" else 1
            accounts.close()
            msg = "\nYour balance is: {}".format(int(columns[1]) * sign)
            return msg
    return "Account does not exist!"

# Track transactions for a specific reference
def ConsultAccountTransactions(ref):
    response = ""
    history = open(history, 'r')
    history_lines = history.readlines()
    for line in history_lines:
        columns = line.split(',')
        if int(columns[0]) == int(ref):
            response += "Transaction:\nType: {}   Value: {}   Result: {}   Account State After Transaction: {}\n".format(
                columns[1], columns[2], columns[3], columns[4])
    history.close()
    if response == "":
        response = "No transactions made with this reference"
    return response

# Browse the bills file to extract the amount to pay in the case of bank interest
def ConsultAccountBill(ref):
    bills = open(bill, 'r')
    bill_lines = bills.readlines()
    for line in bill_lines:
        columns = line.split(',')
        if int(columns[0]) == int(ref):
            return "The bill to pay is: " + columns[1]
    return "Account does not exist!"

# Check the existence of the account in the accounts file
def CheckAccountExistence(ref):
    accounts = open(account, "r")
    account_lines = accounts.readlines()
    for i in range(len(account_lines)):
        columns = account_lines[i].split(',')
        if int(columns[0]) == ref:
            return True
    return False

# Update bills after adding or withdrawing money
def UpdateBills(ref, value):
    accounts = open(account, "r")
    account_lines = accounts.readlines()
    bill_amount = 0
    for i in range(len(account_lines)):
        columns = account_lines[i].split(',')
        if int(columns[0]) == ref:
            if columns[2] == "Negative":
                bill_amount = value * 0.02
            else:
                amount = int(columns[1])
                if (amount - value) < 0:
                    bill_amount = -(amount - value) * 0.02
                    print("A bill is due")
                    break
    bills = open(bill, "r")
    bill_lines = bills.readlines()
    for i in range(len(bill_lines)):
        columns = bill_lines[i].split(',')
        if columns[0] == "\n":
            break
        if int(columns[0]) == ref:
            print("Bill amount:", bill_amount)
            columns[1] = math.trunc(bill_amount + int(columns[1]))
            if i < len(bill_lines) - 1:
                bill_lines[i] = "{},{}\n".format(columns[0], columns[1])
                bills.close()
            else:
                bill_lines[i] = "{},{}\n".format(columns[0], columns[1])
                bills.close()
            break
    open('bills.txt', 'w').close()
    bills = open(bill, "a")
    for i in bill_lines:
        bills.write(i)

# Withdraw the desired amount from the account and make the necessary updates in the files
# while respecting the debit limit specified for each account
def WithdrawAmount(ref, amount):
    success = False
    is_negative = False
    if amount < 0:
        print("You cannot withdraw a negative amount!")
        return False
    if CheckAccountExistence(ref):
        accounts = open(account, "r")
        account_lines = accounts.readlines()
        for i in range(len(account_lines)):
            columns = account_lines[i].split(',')
            if int(columns[0]) == ref:
                if columns[2] == "Negative":
                    is_negative = True
                    if (int(columns[1]) + amount) <= int(columns[3]):
                        UpdateBills(ref, amount)
                        columns[1] = int(columns[1]) + amount
                        account_lines[i] = "{},{},Negative,{}".format(
                            columns[0], columns[1], columns[3])
                        accounts.close()
                        success = True
                        break
                if columns[2] == "Positive":
                    if (int(columns[1]) - amount) > 0:
                        columns[1] = int(columns[1]) - amount
                        account_lines[i] = "{},{},Positive,{}".format(
                            columns[0], columns[1], columns[3])
                        accounts.close()
                        success = True
                        break
                    elif abs(int(columns[1]) - amount) <= int(columns[3]):
                        UpdateBills(ref, amount)
                        account_lines[i] = "{},{},Negative,{}".format(
                            columns[0], abs(int(columns[1]) - amount), columns[3])
                        accounts.close()
                        success = True
                        is_negative = True
                        break
        open('accounts.txt', 'w').close()
        accounts = open(account, "a")
        for i in account_lines:
            accounts.write(i)
        history = open(history, 'a')
        if success:
            if is_negative:
                history.write("\n{},Withdraw,{},Success,Negative".format(ref, amount))
            else:
                history.write("\n{},Withdraw,{},Success,Positive".format(ref, amount))
        else:
            if is_negative:
                history.write("\n{},Withdraw,{},Failure,Negative".format(ref, amount))
            else:
                history.write("\n{},Withdraw,{},Failure,Positive".format(ref, amount))
        history.close()
        return success
    else:
        return False

# Add the desired amount to the account and make the necessary updates in the files
def AddAmount(ref, amount):
    if CheckAccountExistence(ref):
        fact = open(bill, 'r')
        # Pay the bill in case of bank interest
        bill_lines = fact.readlines()
        fact.close()
        accounts = open(account, 'r')
        account_lines = accounts.readlines()
        accounts.close()
        history = open(history, 'a')
        for i in range(len(bill_lines)):
            columns = bill_lines[i].split(',')
            if int(columns[0]) == ref:
                if int(columns[1]) >= amount:
                    columns[1] = int(columns[1]) - amount
                    amount = 0
                    bill_lines[i] = "{},{}".format(columns[0], columns[1])
                else:
                    amount -= int(columns[1])
                    columns[1] = 0
                    if i != len(bill_lines) - 1:
                        bill_lines[i] = "{},{}\n".format(columns[0], columns[1])
                    else:
                        bill_lines[i] = "{},{}".format(columns[0], columns[1])

                # Update the account after the transaction and bill payment
                for i in range(len(account_lines)):
                    columns = account_lines[i].split(',')
                    if int(columns[0]) == ref:
                        if columns[2] == "Negative":
                            if int(columns[1]) > amount:
                                columns[1] = int(columns[1]) - amount
                                account_lines[i] = "{},{},{},{}".format(columns[0], columns[1], columns[2], columns[3])
                                history.write("\n{},Add,{},Success,Negative".format(columns[0], amount))
                            else:
                                history.write("\n{},Add,{},Success,Positive".format(columns[0], amount))
                                columns[1] = amount - int(columns[1])
                                account_lines[i] = "{},{},{},{}".format(columns[0], columns[1], "Positive", columns[3])
                        else:
                            columns[1] = int(columns[1]) + amount
                            history.write("\n{},Add,{},Success,Positive".format(columns[0], amount))
                            account_lines[i] = "{},{},{},{}".format(columns[0], columns[1], "Positive", columns[3])
        history.close()
        open(account, 'w').close()
        open(bill, 'w').close()
        accounts = open(account, "a")
        bills = open(bill, "a")
        for i in account_lines:
            accounts.write(i)
        for i in bill_lines:
            bills.write(i)
        accounts.close()
        bills.close()
        return True
    else:
        return False

LOCALHOST = "127.0.0.1"
PORT = 8084
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))

print("Server available")
print("Waiting for client requests...")
while True:
    # Main loop
    server.listen(1)
    client_sock, client_address = server.accept()
    # Return the (socket, address) pair
    new_thread = threadClients(client_address, client_sock)
    new_thread.start()
    current_threads.append(new_thread)
