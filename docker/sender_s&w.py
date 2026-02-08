import socket
import time

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
EXPECTED_SEQ_ID = 0

fileToSend = open("file.mp3", "rb")
delayTimes = []

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    startThroughPut = time.perf_counter()
    # bind the socket to a OS port
    # bind to 0.0.0.0 to not 5001
    udp_socket.bind(("0.0.0.0", 5003))
    udp_socket.settimeout(1)

    # start sending packets
    isFin = False
    sendNext = True
    bytesCounter = 0
    while True:
        timeouts = 0
        try:
            # create payload
            if (sendNext):
                payload = fileToSend.read(MESSAGE_SIZE)
            if (isFin):
                payload = b'==FINACK=='

            packetToSend = int.to_bytes(EXPECTED_SEQ_ID, SEQ_ID_SIZE, signed=True, byteorder='big') + payload
            

            # send the packet
            udp_socket.sendto(packetToSend, ("localhost",5001))
            if (sendNext):
                startDelay = time.perf_counter()
            bytesCounter += len(packetToSend)

            if (isFin):
                break

            # receive acknowledgement
            ack, client = udp_socket.recvfrom(PACKET_SIZE)
            
            # get the message id
            seq_id, message = ack[:SEQ_ID_SIZE], ack[SEQ_ID_SIZE:]
            
            seq_id = int.from_bytes(seq_id, signed=True, byteorder='big')

            # check ACK
            if seq_id >= EXPECTED_SEQ_ID:
                if message == b'ack':
                    finishDelay = time.perf_counter()
                    delayTimes.append((startDelay,finishDelay))
                    sendNext = True
                if message == b'fin':
                    isFin = True
                EXPECTED_SEQ_ID = seq_id
            else:
                sendNext = False

        except socket.timeout:
            timeouts += 1
            sendNext = False

fileToSend.close()

finThroughPut = time.perf_counter()
sumDelays = 0
for i in delayTimes:
   sumDelays += i[1] - i[0]
packetDelay = sumDelays/len(delayTimes)
throughput = bytesCounter/(finThroughPut - startThroughPut)
print("Throughput: " + str(throughput) + " bytes per second")
print("Average Per-Packet Delay: " + str(packetDelay) + " seconds")
print("Performance: " + str(0.3*(throughput/1000) + 0.7/packetDelay))
