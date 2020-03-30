import sys
import datetime
import socket
import threading
import signal
import hashlib
from time import sleep
import pickle
from random import randint
import ast

class Block:
    def __init__(self, index, prevhash, data, timestamp):
        self.index = index
        self.prevhash = prevhash
        self.data = data
        self.timestamp = timestamp
        self.hash = self.getHash()

    def getIndex(self):
        return self.index
    
    def getPrevHash(self):
        return self.prevhash

    def getData(self):
        return self.data

    def getTime(self):
        return self.timestamp

    def getHash(self):
        hashinfo = (str(self.prevhash) + str(self.data) + str(self.timestamp))
        innerhash = hashlib.sha256(hashinfo.encode()).hexdigest().encode()
        outerhash = hashlib.sha256(innerhash).hexdigest()
        return outerhash

class Runner:
    def __init__(self):
        self.peers = []
        self.blockchain = []
        self.startup()
        self.udplisten = threading.Thread(target=self.listener, args=("udp",), daemon=True)
        self.udplisten.start()
        self.tcplisten = threading.Thread(target=self.listener, args=("tcp",), daemon=True)
        self.tcplisten.start()
        self.keepalivet = threading.Thread(target=self.keepalive, daemon=True)
        self.keepalivet.start()
        print("All listeners opened")
        
        kb = threading.Thread(target=self.keyboard)
        kb.start()

    def createsocket(self, socktype):
        if socktype == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif socktype == "udp":    
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    # a hacky way to get the interface ip (depends on the number of interfaces on your pc)
    def getint(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        return ip

    def startup(self):
        print("Starting Up Blockchain Client...")
        sock = self.createsocket("udp")        
        sock.settimeout(5)
        sock.bind((self.getint(), 0)) # need to change a
        sock.sendto(str.encode("teamblock"), ("255.255.255.255", 8080))
        try:
            data, addr = sock.recvfrom(64)
            data = data.decode("utf-8") 
            if data[0:9] == "teamblock":
                peerslst = ast.literal_eval(data[9:])
                self.peers = peerslst
                self.peers.append(addr)
                sock.close()    
        except socket.timeout:
            print("No peers online.")
            print("Creating Genesis Block...")
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
        block = Block(data["index"], data["prevhash"], data["data"], data["timestamp"])
        self.blockchain.append(block)
        print("Block Created.")

    def listener(self, socktype):
        if socktype == "udp":
            while True:
                ssock = self.createsocket("udp")
                ssock.bind(("0.0.0.0", 8080))    
                data, addr = ssock.recvfrom(64)
                data = data.decode("utf-8") 
                if data == "teamblock":
                    print("\nPeer Connected! IP Address:" + str(addr))
                    ssock.sendto(str.encode("teamblock" + str(self.peers)), addr)
                    self.peers.append(addr)
                    sleep(4)
                    self.sync([addr])
                elif data == "stillalive?":
                    ssock.sendto(str.encode("amalive"), addr)
                
                ssock.close()

        elif socktype == "tcp":
            while True:
                tsock = self.createsocket("tcp")
                tsock.bind((self.getint(), 8080))
                tsock.listen()
                try:
                    while True:
                        conn, addr = tsock.accept()
                        fullmsg = b''
                        data = conn.recv(1024)
                        if data:
                            # print(f'msglen: {data[:10]}')
                            msglen = int(data[:10])

                            fullmsg += data

                            if len(fullmsg)-10 == msglen:
                                print("Block Received from " + str(addr[0]))
                                data = pickle.loads(fullmsg[10:])
                                print(data)
                                self.blockchain = data
                except Exception as e:
                    print("Error: " + str(e))
                finally:
                    tsock.close()

    def sync(self, peerslist):
        for ip in peerslist:
            try:
                sysock = self.createsocket("tcp")
                addr = (str(ip[0]), 8080)
                sysock.connect(addr)
                message = pickle.dumps(self.blockchain)
                message = bytes(f'{len(message):<10}', "utf-8") + message
                sysock.sendall(message)
            finally:
                sysock.close()

    def keepalive(self):
        while True:
            sleep(30)
            for ip in self.peers:
                try:
                    sock = self.createsocket("udp")
                    sock.settimeout(5)
                    sock.bind((self.getint(), 0))
                    sock.sendto(str.encode("stillalive?"), (ip[0], 8080))
                    data, addr = sock.recvfrom(64)
                    data = data.decode("utf-8") 
                    if data == "amalive":
                        sock.close()
                except socket.timeout:
                    print(str(ip) + " isn't responding...")
                    print("Removing from active peers")
                    self.peers.remove(ip)
                    sock.close()
                except Exception as e:
                    print("Error: " + str(e))
        
    def keyboard(self):
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
            elif command.lower() == "blocks":
                print("Block Info:")
                print(self.blockchain)
                for block in self.blockchain:
                    print("=========================================")
                    print("Index: " + str(block.getIndex()))
                    print("Previous Hash: " + str(block.getPrevHash()))
                    print("Data: " + str(block.getData()))
                    print("Timestamp: " + str(block.getTime()))
                    print("Hash: " + str(block.getHash()))

            elif command.lower() == "sync":
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

            elif command.lower() == "exit":
                sys.exit()
            elif command.lower() == "help":
                print("=========================================")
                print("P2P Blockchain Implementation")
                print("=========================================")
                print("Commands:")
                print("add/create: add a new block to the chain")
                print("blocks: prints all blockchains")
                print("help: prints this help menu")
                print("info: list info of current network and blockchain")
                print("query: query a particular block in the chain")
                print("exit: quit application")
            else:
                print("Command Not Recognised. Enter 'help' for help.")
        
def exithandler(signal_received, frame):
    # Handle any cleanup here
    print('Quitting Program...')
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exithandler)
    run = Runner()