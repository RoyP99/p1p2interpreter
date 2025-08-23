'''
Created on 27 jul 2025

@author: robje
'''
import threading
import paho.mqtt.client
import queue

class cMqttClient(object):
    '''
    classdocs
    '''


    def __init__(self, mqttIp:str, sendTopic:str):
        '''
        Constructor
        '''
        self.running = False
        self.stopRunning = False
        self.mqttIp = mqttIp
        self.sendTopic = sendTopic
        self.recvCbs = []

    def addReceiveTopic(self, recvTopic, cb):
        self.recvCbs.append({ 'topic': recvTopic, 'callback': cb})
        
    def start(self):
        if self.running == False:
            self.myThread = threading.Thread(target = self.handleMqtt)
            self.stopRunning = False
            self.myThread.start()
            self.running = True
    
    def stop(self):
        if self.running:
            self.stopRunning = True
            self.mqttClient.disconnect()
            self.myThread.join(1.0)
            self.running = False
    
    def handleMqtt(self):
        print('mqtt client started')
        self.mqttClient = paho.mqtt.client.Client(client_id='p1p2int')
        self.mqttClient.on_connect = self.onConnect
        print('try to connect ', self.mqttIp)
        self.mqttClient.connect(self.mqttIp, 1883)
        while self.running:
            pass
            self.mqttClient.loop()
        print('mqtt client ended')
        
    def onConnect(self, client, userData, flags, rc):
        #print('connected')
        #self.mqttClient.on_message = self.onMessage
        for recvCb in self.recvCbs:
            self.mqttClient.message_callback_add(recvCb['topic'], recvCb['callback'])
            self.mqttClient.subscribe(recvCb['topic'])

    def publish(self, id, value):
        pass
        