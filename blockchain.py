import sys
import datetime
import socket
import threading
import signal
import hashlib
from time import sleep
import pickle
import ast
import traceback

class Block:
    '''
    Block
    -------------
    Parameters:
    index : int of index
    prevhash : string of previous hash
    data : string of data to be stored in the block
    timestamp : timestamp of blockcreation
    '''
    def __init__(self, index, prevhash, data, timestamp):
        self.index = index
        self.prevhash = prevhash
        self.data = data
        self.timestamp = timestamp
        self.hash = self.getHash()

    def getIndex(self):
        '''
        Returns Index of Block
        '''
        return self.index
    
    def getPrevHash(self):
        '''
        Returns Previous Hash of Block
        '''
        return self.prevhash

    def getData(self):
        '''
        Returns Data of Block
        '''
        return self.data

    def getTime(self):
        '''
        Returns Timestamp
        '''
        return self.timestamp

    def getHash(self):
        '''
        Calculates Hash of Block
        '''
        hashinfo = (str(self.prevhash) + str(self.data) + str(self.timestamp))
        innerhash = hashlib.sha256(hashinfo.encode()).hexdigest().encode()
        outerhash = hashlib.sha256(innerhash).hexdigest()
        return outerhash

class Runner:
    def __init__(self):
        '''
        Runs the P2P Client
        '''
        self.peers = []
        self.blockchain = []
        self.startup() # run startup function
        self.udplisten = threading.Thread(target=self.listener, args=("udp",), daemon=True)
        self.udplisten.start() # run udp listener in thread
        self.tcplisten = threading.Thread(target=self.listener, args=("tcp",), daemon=True)
        self.tcplisten.start() # run tcp listener in thread
        self.keepalivet = threading.Thread(target=self.keepalive, daemon=True)
        self.keepalivet.start() # run keepalive thread
        print("All processes running.")
        
        kb = threading.Thread(target=self.keyboard)
        kb.start() # run commandline interface thread

    def createsocket(self, socktype):
        '''
        Function to create a TCP or UDP socket
        -------------
        Parameters:
        socktype : "tcp" or "udp"
        '''
        if socktype == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif socktype == "udp":    
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # allow broadcast
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allow reuse of address
        return sock

    # a hacky way to get the interface ip (depends on the number of interfaces on your pc)
    # only localhost
    # no firewalls
    # no weird stuffs
    # best is VMs
    def getif(self):
        '''
        Gets the interface to bind to the sockets
        -------------   1
        It's a hacky way to get the interface IP (Depends on the # of interfaces on computer)
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        return ip

    def startup(self):
        '''
        Starts up the client
        -------------
        Sends a UDP broadcast to the network to check if there are peers on the network
        Waits 5 seconds to receive a response from peers
        If there are peers, retrieve blockchain and add peers that responded to the peers list
        '''
        print("Starting Up Blockchain Client...")
        sock = self.createsocket("udp")        
        sock.settimeout(5)
        sock.bind((self.getif(), 0))
        sock.sendto(str.encode("teamblock"), ("255.255.255.255", 8080)) # send 'teamblock' (keyword to not have false positives) to the broadcast address
        try:
            data, addr = sock.recvfrom(64)
            data = data.decode("utf-8") 
            if data[0:9] == "teamblock":
                peerslst = ast.literal_eval(data[9:])
                self.peers = peerslst
                self.peers.append(addr[0]) # add peer to the list
                sock.close()    
                
        except socket.timeout: # wait for timeout
            print("No peers online.")
            print("Creating Genesis Block...") # create genesis block since this is the only peer on the network
            sock.close()
            data = {
                "index": 0,
                "prevhash": None,
                "data": "This is the genesis block",
                "timestamp": datetime.datetime.now(),
            }
            self.create(data)
            return True

    def create(self, data):
        '''
        Creates Block and appends to blockchain list
        -------------
        Parameters:
        data : dict of data for the creation of Block
        '''
        block = Block(data["index"], data["prevhash"], data["data"], data["timestamp"])
        self.blockchain.append(block)
        print("Block Created!")

    def listener(self, socktype):
        '''
        Runs a listener for either tcp or udp packets
        -------------
        Parameters:
        socktype : "tcp" or "udp"
        '''
        if socktype == "udp":
            while True:
                ssock = self.createsocket("udp")
                ssock.bind(("0.0.0.0", 8080))
                data, addr = ssock.recvfrom(64) # receives udp packets
                data = data.decode("utf-8")
                if data == "teamblock": # checks if any client has broadcasted the startup packet
                    print("\nPeer Connected! IP Address:" + str(addr))
                    ssock.sendto(str.encode("teamblock" + str(self.peers)), addr) # reply to the client
                    if addr[0] not in self.peers:
                        self.peers.append(addr[0]) # appends the ip address of the new client to the peers list
                    sleep(4)
                    self.sync([addr[0]]) # send a sync request to the new peer
                elif data == "stillalive?": # check if the data received is a keepalive packet
                    ssock.sendto(str.encode("amalive"), addr) # reply to keepalive packet
                elif data == "amleaving": # checks if the data is an exit packet
                    print("\n" + str(addr[0]) + " has left the chat.")
                    if addr[0] in self.peers:
                        self.peers.remove(addr[0]) # remove peer from list
                
                ssock.close()

        elif socktype == "tcp":
            tsock = self.createsocket("tcp")
            tsock.bind((self.getif(), 8080))
            tsock.listen()
            while True:
                try:
                    conn, addr = tsock.accept()
                    fullmsg = b'' # expect bytes
                    newmsg = True # getting new message
                    while True:
                        data = conn.recv(1024) # recv buffer of 1024
                        if newmsg:
                            message = data[:10].decode("utf-8").strip()
                            print(message)
                            msglen = int(message)
                            newmsg = False
                            print("\nMessage Length: " + str((msglen)))

                        fullmsg += data
                        
                        if len(fullmsg)-10 == msglen: # check if full data received
                            print("\nSync Received from " + str(addr[0]))
                            if addr[0] not in self.peers:
                                self.peers.append(addr[0])
                            data = pickle.loads(fullmsg[10:]) # decode the pickle data
                            self.blockchain = data
                            newmsg = True
                            fullmsg = b''

                except Exception as e:
                    print(traceback.format_exc())
                    print("\nError: " + str(e))

    def sync(self, peerslist):
        '''
        Sends synchronise request
        -------------
        Parameters:
        peerslist : list of peers IP
        '''
        if len(peerslist) != 0:
            for ip in peerslist: # loop through each peer in the peers list
                try:
                    sysock = self.createsocket("tcp")
                    addr = (str(ip), 8080)
                    sysock.connect(addr)
                    message = pickle.dumps(self.blockchain) # create pickle object from blockchain
                    message = bytes(f'{len(message):<10}', "utf-8") + message # prepend len of message to the data
                    sysock.sendall(message) 
                except:
                    print("Failed to sync with peer " + str(ip))
                finally:
                    sysock.close()
        else:
            print("No peers to sync with...")

    def keepalive(self):
        '''
        Keep Alive function to check if peers have disconnected
        '''
        while True:
            sleep(30) # runs every 30 seconds
            for ip in self.peers:
                x = 0 
                while x < 3: # 3 attempts before kicking peer
                    try:
                        sock = self.createsocket("udp")
                        sock.settimeout(5)
                        sock.bind((self.getif(), 0))
                        sock.sendto(str.encode("stillalive?"), (ip, 8080)) # sends stillalive? as data
                        data, _ = sock.recvfrom(64)
                        data = data.decode("utf-8") 
                        if data == "amalive":
                            x = 3
                            sock.close()
                    except socket.timeout:
                        if x == 2: # if the peer has not replied thrice
                            print("\n" + str(ip) + " hasn't been responding for awhile...")
                            print("\nRemoving from active peers.")
                            self.peers.remove(ip)
                        
                        x = x + 1
                        sock.close()
                    except Exception as e:
                        print("Error: " + str(e))
        
    def keyboard(self):
        '''
        Creates Command Line Interface
        '''
        while True:
            command = input("Enter Command > ")
            if command.lower() == "add" or command.lower() == "create":
                index = len(self.blockchain)
                prevhash = self.blockchain[index-1].getHash()
                data = input("Please enter data: ")

                data = {
                    "index": index,
                    "prevhash": prevhash,
                    "data": data,
                    "timestamp": datetime.datetime.now(),
                }

                self.create(data)
                self.sync(self.peers)

            elif command.lower() == "info":
                print("# of Peers: " + str(len(self.peers)))
                print("Peers: " + str(self.peers))
                print("# of Blocks: " + str(len(self.blockchain)))
            elif command.lower() == "blocks" or command.lower() == "list" or command.lower() == "ls":
                print("=========================================")
                print("Block Info:")
                for block in self.blockchain:
                    print("=========================================")
                    print("Index: " + str(block.getIndex()))
                    print("Previous Hash: " + str(block.getPrevHash()))
                    print("Data: " + str(block.getData()))
                    print("Timestamp: " + str(block.getTime()))
                    print("Hash: " + str(block.getHash()))

            elif command.lower() == "sync":
                print("Sending sync request...")
                self.sync(self.peers)

            elif command == "":
                pass

            elif command.lower() == "query":
                index = input("Which block would you like to query? Enter Index [0 - " + str((len(self.blockchain) - 1)) + "] > ")
                index = int(index)
                if index in list(range(0, len(self.blockchain))):
                    print("=========================================")
                    print("Index: " + str(self.blockchain[index].getIndex()))
                    print("Previous Hash: " + str(self.blockchain[index].getPrevHash()))
                    print("Data: " + str(self.blockchain[index].getData()))
                    print("Timestamp: " + str(self.blockchain[index].getTime()))
                    print("Hash: " + str(self.blockchain[index].getHash()))
                    print("=========================================")
                else:
                    print("Index given out of range!")

            elif command.lower() == "exit":
                if len(self.peers) == 0:
                    print("You are the last node on the network. Exiting would destroy the blockchain.")
                    exitinput = input("Are you sure you want to leave? [y/N]")
                    if exitinput.lower() != "y":
                        pass
                    else:
                        sys.exit()
                else:
                    sock = self.createsocket("udp")        
                    sock.settimeout(5)
                    sock.bind((self.getif(), 0))
                    sock.sendto(str.encode("amleaving"), ("255.255.255.255", 8080))

                    sys.exit()

            elif command.lower() == "help":
                print("=========================================")
                print("P2P Blockchain Client")
                print("=========================================")
                print("Commands:")
                print("add/create: add a new block to the chain")
                print("blocks/list/ls: prints all blocks in the chain")
                print("help: prints this help menu")
                print("info: list info of current network and blockchain")
                print("sync: manual sync request of current blockchain list with peers")
                print("query: query a particular block in the chain")
                print("exit: quit application")
            else:
                print("Command Not Recognised. Enter 'help' for help.")
        
def exithandler(signal_received, frame):
    '''
    Handles exit from main thread
    '''
    print('Quitting Program...')
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exithandler)
    run = Runner()