# Writer to the InfluxDB

This app listens to the simulators measurements and writes the cells and UEs KPIs to the InfluxDB pod in RIC.

Before runnning a simulation scenario make sure this app runs and listens to the simulator measurements.

1. UE Flask first, as it create the measurements in influxDB pod.
```
cd src/
python3 ue.py
```
2. In another terminal run the cell app.
```
cd src/
python3 cell.py
```

