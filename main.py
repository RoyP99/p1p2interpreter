'''
Created on 27 jul 2025

@author: robje
'''
import mqttclient
import p1p2Message
import queue
import time
import json
import telnetlib

MQTT_IP_ADDR = '192.168.2.98'
RECV_TOPIC = 'P1P2/R/073'
SEND_TOPIC = 'domoticz/in'
RECV_TOPIC_REQ_ROOM_TEMP = 'domoticz/out/148'
P1P2_MODULE_IP = '192.168.2.73'

myMasterQueue = queue.Queue(100)
myMainQueue = queue.Queue(100)
myReqRoomTempQueue = queue.Queue(100)

def cbMain(client, userData, message):
    if not myMasterQueue.full():
        #print(message.payload)
        myMainQueue.put(message.payload)
        myMasterQueue.put(1)
    
def cbReqRoomTemp(client, userData, message):
    if not myMasterQueue.full():
        #print(message.payload)
        myReqRoomTempQueue.put(message.payload)
        myMasterQueue.put(2)
    
if __name__ == '__main__':
    #myMainQueue = queue.Queue(100)
    myMqttClient = mqttclient.cMqttClient(MQTT_IP_ADDR, SEND_TOPIC)
    myMqttClient.addReceiveTopic(RECV_TOPIC, cbMain)
    myMqttClient.addReceiveTopic(RECV_TOPIC_REQ_ROOM_TEMP, cbReqRoomTemp)

    myP1P2Messages = p1p2Message.cP1P2Message(myMqttClient)

    #reg0x35Req = myP1P2Messages.definePacketType(p1p2Message.PACKET_TYPE_8BIT_REG, 0x35, p1p2Message.HDR_0_REQUEST_CNTRL_TO_PERIPH)

    reg0x10Resp = myP1P2Messages.definePacketType(p1p2Message.PACKET_TYPE_BIT, 0x10, p1p2Message.HDR_0_RESPONSE_FROM_PERIPH)
    reg0x10Resp.addSubRegister(18, 0, 'Warmtepomp', 151, p1p2Message.VALUE_TYPE_BIT)
    reg0x10Resp.addSubRegister(18, 3, 'Circulatiepomp', -1, p1p2Message.VALUE_TYPE_BIT)
    reg0x10Resp.addSubRegister(19, 1, 'Gasketel', 152, p1p2Message.VALUE_TYPE_BIT)
    
    reg0x11Resp = myP1P2Messages.definePacketType(p1p2Message.PACKET_TYPE_BYTES, 0x11, p1p2Message.HDR_0_RESPONSE_FROM_PERIPH)
    reg0x11Resp.addSubRegister(0, 'TempLWT', 145, p1p2Message.VALUE_TYPE_F8_8)     
    reg0x11Resp.addSubRegister(4, 'CV Buiten Temp', 163, p1p2Message.VALUE_TYPE_F8_8)     
    reg0x11Resp.addSubRegister(6, 'TempRWT', 146, p1p2Message.VALUE_TYPE_F8_8)     
    reg0x11Resp.addSubRegister(12, 'RoomTemp', 147, p1p2Message.VALUE_TYPE_F8_8)     

    # reg0x14Resp = myP1P2Messages.definePacketType(p1p2Message.PACKET_TYPE_BYTES, 0x14, p1p2Message.HDR_0_REQUEST_CNTRL_TO_PERIPH)
    # reg0x14Resp.addSubRegister(0, 'TempSetpointLWT', 153, p1p2Message.VALUE_TYPE_F8_8)     
    
    reg0x36Req = myP1P2Messages.definePacketType(p1p2Message.PACKET_TYPE_16BIT_REG, 0x36, p1p2Message.HDR_0_REQUEST_CNTRL_TO_PERIPH) 
    reg0x36Req.addSubRegister(0, 'RoomTargetTemp', -1, p1p2Message.VALUE_TYPE_U16DIV10)    
    reg0x36Req.addSubRegister(0x0a, 'TempSetpointLWT', 153, p1p2Message.VALUE_TYPE_U16DIV10)    
    
    myMqttClient.start()
    
    nrItems = 0
    while True: #nrItems < 100:
        id = myMasterQueue.get()
        if id == 1:
            payload = myMainQueue.get()
            myP1P2Messages.handleMessage(payload)
        if id == 2:
            payload = json.loads(myReqRoomTempQueue.get())
            reqTemp = int(int(payload['svalue1']) / 10 + 15)
            msg = b'E36 0 ' + f'{reqTemp*10:x}'.encode() + b'\r\n'
            print(msg)
            tn = telnetlib.Telnet(P1P2_MODULE_IP, 23)
            time.sleep(0.5)
            tn.write(msg)
            time.sleep(0.5)
            tn.close()
            #print("WRITTEN")
        nrItems += 1
    myMqttClient.stop()
    print('Done')

