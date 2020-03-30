### 
# Blockchain Structure
#   - Index: 0 - n
#   - Timestamp: epoch (?)
#   - Data: name
#   - Hash: generated
#   - PrevHash: generated

# How do you check for other nodes?


# functions to implement
# - create block (genesis, non-gen)
# - get latest blockchain (sychronise)
# - 

1. check if peers on network
2. if no peers, create genesis block, listen out for peers
3. if peers connect, send latest blockchain to peer (synchronise)
4. if creating new block, get last hash in blockchain, create block, append and sync

https://benediktkr.github.io/dev/2016/02/04/p2p-with-twisted.html

# from block import Block
# import datetime

# num_blocks_to_add = 10

# block_chain = [Block.create_genesis_block()]

# print("The genesis block has been created.")
# print("Hash: %s" % block_chain[0].hash)

# for i in range(1, num_blocks_to_add):
#     block_chain.append(Block(block_chain[i-1].hash,
#                              "Block number %d" % i,
#                              datetime.datetime.now()))
#     print("Block #%d created." % i)
#     print("Hash: %s" % block_chain[-1].hash)