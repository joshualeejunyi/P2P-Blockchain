import datetime
import hashlib

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