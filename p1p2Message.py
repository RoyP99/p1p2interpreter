'''
Created on 27 jul 2025

@author: robje
'''
HDR_0_REQUEST_CNTRL_TO_PERIPH = 0x00
HDR_0_RESPONSE_FROM_PERIPH = 0x40
HDR_1_PERIPH_ADDR_HEAT_PUMP = 0x00
HDR_1_PERIPH_ADDR_EXT_CNTRL_= 0xF0

PACKET_TYPE_BIT = 1
PACKET_TYPE_BYTES = 2
PACKET_TYPE_8BIT_REG = 3
PACKET_TYPE_16BIT_REG = 4
PACKET_TYPE_24BIT_REG = 5
PACKET_TYPE_32BIT_REG = 6

VALUE_TYPE_U16DIV10 = 1
VALUE_TYPE_U8 = 2
VALUE_TYPE_F8_8 = 3
VALUE_TYPE_BIT = 4

class cP1P2MsgBase():
    def __init__(self, mqttClient):
        self.mqttClient = mqttClient
        
    def setRegisterDef(self, registerDef):
        self.registerDef = registerDef
        if 'subreg' not in registerDef:
            registerDef['subregs'] = []

    def getSubReg(self, message):
        s0 = int(message[0:2], 16)
        s1 = int(message[2:4], 16)
        subReg = s1 * 256 + s0
        return subReg
    
    def getValue(self, message, bytelen):
        val = 0
        for i in range(bytelen):
            v0 = int(message[i*2:2+i*2], 16)
            val += v0 * pow(256, i)
        return val
    
    def publish(self, subReg, val):
        id = subReg['id']
        print('found', subReg['description'], val, id)
        if id != -1:
            self.mqttClient.publish(id, val)
    
class cP1P2MsgBit(cP1P2MsgBase):
    def addSubRegister(self, startByte, startBit, description, id, valueType):
        subRegs = self.registerDef['subregs']
        newSubreg = { 'startbyte': startByte, 'startbit': startBit, 'description': description, 'id': id, 'valuetype': valueType }
        subRegs.append(newSubreg)
        
    def handleMsg(self, message):
        #print('handle msg ', message, ' ', self.registerDef)
        subRegs = self.registerDef['subregs']
        for iSubReg in subRegs:
            messageIndex = iSubReg['startbyte'] * 2
            if messageIndex <= len(message) - 2:
                b = int(message[messageIndex: messageIndex+2], 16)
                val = b >> iSubReg['startbit']
                if iSubReg['valuetype'] == VALUE_TYPE_BIT:
                    val = val & 1
                self.publish(iSubReg, val)
            
class cP1P2MsgBytes(cP1P2MsgBase):
    def addSubRegister(self, startByte, description, id, valueType):
        subRegs = self.registerDef['subregs']
        newSubreg = { 'startbyte': startByte, 'description': description, 'id': id, 'valuetype': valueType }
        subRegs.append(newSubreg)
        
    def handleMsg(self, message):
        #print('handle msg ', message, ' ', self.registerDef)
        subRegs = self.registerDef['subregs']
        for iSubReg in subRegs:
            messageIndex = iSubReg['startbyte'] * 2
            if iSubReg['valuetype'] == VALUE_TYPE_F8_8:
                if messageIndex <= len(message) - 4:
                    b = int(message[messageIndex: messageIndex+4], 16)
                    if b & 0x8000:
                        val = (-(0x10000 - b)) / 256
                    else:
                        val = b / 256                    
                self.publish(iSubReg, val)
                
class cP1P2Msg8BitParm(cP1P2MsgBase):
    def addSubRegister(self, subReg, description, id, valueType):
        subRegs = self.registerDef['subregs']
        for iSubReg in subRegs:
            if iSubReg['subreg'] == subReg:
                return  # already registrated
        newSubreg = { 'subreg': subReg, 'description': description, 'id': id, 'valuetype': valueType }
        subRegs.append(newSubreg)
        
    def handleMsg(self, message):
        print('handle msg ', message, ' ', self.registerDef)
        while len(message) >= 6:
            # u16div10
            subReg = self.getSubReg(message)
            message = message[4:]
            subRegs = self.registerDef['subregs']
            for iSubReg in subRegs:
                if iSubReg['subreg'] == subReg:
                    vt = iSubReg['valuetype']
                    if vt == VALUE_TYPE_U8:
                        val = self.getValue(message, 1)
                    print('found ', iSubReg['description'], ' ', val)
                    break
            message = message[1:]

class cP1P2Msg16BitParm(cP1P2MsgBase):
    def addSubRegister(self, subReg, description, id, valueType):
        subRegs = self.registerDef['subregs']
        for iSubReg in subRegs:
            if iSubReg['subreg'] == subReg:
                return  # already registrated
        newSubreg = { 'subreg': subReg, 'description': description, 'id': id, 'valuetype': valueType }
        subRegs.append(newSubreg)
        
    def handleMsg(self, message):
        #print('handle msg ', message, ' ', self.registerDef)
        while len(message) >= 8:
            # u16div10
            subReg = self.getSubReg(message)
            message = message[4:]
            subRegs = self.registerDef['subregs']
            for iSubReg in subRegs:
                if iSubReg['subreg'] == subReg:
                    vt = iSubReg['valuetype']
                    if vt == VALUE_TYPE_U16DIV10:
                        val = self.getValue(message, 2) / 10
                    self.publish(iSubReg, val)
                    break
            message = message[4:]
            

class cP1P2Msg24BitParm(cP1P2MsgBase):
    pass

class cP1P2Msg32BitParm(cP1P2MsgBase):
    pass

class cP1P2Message(object):
    '''
    classdocs
    '''


    def __init__(self, mqttClient):
        '''
        Constructor
        '''
        self.mqttClient = mqttClient
        self.registerDefs = []
     
    def definePacketType(self, packetType, register, direction):
        for registerDef in self.registerDefs:
            if registerDef['register'] == register and registerDef['direction'] == direction:
                return registerDef['parmClass']
        # not found
        parmClass = None
        if packetType == PACKET_TYPE_BIT:
            parmClass = cP1P2MsgBit(self.mqttClient)
        elif packetType == PACKET_TYPE_BYTES:
            parmClass = cP1P2MsgBytes(self.mqttClient)
        elif packetType == PACKET_TYPE_8BIT_REG:
            parmClass = cP1P2Msg8BitParm(self.mqttClient)
        elif packetType == PACKET_TYPE_16BIT_REG:
            parmClass = cP1P2Msg16BitParm(self.mqttClient)
        elif packetType == PACKET_TYPE_24BIT_REG:
            parmClass = cP1P2Msg24BitParm(self.mqttClient)
        elif packetType == PACKET_TYPE_32BIT_REG:
            parmClass = cP1P2Msg32BitParm(self.mqttClient)
        else:
            return None
        e = { 'register': register, 'direction': direction, 'parmClass': parmClass }
        parmClass.setRegisterDef(e)
        self.registerDefs.append(e)
        return parmClass
           
    def handleMessage(self, message):
        #print(message)
        # message starts with 'R '
        headerDirection = int(message[2:4], 16)
        headerAddress = int(message[4:6], 16)
        headerType = int(message[6:8], 16)
        message = message[8:]
        #print(headerDirection, ' ', headerAddress, ' ', headerType, ' ', message)
        # search in registerDefs for registerDef
        for registerDef in self.registerDefs:
            if registerDef['register'] == headerType and registerDef['direction'] == headerDirection:
                # handle message
                registerDef['parmClass'].handleMsg(message)
                return
        
        
    # 40F0300000000000000000000000000000AD