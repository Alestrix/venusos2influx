#!/usr/bin/env python3

"""A MQTT to InfluxDB Bridge

This script receives MQTT data and saves those to InfluxDB.

"""

import re
from typing import NamedTuple
import configparser

import threading

from time import sleep

import json

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

Config = configparser.ConfigParser()


INFLUXDB_ADDRESS = 'influx'
INFLUXDB_USER = ''
INFLUXDB_PASSWORD = ''
INFLUXDB_DATABASE = 'bat'
INFLUXDB_MEASUREMENT = ''

MQTT_ADDRESS = 'multiplus1'
MQTT_USER = 'dummy'
MQTT_PASSWORD = ''
MQTT_TOPICS = []
MQTT_REGEXS = []
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float

def loadConfig(configFile="bat2influx.ini"):
    Config.read(configFile)

    global INFLUXDB_ADDRESS, INFLUXDB_USER, INFLUXDB_PASSWORD, INFLUXDB_DATABASE, INFLUXDB_MEASUREMENT
    global MQTT_ADDRESS, MQTT_USER, MQTT_PASSWORD, MQTT_TOPICS, MQTT_REGEXS

    INFLUXDB_ADDRESS =  Config.get("Influx", "address")
    INFLUXDB_USER =  Config.get("Influx", "user", fallback=INFLUXDB_USER)
    INFLUXDB_PASSWORD =  Config.get("Influx", "password", fallback=INFLUXDB_PASSWORD)
    INFLUXDB_DATABASE =  Config.get("Influx", "db", fallback=INFLUXDB_DATABASE)
    INFLUXDB_MEASUREMENT = Config.get("Influx", "measurement", fallback=INFLUXDB_MEASUREMENT)

    MQTT_ADDRESS = Config.get("Battery", "address")
    MQTT_PASSWORD = Config.get("Battery", "password")
    serial = Config.get("Battery", "serial")
    MQTT_TOPICS = [f'N/{serial}/vebus/275/Dc/0/+', f'N/{serial}/vebus/275/Soc']
    MQTT_REGEXS = [f'N/{serial}/vebus/275/Dc/0/([^/]+)', f'N/{serial}/vebus/275/([^/]+)$']


def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    for topic in MQTT_TOPICS:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    # print(msg.topic + ' ' + str(msg.payload))
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
    if sensor_data is not None:
        #print(sensor_data)
        _send_sensor_data_to_influxdb(sensor_data)


def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEXS[0], topic)
    if not match:
        match = re.match(MQTT_REGEXS[1], topic)
    if match:
        location = INFLUXDB_MEASUREMENT
        measurement = match.group(1)
        if measurement in ['Temperature', 'MaxChargeCurrent']:
            return None
        value = json.loads(payload)["value"]
        return SensorData(location, measurement, round(float(value), 4))
    return None


def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data.location,
            'fields': {
                sensor_data.measurement: sensor_data.value
            }
        }
    ]
    influxdb_client.write_points(json_body)


def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)

def pub(mqtt_client):
    i = 0
    while True:
        mqtt_client.publish("R/c0619ab44e6d/vebus/275/Dc/0", "")
        i = (i + 1) % 10
        if i == 0:
            mqtt_client.publish("R/c0619ab44e6d/vebus/275/Soc", "")
        sleep(1)

def main():
    _init_influxdb_database()

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)

    x = threading.Thread(target=pub, args=(mqtt_client,))
    x.start()

    mqtt_client.loop_forever()



if __name__ == '__main__':
    print('Loading Config')
    loadConfig()
    print('Starting MQTT to InfluxDB bridge for VenusOS')
    main()
