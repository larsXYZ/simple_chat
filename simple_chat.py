import socket
import threading
import time
import os
import json

#Loading PID
PG_ID   = int(os.getpid())

#Ports
RX_PORT = 14001
TX_PORT = 14002
HB_PORT = 14003

#Creating sockets
try:
    s_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #  Receive socket
    s_rx.bind(('', RX_PORT))
    s_rx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Transmit socket
    s_tx.bind(('', TX_PORT))
    s_tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s_hb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Heartbeat socket
    s_hb.settimeout(1) #This socket will only block in for 1 second
    s_hb.bind(('', HB_PORT))
    s_hb.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
except:
    print("Error creating sockets")
    time.sleep(5)
    import sys
    sys.exit(1)

#Loading username
username = input("Username: ")

#We launch the receive thread
def rx(s_rx):
    while True:
        data_rx, addr = s_rx.recvfrom(1024)
        msg_rx_dic = json.loads(data_rx.decode('utf-8'))

        if msg_rx_dic['username'] != username: print(msg_rx_dic['username'], "->", msg_rx_dic['msg'])

rx_thread = threading.Thread(target=rx,args=(s_rx,))
rx_thread.start()

# We launch the heartbeat thread
def hb(s_hb):

    #We keep track of connected users
    connected_users = {}

    while True:

        #Generate heartbeat signal
        hb_sig = { "id" : PG_ID, "time" : int(time.time()), "username" : username}
        s_hb.sendto(bytearray(json.dumps(hb_sig),encoding='utf-8'), ('192.168.1.255', HB_PORT))
        time.sleep(1)

        #Listen for heartbeat
        data = None
        try:
            while True:
                #Receive heartbeat signal
                data, addr = s_hb.recvfrom(1024)
                h_rx_dic = json.loads(data.decode('utf-8'))

                #Update connected users dictionary
                if (h_rx_dic["id"] != PG_ID):

                    if not h_rx_dic["username"] in connected_users:
                        print(h_rx_dic["username"], "has entered the chat!")

                    connected_users[h_rx_dic["username"]] = h_rx_dic["time"]

        except:
            #Checking if any users have timed out
            time_now = int(time.time())
            for user, timestamp in list(connected_users.items()):
                if time_now - timestamp > 10:
                    print(user, "has left the chat..")
                    del connected_users[user]

hb_thread = threading.Thread(target=hb,args=(s_hb,))
hb_thread.start()

#Sending and receiving
while True:
    input()
    msg_tx_dic = { "username" : username , "msg" : input("<- ")}
    s_rx.sendto(bytearray(json.dumps(msg_tx_dic), encoding='utf-8'), ('192.168.1.255', RX_PORT))
