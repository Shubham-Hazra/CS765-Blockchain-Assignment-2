# Class for block
class Block:
    def __init__(self,creator_id, previous_block_id,created_at, transactions,n,balances,block_id = -1,length = 0):
        self.block_id = f"Block_{block_id}" # Set the block ID to the global block ID (Unique ID for each block)(Block ID is set to 0 if the block is the genesis block)
        self.creator_id = creator_id # Set the ID of the creator of the block
        self.previous_id = previous_block_id # Set the ID of the previous block
        self.created_at = created_at # Set the time of creation of the block
        self.transactions = transactions # List of all the TXNs
        self.length = length # Length of the block initially set to 0 (Length is updated when the block is added to the blockchain of a particular peer)
        self.received = [0]*n # Array to store which peer has received the block
        self.balances = balances # Stores teh balances of all the node at the time the block was created

    # VERIFIED
    def get_size(self): # Function to get the size of the block in Mbs
        return (1 + len(self.transactions)) * 0.008 # Assuming that each transaction is 1KB and the coinbase is 1KB            

    # VERIFIED
    # Function for printing block information
    def print_block(self):
        print("===========================================================================")
        print("Block id: ", self.block_id)
        print("Block creator id: ", self.creator_id)
        print("Block previous: ", self.previous_id)
        print("Block transactions: ", self.transactions)
        print("Block balances:",self.balances)
        print("===========================================================================")

# Testing
if __name__ == '__main__':
    b1 = Block(0, 1, 1,[100,100],["Txn_1", "Txn_2"],2)
    b1.print_block()
    b2 = Block(1, 2, 2, [100,100],["Txn_3", "Txn_4"],2)
    b2.print_block()
