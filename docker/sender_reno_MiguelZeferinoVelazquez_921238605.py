import socket
import time

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
EXPECTED_SEQ_ID = 0
WINDOW = {}
INITIAL_WINDOW_SIZE = 1
WINDOW_SIZE = INITIAL_WINDOW_SIZE
SLOW_START_THRESHOLD = 64

fileToSend = open("file.mp3", "rb")

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    startThroughPut = time.perf_counter()
    # bind the socket to a OS port
    # bind to 0.0.0.0 to not 5001
    udp_socket.bind(("0.0.0.0", 5003))
    udp_socket.settimeout(1)

    # start sending packets
    sendAll = False
    packetCounter = 0
    bytesCounter = 0
    lastAck = 0
    repeatCounter = 0
    delayTimeStarts = []
    delayTimeSum = 0
    while True:
        try:
            # create packets and send
            index = EXPECTED_SEQ_ID 
            for i in range(WINDOW_SIZE):
                if WINDOW.get(index) == None:
                    payload = fileToSend.read(MESSAGE_SIZE)
                    WINDOW[index] =  int.to_bytes(index, SEQ_ID_SIZE, signed=True, byteorder='big') + payload
                    packetCounter += 1
                    udp_socket.sendto(WINDOW[index],("localhost",5001))
                    delayTimeStarts.append(time.perf_counter())
                    bytesCounter += len(WINDOW[index])
                elif sendAll:
                    udp_socket.sendto(WINDOW[index],("localhost",5001))
                    bytesCounter += len(WINDOW[index])
                if len(WINDOW[index]) == SEQ_ID_SIZE:
                    break
                index += len(WINDOW[index])-SEQ_ID_SIZE

            if sendAll:
                sendAll = False

            # receive acknowledgement
            ack, client = udp_socket.recvfrom(PACKET_SIZE)
            
            # get the message id
            seq_id, message = ack[:SEQ_ID_SIZE], ack[SEQ_ID_SIZE:]
            
            seq_id_int = int.from_bytes(seq_id, signed=True, byteorder='big')

            # check ACK
            if seq_id_int >= EXPECTED_SEQ_ID:
                if message == b'ack':
                    delayTimeEnd = time.perf_counter()
                    numAck = 0
                    for k in WINDOW.keys():
                        if k < seq_id_int:
                            numAck += 1
                    for i in range(numAck):
                        delayTimeSum += delayTimeEnd - delayTimeStarts.pop(0)
                    if seq_id_int == lastAck:
                        repeatCounter +=1
                        # Multiplicative Decrease  & Slow Start Threshold Adjustment
                        if repeatCounter == 3:
                            sendAll = True
                            WINDOW_SIZE //= 2
                            SLOW_START_THRESHOLD = WINDOW_SIZE
                        elif repeatCounter > 3:
                            # Fast Recovery
                            WINDOW_SIZE +=1
                    else:
                        lastAck = seq_id_int
                        repeatCounter = 0
                        # Additive OR Slow Start Increase
                        if WINDOW_SIZE < SLOW_START_THRESHOLD:
                            WINDOW_SIZE *= 2
                        else:
                            WINDOW_SIZE += 1
                if message == b'fin':
                    udp_socket.sendto(seq_id + b'==FINACK==', ("localhost",5001))
                    bytesCounter += len(seq_id + b'==FINACK==')
                    break
                EXPECTED_SEQ_ID = seq_id_int

            oldKeys = []
            for k in WINDOW.keys():
                if k < seq_id_int:
                    oldKeys.append(k)
            for i in oldKeys:
                del WINDOW[i]


        except socket.timeout:
            sendAll = True
            repeatCounter = 0
            # Window Size Reset
            WINDOW_SIZE = INITIAL_WINDOW_SIZE

fileToSend.close()

finThroughPut = time.perf_counter()
packetDelay = delayTimeSum/packetCounter
throughput = bytesCounter/(finThroughPut - startThroughPut)
print("%.7f," % throughput)
print("%.7f," % packetDelay)
print("%.7f" % (0.3*(throughput/1000) + 0.7/packetDelay))