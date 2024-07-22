import socket

class ExtremeUSB():
    PORT = 6137
    MAGIC_NUMBER = b'\xA9\xC4\xD8\xF4'

    OPCODE_REQ_INFO = b'\x00'
    OPCODE_REP_INFO = b'\x01'
    OPCODE_PING = b'\x02'
    OPCODE_ACK = b'\x03'
    OPCODE_PAIR = b'\x04'
    OPCODE_REMOVE_PAIRING = b'\x05'
    OPCODE_REQ_TOPO = b'\x06'
    OPCODE_REP_TOPO = b'\x07'
    OPCODE_REP_UNHANDLED_CMD = b'\x08'
    OPCODE_NACK = b'\x09'
    OPCODE_REMOVE_PAIRING_ALL = b'\x0a'

    LOCAL = b'\x00'
    REMOTE = b'\x01'

    def __init__(self, debug=False):
        self.debug = debug

        self._transId = 0
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.settimeout(0.5)
        self._sock.bind(("", self.PORT))

    def _sendCmd(self, data):
        #check if we are sending to broadcast and change receive behavior later
        # bcast = False
        # if (data[1:8] == b'\xff\xff\xff\xff\xff\xff'):
        #     print("Sending to bcast")
        #     bcast = True
        transIdBytes = self._transId.to_bytes(4, "big")
        opcode = data[0]
        msg = self.MAGIC_NUMBER + transIdBytes + data
        try:
            self._sock.sendto(msg, ('<broadcast>', self.PORT))

            recv = []
            recvCount = 0
            try:
                while True:
                    data, addr = self._sock.recvfrom(1024)
                    #extreme usb devices do not technically have an IP, as they operate on layer 2, and "send" from 0.0.0.0
                    #broadcast listener will catch our own command, so we need to filter it out
                    ip, port = addr
                    if (ip == "0.0.0.0"):
                        recv.append(data)
                        recvCount += 1
            except TimeoutError:
                #in the try loop we keep trying for new data until it doesn't come anymore
                #so despite a timeout error being inevitable, we need to keep track of how many replies we've gotten,
                #and only error out if we got 0
                if (recvCount > 0):
                    pass
                else:
                    raise TimeoutError()
            except Exception as e:
                raise e
            
            retVal = []
            for reply in recv:
                # verify incoming packet has magic number (it came from a USB extender and not some other device)
                if (reply[0:4] == self.MAGIC_NUMBER):
                    # verify the transaction IDs match
                    incomingTransId = reply[4:8]
                    if (incomingTransId != transIdBytes):
                        raise Exception("Incoming transaction ID does not match outgoing! Something suspicious is going on.")
                    
                    # handle NACKs and unhandled commands
                    incomingOpcode = reply[8]

                    if (incomingOpcode == self.OPCODE_NACK):
                        raise Exception("Device replied with NACK.")

                    if (incomingOpcode == self.OPCODE_REP_UNHANDLED_CMD):
                        raise Exception("Device replied with unhandled command.")
                    
                    incomingMac = reply[9:15]
                    incomingMac = self._unParseMac(incomingMac)

                    data = reply[15:]
                    
                    reply = {incomingMac: data}
                    retVal.append(reply)
            
            return retVal
        except Exception as e:
            raise e
        finally:
            self._transId += 1

    def _parseMac(self, inMac):
        outMac = b''
        inMac = inMac.split(':')
        for b in inMac:
            outMac += int(b, 16).to_bytes(1, "big")
        return outMac
    
    def _unParseMac(self, inBytes):
        intArr = [f'{x:02x}' for x in inBytes]
        outStr = ":".join(intArr)
        return outStr

    def getInfo(self, mac):
        parsedMac = self._parseMac(mac)
        msg = self.OPCODE_REQ_INFO + parsedMac
        resp = self._sendCmd(msg)
        
        retVal = []
        #iterate over devices that replied
        for dev in resp:
            for mac in dev:
                devReply = dev[mac]
                side = 'local' if devReply[76] == 0 else 'remote'
                data = {'mac': mac, 'side': side, 'paired': False}

                #check if it's paired, possible for one side to think it's paired but the other side disagrees, causing them to not be paired
                pairedMac = ""
                if (len(devReply) > 78):
                    isPaired = True
                    remoteMac = devReply[78:84]
                    remoteMac = self._unParseMac(remoteMac)
                    data["paired"] = True
                    data["remoteMac"] = remoteMac
                
                retVal.append(data)

        return retVal

    def pair(self, localMac, dstMac):
        parsedLocalMac = self._parseMac(localMac)
        parsedDstMac = self._parseMac(dstMac)
        msg = self.OPCODE_PAIR + parsedLocalMac + parsedDstMac
        resp = self._sendCmd(msg)
        msg = self.OPCODE_PAIR + parsedDstMac + parsedLocalMac
        resp = self._sendCmd(msg)

    def unpair(self, localMac, dstMac):
        parsedLocalMac = self._parseMac(localMac)
        parsedDstMac = self._parseMac(dstMac)
        msg = self.OPCODE_REMOVE_PAIRING + parsedLocalMac + parsedDstMac
        resp = self._sendCmd(msg)
        msg = self.OPCODE_REMOVE_PAIRING + parsedDstMac + parsedLocalMac
        resp = self._sendCmd(msg)

    def unpairAll(self, mac):
        parsedMac = self._parseMac(mac)
        msg = self.OPCODE_REMOVE_PAIRING_ALL + parsedMac
        resp = self._sendCmd(msg)
    
    def ping(self, mac):
        parsedMac = self._parseMac(mac)
        msg = self.OPCODE_PING + parsedMac
        resp = self._sendCmd(msg)

