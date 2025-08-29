<h1>P1P2 Interpreter Domoticz</h1>

This is a standalone Python program to extract P1P2 messages from MQTT and send a translation back to MQTT to be used in Domoticz<br>
The P1P2 information that is written to the MQTT server comes from the great project from Arnold Niessen, [link](https://github.com/Arnold-n/P1P2MQTT)
The message used are from the topic /P1P2/R/<nr>

The messages written back are using the channelnumbers of Domoticz and are written to the topic /domoticz/in

Work in progress