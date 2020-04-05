# P2P Blockchain Client
This simple python program discovers and joins a blockchain peer-to-peer network on the current network. If there is no existing blockchain on the network, the program will create the genesis block and start the chain. The node can then create and query information about the blocks in the chain, synchronising with the other peers on the network.

## Requirements
This program uses basic Python 3 libraries. As such, no extra packages are required to be installed.


## Setup
This program only works within the local network (i.e. connection only works between computers on the same network/subnet). This is because we use UDP Broadcast packets to discover other peers on the network.

## Usage
A command line interface is implemented to allow the creation of block, to query information and to synchronise. 
### Command Line
**add/create** : Add a new block to the chain  
**blocks/list/ls** : Prints all blocks in the chain  
**help** : Prints the help menu  
**info** : List information regarding the current network and blockchain  
**sync** : Manual synchronize request of current blockchain list with peers in the network  
**query** : Query information about a particular block in the chain  
**exit** : Exits program  

## Features
All the features work simultaneously through multi-threading, as such, there is no blocking or waiting before being able to type in commands.

### UDP Broadcast
The program uses UDP broadcast packets to discover peers on the network

### TCP Synchronisation
The program uses TCP sockets to synchronize the information on the network

### UDP Keep Alive
In order to maintain the active peers on the network, a UDP keep alive is implemented to check on peers. If they are inactive, they will be removed from the client's list of peers.