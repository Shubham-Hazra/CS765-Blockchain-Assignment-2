class Transaction:
    def __init__(self,txn_id, sender_id, receiver_id, amount,is_coinbase): # The simulator ensures distinct transaction ids
        self.txn_id = f"Txn_{txn_id}" # Transaction id in string format
        self.sender_id = sender_id # Sender id
        self.receiver_id = receiver_id # Receiver id
        self.amount = amount # Amount of coins
        if not is_coinbase: # If is_coinbase is true, it is a mining transaction
            self.message = f"{self.txn_id}: {self.sender_id} pays {self.receiver_id} {self.amount} coins" # Transaction message for normal transactions
        else:
            self.message = f"{self.txn_id}: {self.sender_id} mines {self.amount} coins" # Transaction message for mining transactions

    # Function for printing transaction information
    def print_transaction(self):
        print(self.message)

    # Function for getting transaction message
    def get_transaction(self):
        return self.message

# Testing
if __name__ == "__main__":
    txn1 = Transaction(0,1, 2, 3, 0)
    txn2 = Transaction(1, 2, 3, 4, 1)
    txn1.print_transaction()
    txn2.print_transaction()
