# VenusOS Battery Telemetry to InfluxDB

## Purpose

`bat2influx` reads the battery's (DC) voltage, current, power, and state-of-charge (SOC) from a Victron
Energy VenusOS battery inverter/charger and the voltage, current and both active and apparent power and
frequence from the AC side and stores the values into an Influx database. From there the
user is free to use thease measurements to their liking, like displaying in a Grafana dashboard.

## How it works

`bat2influx` connects to the MQTT broker running on VenusOS and to the InfluxDB provided by the
user in parallel. It then triggers the sending of a telemetry message from VenusOS by publishing
an empty message to various topics starting with `R/<serialnumber>/vebus/275/` (every second) and to
`R/<serialnumber>/vebus/275/Soc` (every 10 seconds) and stores the received values inside an
InfluxDB database into a measurement (database name and measurement name are both configurable) under these fields:
- for DC: Current, Voltage, Power, Soc.
- for AC: I (current), V (voltage), P (power), S (apparent power)

## How it looks

Once the measurements are stored into Influx, a simple influxQL SELECT statement (I hate flux) looks
like this:

```
> select * from dc where time > now()-5s 
name: dc
time                           Current F       I     P    Power S    Soc  V      Voltage
----                           ------- -       -     -    ----- -    ---  -      -------
2025-02-21T22:08:01.788934596Z                            -738                   
2025-02-21T22:08:01.835538738Z                                                   52.06
2025-02-21T22:08:01.843789552Z -15                                               
2025-02-21T22:08:01.852458743Z                                       28.5        
2025-02-21T22:08:01.860366589Z                 -3.32                             
2025-02-21T22:08:01.869456173Z                       -749                        
2025-02-21T22:08:01.879514895Z                                  -804             
2025-02-21T22:08:01.903708535Z                                            242.33 
2025-02-21T22:08:01.9137971Z           50.1026                                   
2025-02-21T22:08:02.741105314Z                            -747                   
2025-02-21T22:08:02.764027173Z                                                   52.06
2025-02-21T22:08:02.772328114Z -14.9                                             
2025-02-21T22:08:02.779616795Z                 -3.32                             
2025-02-21T22:08:02.789391378Z                       -754                        
2025-02-21T22:08:02.796424865Z                                  -804             
2025-02-21T22:08:02.805218721Z                                            242.33 
2025-02-21T22:08:02.814819592Z         50.1026                                   
2025-02-21T22:08:03.68915136Z                             -737                   
2025-02-21T22:08:03.713972541Z                                                   52.06
2025-02-21T22:08:03.721916981Z -15.6                                             
2025-02-21T22:08:03.730049076Z                 -3.32                             
2025-02-21T22:08:03.738515146Z                       -763                        
2025-02-21T22:08:03.746770476Z                                  -804             
2025-02-21T22:08:03.755189383Z                                            242.33 
2025-02-21T22:08:03.763574336Z         50.1026                                   

```

By grouping these entries by second, the fields can be mapped into the same series (ignoring apparent power `S` here):
```
> select mean(Current) as DC_I, mean(Voltage) as DC_U, mean(Power) as DC_P, mean(Soc) as Soc, mean(I) as AC_I, mean(V) as AC_U, mean(P) as AC_P FROM dc WHERE here time > now()-5s GROUP BY time(1s)
name: dc
time                 DC_I  DC_U  DC_P Soc  AC_I  AC_V   AC_P
----                 ----  ----  ---- ---  ----  ----   ----
2025-02-21T22:08:01Z -15   52.06 -738 28.5 -3.32 242.33 -749
2025-02-21T22:08:02Z -14.9 52.06 -747      -3.32 242.33 -754
2025-02-21T22:08:03Z -15.6 52.06 -737      -3.32 242.33 -763
```

## How to configure

Just copy `bat2influx.template.ini` to `bat2influx.ini` and edit the values to your needs.

## How to run

### Run directly with Python

You need to have pip installed and use it to install the dependencies:  
`python -m pip install -r requirements.txt`

Then run the application:  
`python bat2influx.py`

### Run with Docker

If you have `bat2influx.ini` at a different path or use a different name, edit the `docker-compose.yml`
accordingly. Otherwise the defaults should be ok for you.

Then run it via docker in the directory where `docker-compose.yml` resides:  
`docker compose up -d`

This uses the docker image I created using the `Dockerfile` via GitHib Actions and pushed
to `ghcr.io/alestrix/bat2influx:latest`.

## To-Dos

- Testing - nobody except for me has ever run this code, so I have no idea whether some pecurilarities only
specific to my setup might still be hard-coded
- ~~Dockerize~~ (Done)
- ~~Make path of config file configurable via command line parameter~~ (not needed when containerized)
- ~~Reducing the effect of jitter: Maybe set wating time to 0.9s instead of 1s, thus making sure that every 1s-Interval
has **at least** one measurement. Best to make this conigurable.~~ (Done)

## Why?

Q: Why I didn't want to use [venus-influx-loader](https://github.com/victronenergy/venus-influx-loader):  
A:  
- It doesn't support password authentication towards the battery (i.e. towards the MQTT server)
- It reads a gazillion times more values and stores them into influx than I'm interested in
- It creates one measurement for every value stored, I wanted the values as different fields inside the same measurement

Q: Why is the project called venusos2influx and the program bat2influx?  
A: I changed my mind after I had set up the name and forgot about it. Now I don't bother changing it again.

Q: Why don't you just use modbus? It's less complicated than MQTT.
A: I didn't know how to do modbus at first. After I looked into it I found out that the AC-Power (`/Ac/ActiveIn/L1/P`) that
has a precission of 1 watt when read via MQTT only has a precission of 10 watts when read via modbus. That's a no-go for me.

## Mentions

The code is heavily based on [this](https://gist.github.com/zufardhiyaulhaq/fe322f61b3012114379235341b935539)
Gist by [Zufar Dhiyaulhaq](https://github.com/zufardhiyaulhaq).

Notable changes:
- config file
- triggering of sending of telemetry data from the battery - my VenusOS didn't publish any data unless I
repeatedly published an empty message to a certain topic.

## Legal

Victron Energy are not affiliated with this project in any way. Do not bother them if you have any problems
with the code. Also, do not bother them or me if the code breaks your battery or causes your house to burn
to the ground. I only guarantee that this code works mostly on my setup and so far my house still stands. Other
than that there is no guarantee of any kind, especially not regarding the safety of this code or the fitness
for any purpose.
