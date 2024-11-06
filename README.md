# VenusOS Battery Telemetry to InfluxDB

## Purpose

`bat2influx` reads voltage, amerage, power, and state of charge from a Victron Energy VenusOS
battery inverter/charger and stores the values into an Influx database. From there the user is
free to use them to their liking, like displaying in a Grafana dashboard.

## How it works

`bat2influx` connects to the MQTT broker running on VenusOS and to the InfluxDB provided by the
user in parallel. It then triggers the sending of a telemetry message from VenusOS by publishing
an empty message to `N/<serialnumber>/vebus/275/Dc/0/+` (every second) and to
`N/<serialnumber>/vebus/275/Soc` (every 10 seconds) and stores the received values inside an
InfluxDB database into a measurement (both configurable) under these fields: Current, Power,
Voltage, Soc.

## How it looks

A simple influxQL SELECT statement (I hate flux) looks like this:

```
> select * from dc where time > now()-5s 
name: dc
time                           Current Power Soc  Voltage
----                           ------- ----- ---  -------
2024-11-06T13:54:19.853411972Z         22         
2024-11-06T13:54:19.888644485Z                    52.26
2024-11-06T13:54:19.905109204Z 0                  
2024-11-06T13:54:20.856328777Z         21         
2024-11-06T13:54:20.938091223Z                    52.26
2024-11-06T13:54:20.972238084Z 0                  
2024-11-06T13:54:21.85650829Z          22         
2024-11-06T13:54:21.891096719Z                    52.26
2024-11-06T13:54:21.900385275Z 0                  
2024-11-06T13:54:22.857095492Z         22         
2024-11-06T13:54:22.884699808Z                    52.26
2024-11-06T13:54:22.894218306Z 0                  
2024-11-06T13:54:23.866700336Z         22         
2024-11-06T13:54:23.878145991Z                    52.24
2024-11-06T13:54:23.886577557Z 0                  
2024-11-06T13:54:23.919809621Z               15.5 
```

By grouping these measurements by second the fields can be mapped to the same measurement:
```
> select mean(Current) as Current, mean(Power) as Power, mean(Voltage) as Voltage, mean(Soc) as Soc from dc where time > now()- 5s group by time(1s)
name: dc
time                 Current Power Voltage Soc
----                 ------- ----- ------- ---
2024-11-06T13:56:31Z                       
2024-11-06T13:56:32Z 0       22    52.26   
2024-11-06T13:56:33Z 0       22    52.26   
2024-11-06T13:56:34Z 0       22    52.26   15.5
2024-11-06T13:56:35Z 0       22    52.26   
2024-11-06T13:56:36Z 0       22    52.26   
```

## Configuration

Just copy `bat2influx.template.ini` to `bat2influx.ini` and edit the values to your needs.

## To-Dos

- Testing - nobody except for me has ever run this code, so I have no idea whether some pecurilarities only
specific to my setup might still be hard-coded
- Dockerize
- Make path of config file configurable via command line parameter (maybe not needed once containerized)

## Why?

Why I didn't want to use [venus-influx-loader](https://github.com/victronenergy/venus-influx-loader):

- It doesn't support password authentication towards the battery (i.e. towards the MQTT server)
- It reads a gazillion times more values and stores them into influx than I'm interested in
- It creates one measurement for every value stored, I wanted the values as different fields inside the same measurement

## Mentions

The code is heavily based on [this](https://gist.github.com/zufardhiyaulhaq/fe322f61b3012114379235341b935539)
Gist by [Zufar Dhiyaulhaq](https://github.com/zufardhiyaulhaq).

Notable changes:
- config file
- triggering of sending of telemetry data from the battery - my VenusOS didn't publish any data unless I
repetedly published an empty message to a certain topic.

## Legal

Victron Energy are not affiliated with this project in any way. Do not bother them if you have any problems
with the code. Also, do not bother them or me if the code breaks your battery or causes your house to burn
to the ground. I only guarantee that this code works mostly on my setup and so far my house still stands. Other
than that there is no guarantee of any kind, especially not regarding the safety of this code or the fitness
for any purpose.
