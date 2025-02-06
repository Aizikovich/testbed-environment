# ==================================================================================
#  Copyright (c) 2020 HCL Technologies Limited.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ==================================================================================

"""
This Module is temporary for pushing data into influxdb before dpeloyment of QP xApp. It will depreciated in future, when data will be coming through KPIMON
"""

import datetime
from flask import Flask, request
from influxdb import DataFrameClient
from configparser import ConfigParser
from mdclogpy import Logger
from exceptions import NoDataError
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException
import pandas as pd
import time

logger = Logger(name=__name__)


class DATABASE(object):

    def __init__(self, dbname='Timeseries', user='root', password='root', host="r4-influxdb.ricplt", port='8086', path='', ssl=False):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.path = path
        self.ssl = ssl
        self.dbname = dbname
        self.data = None
        self.client = None
        self.config()

    def connect(self):
        if self.client is not None:
            self.client.close()

        try:
            self.client = DataFrameClient(self.host, port=self.port, username=self.user, password=self.password, path=self.path, ssl=self.ssl, database=self.dbname, verify_ssl=self.ssl)
            version = self.client.request('ping', expected_response_code=204).headers['X-Influxdb-Version']
            logger.info("Conected to Influx Database, InfluxDB version : {}".format(version))
            return True

        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError):
            logger.error("Failed to establish a new connection with InflulxDB, Please check your url/hostname")
            time.sleep(120)

    def read_data(self, meas='ueMeasReport', limit=10000, cellid=False, ueid=False):

        if cellid:
            meas = self.cellmeas
            param = self.cid
            Id = cellid

        if ueid:
            meas = self.uemeas
            param = self.ue
            limit = 1
            Id = ueid

        # select * from {Measurement} where {param} = {Id} ORDER BY DESC LIMIT {limit}
        query = """select * from {}""".format(meas)
        query += """ where "{}" = \'{}\'""".format(param, Id)
        query += "  ORDER BY DESC LIMIT {}".format(limit)
        print(f"in {__name__} read_data(), query: {query}")
        self.query(query, meas, Id)

    def query(self, query, meas, Id=False):
        try:
            result = self.client.query(query)
            if len(result) == 0:
                raise NoDataError
            else:
                self.data = result[meas]

        except (RequestException, InfluxDBClientError, InfluxDBServerError):
            logger.error("Failed to connect to influxdb")

        except NoDataError:
            self.data = None
            if Id:
                logger.error("Data not found for " + Id + " in measurement: "+meas)
            else:
                logger.error("Data not found for " + meas)

    def cells(self, meas='CellReports', limit=100):
        meas = self.cellmeas
        query = """select * from {}""".format(meas)
        query += " ORDER BY DESC LIMIT {}".format(limit)
        self.query(query, meas)
        if self.data is not None:
            return self.data[self.cid].unique()

    def write_prediction(self, df, meas_name='QP'):
        try:
            self.client.write_points(df, meas_name)
        except (RequestException, InfluxDBClientError, InfluxDBServerError):
            logger.error("Failed to send metrics to influxdb")

    def config(self):
        cfg = ConfigParser()
        cfg.read('qp_config.ini')
        for section in cfg.sections():
            if section == 'influxdb':
                self.host = cfg.get(section, "host")
                self.port = cfg.get(section, "port")
                self.user = cfg.get(section, "user")
                self.password = cfg.get(section, "password")
                self.path = cfg.get(section, "path")
                self.ssl = cfg.get(section, "ssl")
                self.dbname = cfg.get(section, "database")

            if section == 'measurements':
                self.cellmeas = cfg.get(section, "cell_reports")
                self.uemeas = cfg.get(section, "ue_reports")

            if section == 'cell_features':
                self.thptparam = [cfg.get(section, "thptUL"), cfg.get(section, "thptDL")]
                self.nbcells = cfg.get(section, "nbcells")
                self.servcell = cfg.get(section, "servcell")
                self.ue = cfg.get(section, "ue")
                self.cid = cfg.get(section, "cid")





app = Flask(__name__)

class INSERTDATA(DATABASE):

    def __init__(self):
        super().__init__()
        self.connect()

    def createdb(self, dbname):
        print("Create database: " + dbname)
        self.client.create_database(dbname)
        self.client.switch_database(dbname)

    def dropdb(self, dbname):
        print("DROP database: " + dbname)
        self.client.drop_database(dbname)

    def dropmeas(self, measname):
        print("DROP MEASUREMENT: " + measname)
        self.client.query('DROP MEASUREMENT '+measname)

    # def assign_timestamp(self, df):
    #     steps = df['measTimeStampRf'].unique()
    #     for timestamp in steps:
    #         d = df[df['measTimeStampRf'] == timestamp]
    #         d.index = pd.date_range(start=datetime.datetime.now(), freq='1ms', periods=len(d))
    #         self.client.write_points(d, self.cellmeas)
    #         time.sleep(0.4)
    def assign_timestamp(self, data):
        df = pd.DataFrame(data)
        # Do something with the data here
        # time.sleep(1)  # Simulate a delay
        steps = df['measTimeStampRf'].unique()
        for timestamp in steps:
            d = df[df['measTimeStampRf'] == timestamp]
            d.index = pd.date_range(start=datetime.datetime.now(), freq='1ms', periods=len(d))
            self.client.write_points(d, self.cellmeas)
            time.sleep(0.4)


def populatedb():
    # inintiate connection and create database UEDATA
    db = INSERTDATA()
    df = pd.read_csv('src/cells.csv')
    print("Writin data into influxDB")
    while True:
        db.assign_timestamp(df)

@app.route('/receive_cell', methods=['POST'])
def receive_cell():

    try:
        received_data = request.json
        #print(received_data)
        #print("Received data:", pd.DataFrame(received_data), flush=True)
        if received_data is not None:
            db.assign_timestamp(received_data)
            received_data = None
        else:
            # db.assign_timestamp("No data received")
            time.sleep(1)
        return "Data received successfully!"

    except Exception as e:
        print("Error:", e, flush=True)
        return "Error occurred while receiving data"


if __name__ == "__main__":
    db = INSERTDATA()
    app.run(host="0.0.0.0", port=5002, threaded=True)