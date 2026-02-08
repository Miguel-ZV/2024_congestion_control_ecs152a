import socket
import time

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
EXPECTED_SEQ_ID = 0
WINDOW_SIZE = 100
WINDOW = {}

fileToSend = open("file.mp3", "rb")
delayTimeStarts = []
delayTimeEnds = []

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    startThroughPut = time.perf_counter()
    # bind the socket to a OS port
    # bind to 0.0.0.0 to not 5001
    udp_socket.bind(("0.0.0.0", 5003))
    udp_socket.settimeout(1)

    # start sending packets
    bytesCounter = 0
    packetCount = 0
    while True:
        timeouts = 0
        try:
            # create packets
            for i in range(100):
                if WINDOW.get(EXPECTED_SEQ_ID+i) == None:
                    WINDOW[EXPECTED_SEQ_ID+i] = int.to_bytes(EXPECTED_SEQ_ID, SEQ_ID_SIZE, signed=True, byteorder='big') + fileToSend.read(MESSAGE_SIZE)
                    packetCount += 1
            
            # send packets
            for i in range(100):
                udp_socket.sendto(WINDOW[EXPECTED_SEQ_ID+i], ("localhost",5001))
                delayTimeStarts.append(time.perf_counter)
                bytesCounter += len(WINDOW[EXPECTED_SEQ_ID+i])

            # receive acknowledgement
            ack, client = udp_socket.recvfrom(PACKET_SIZE)
            
            # get the message id
            seq_id, message = ack[:SEQ_ID_SIZE], ack[SEQ_ID_SIZE:]
            
            seq_id = int.from_bytes(seq_id, signed=True, byteorder='big')

            # check ACK
            if seq_id >= EXPECTED_SEQ_ID:
                if message == b'ack':
                    finishDelay = time.perf_counter()
                    for i in range(EXPECTED_SEQ_ID, seq_id):
                        delayTimeEnds.append(finishDelay)
                    print("ACK" + str(EXPECTED_SEQ_ID))
                if message == b'fin':
                    udp_socket.sendto(seq_id + b'==FINACK==', ("localhost",5001))
                    break
                EXPECTED_SEQ_ID = seq_id

        except socket.timeout:
            timeouts += 1
            print("Timeout" + str(EXPECTED_SEQ_ID))


fileToSend.close()

finThroughPut = time.perf_counter()
sumDelays = 0

for i in range(packetCount):
   sumDelays += delayTimeEnds[i] - delayTimeEnds[i]

packetDelay = sumDelays/packetCount
throughput = bytesCounter/(finThroughPut - startThroughPut)
print("Throughput: " + str(throughput) + " bytes per second")
print("Average Per-Packet Delay: " + str(packetDelay) + " seconds")
print("Performance: " + str(0.3*(throughput/1000) + 0.7/packetDelay))
