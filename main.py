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
    while nrItems < 100:
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
            tn.write(msg)
            tn.close()
        nrItems += 1
    myMqttClient.stop()
    print('Done')

# {
#     "Battery" : 255,
#     "LevelActions" : "|||||",
#     "LevelNames" : "15|16|17|18|19|20",
#     "LevelOffHidden" : "false",
#     "RSSI" : 12,
#     "SelectorStyle" : "0",
#     "description" : "",
#     "dtype" : "Light/Switch",
#     "hwid" : "12",
#     "id" : "000140E4",
#     "idx" : 148,
#     "name" : "CV Temperatuur",
#     "nvalue" : 2,
#     "stype" : "Selector Switch",
#     "svalue1" : "30",
#     "switchType" : "Selector",
#     "unit" : 1
# }
    
# [
#     {
#         "id": "39dfb777f4bcd0ed",
#         "type": "tab",
#         "label": "Flow Domoticz",
#         "disabled": false,
#         "info": "",
#         "env": []
#     },
#     {
#         "id": "24f055c6319fc45b",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "CV AWT",
#         "topic": "P1P2/P/073/T/1/Temperature_Leaving_Water",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 140,
#         "y": 180,
#         "wires": [
#             [
#                 "7a31bea1bfcb0785"
#             ]
#         ]
#     },
#     {
#         "id": "7a31bea1bfcb0785",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 145;\nmsg.payload = { \"command\": \"udevice\", \n    \"idx\": idx, \n    \"svalue\": msg.payload.toString() \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 180,
#         "wires": [
#             [
#                 "0b36f12705dab610"
#             ]
#         ]
#     },
#     {
#         "id": "0b36f12705dab610",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 180,
#         "wires": []
#     },
#     {
#         "id": "1a022256ee4c0ce1",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "CV RWT",
#         "topic": "P1P2/P/073/T/1/Temperature_Return_Water",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 140,
#         "y": 280,
#         "wires": [
#             [
#                 "a96846af39369e2d"
#             ]
#         ]
#     },
#     {
#         "id": "a96846af39369e2d",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 146;\nmsg.payload = { \"command\": \"udevice\", \n    \"idx\": idx, \n    \"svalue\": msg.payload.toString() \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 280,
#         "wires": [
#             [
#                 "ef85945d55976ae1"
#             ]
#         ]
#     },
#     {
#         "id": "ef85945d55976ae1",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 280,
#         "wires": []
#     },
#     {
#         "id": "07d0961901d7c056",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "CV RoomTemp",
#         "topic": "P1P2/P/073/T/1/Temperature_Room",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 160,
#         "y": 380,
#         "wires": [
#             [
#                 "bceca1d9dae0e8b3"
#             ]
#         ]
#     },
#     {
#         "id": "bceca1d9dae0e8b3",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 147;\nmsg.payload = { \"command\": \"udevice\", \n    \"idx\": idx, \n    \"svalue\": msg.payload.toString() \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 380,
#         "wires": [
#             [
#                 "aa3cd09b254a2a00"
#             ]
#         ]
#     },
#     {
#         "id": "aa3cd09b254a2a00",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 380,
#         "wires": []
#     },
#     {
#         "id": "fea28fe7838e9d52",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "Warmtepomp actief",
#         "topic": "P1P2/P/073/S/1/Compressor_OnOff",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 170,
#         "y": 460,
#         "wires": [
#             [
#                 "2536c904b5fb4008"
#             ]
#         ]
#     },
#     {
#         "id": "2536c904b5fb4008",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 151;\nmsg.payload = {\n    \"command\": \"udevice\", \n    \"idx\": idx, \n    \"nvalue\": msg.payload \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 460,
#         "wires": [
#             [
#                 "c80d8a47ac762ed2"
#             ]
#         ]
#     },
#     {
#         "id": "c80d8a47ac762ed2",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 460,
#         "wires": []
#     },
#     {
#         "id": "d8de7188ae8e0e81",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "Gas ketel actief",
#         "topic": "P1P2/P/073/S/1/GasBoiler_OnOff",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 160,
#         "y": 540,
#         "wires": [
#             [
#                 "fd3c619dcd3a83a6"
#             ]
#         ]
#     },
#     {
#         "id": "fd3c619dcd3a83a6",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 152;\nmsg.payload = {\n    \"command\": \"udevice\", \n    \"idx\": idx, \n    \"nvalue\": msg.payload \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 540,
#         "wires": [
#             [
#                 "f7180a45879451be"
#             ]
#         ]
#     },
#     {
#         "id": "f7180a45879451be",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 540,
#         "wires": []
#     },
#     {
#         "id": "63153aee1b66532b",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "CV streef AWT",
#         "topic": "P1P2/P/073/S/2/Target_Temperature_LWT_Zone_Main",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 160,
#         "y": 600,
#         "wires": [
#             [
#                 "8da3a470e28a1ac4"
#             ]
#         ]
#     },
#     {
#         "id": "8da3a470e28a1ac4",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "AWT to json",
#         "func": "var idx = 153;\nmsg.payload = { \"command\": \"udevice\", \n    \"idx\": idx, \n    \"svalue\": msg.payload.toString() \n    }\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 600,
#         "wires": [
#             [
#                 "29873d54f90533ff"
#             ]
#         ]
#     },
#     {
#         "id": "29873d54f90533ff",
#         "type": "mqtt out",
#         "z": "39dfb777f4bcd0ed",
#         "name": "set domoticz",
#         "topic": "domoticz/in",
#         "qos": "0",
#         "retain": "false",
#         "respTopic": "",
#         "contentType": "",
#         "userProps": "",
#         "correl": "",
#         "expiry": "",
#         "broker": "3830a15019ef3926",
#         "x": 610,
#         "y": 600,
#         "wires": []
#     },
#     {
#         "id": "581b7ff04eb1b959",
#         "type": "mqtt in",
#         "z": "39dfb777f4bcd0ed",
#         "name": "CV temperatuur",
#         "topic": "domoticz/out/148",
#         "qos": "2",
#         "datatype": "auto-detect",
#         "broker": "3830a15019ef3926",
#         "nl": false,
#         "rap": true,
#         "rh": 0,
#         "inputs": 0,
#         "x": 160,
#         "y": 680,
#         "wires": [
#             [
#                 "8cadb7b47449effb"
#             ]
#         ]
#     },
#     {
#         "id": "8cadb7b47449effb",
#         "type": "function",
#         "z": "39dfb777f4bcd0ed",
#         "name": "svalue2p1p2temp",
#         "func": "var v = msg.payload.svalue1;\nvar r = 18;\n//msg.payload = '\\n';\n//node.send(msg);\nswitch (v)\n{\n    case \"0\": r = 15; break;\n    case \"10\": r = 16; break;\n    case \"20\": r = 17; break;\n    case \"30\": r = 18; break;\n    case \"40\": r = 19; break;\n    case \"50\": r = 20; break;\n    default: r = 18;\n}\nr = r * 10;\nvar s = r.toString(16);\nmsg.payload = '\"E36 0 ' + s + '\\r\\n\"';\nreturn msg;",
#         "outputs": 1,
#         "noerr": 0,
#         "initialize": "",
#         "finalize": "",
#         "libs": [],
#         "x": 410,
#         "y": 680,
#         "wires": [
#             [
#                 "36b878a2fdab9f5d"
#             ]
#         ]
#     },
#     {
#         "id": "36b878a2fdab9f5d",
#         "type": "exec",
#         "z": "39dfb777f4bcd0ed",
#         "command": "/home/robert/telnetp1p2.sh",
#         "addpay": "payload",
#         "append": "",
#         "useSpawn": "false",
#         "timer": "",
#         "winHide": false,
#         "oldrc": false,
#         "name": "send with telnet",
#         "x": 680,
#         "y": 680,
#         "wires": [
#             [
#                 "b3a7c5e9f63222ba"
#             ],
#             [],
#             []
#         ]
#     },
#     {
#         "id": "b3a7c5e9f63222ba",
#         "type": "debug",
#         "z": "39dfb777f4bcd0ed",
#         "name": "debug 1",
#         "active": true,
#         "tosidebar": true,
#         "console": false,
#         "tostatus": false,
#         "complete": "false",
#         "statusVal": "",
#         "statusType": "auto",
#         "x": 880,
#         "y": 660,
#         "wires": []
#     },
#     {
#         "id": "3830a15019ef3926",
#         "type": "mqtt-broker",
#         "name": "RPI MQTT",
#         "broker": "192.168.2.98",
#         "port": "1883",
#         "clientid": "",
#         "autoConnect": true,
#         "usetls": false,
#         "protocolVersion": "4",
#         "keepalive": "60",
#         "cleansession": true,
#         "birthTopic": "",
#         "birthQos": "0",
#         "birthPayload": "",
#         "birthMsg": {},
#         "closeTopic": "",
#         "closeQos": "0",
#         "closePayload": "",
#         "closeMsg": {},
#         "willTopic": "",
#         "willQos": "0",
#         "willPayload": "",
#         "willMsg": {},
#         "userProps": "",
#         "sessionExpiry": ""
#     }
# ]    