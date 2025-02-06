import datetime
from flask import Flask
from influxdb import DataFrameClient
from configparser import ConfigParser
from mdclogpy import Logger
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException, ConnectionError
import time

logger = Logger(name=__name__)


class DATABASE:
    def __init__(self):
        self.data = None
        self.client = None
        self.config()

    def config(self):
        cfg = ConfigParser()
        cfg.read('config.ini')

        if 'influxdb' in cfg.sections():
            self.host = cfg.get('influxdb', 'host')
            self.port = cfg.get('influxdb', 'port')
            self.user = cfg.get('influxdb', 'user')
            self.password = cfg.get('influxdb', 'password')
            self.path = cfg.get('influxdb', 'path')
            self.ssl = cfg.getboolean('influxdb', 'ssl')
            self.dbname = cfg.get('influxdb', 'database')

        if 'measurements' in cfg.sections():
            self.ue_meas = cfg.get('measurements', 'ue_reports')
            self.cell_meas = cfg.get('measurements', 'cell_reports')

    def connect(self):
        if self.client is not None:
            self.client.close()

        try:
            self.client = DataFrameClient(
                self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                path=self.path,
                ssl=self.ssl,
                database=self.dbname,
                verify_ssl=self.ssl
            )
            version = self.client.request('ping', expected_response_code=204).headers['X-Influxdb-Version']
            logger.info(f"Connected to InfluxDB version: {version}")
            return True
        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError):
            logger.error("Failed to connect to InfluxDB. Check hostname/URL.")
            time.sleep(120)

    def query(self, query):
        try:
            return self.client.query(query)
        except (RequestException, InfluxDBClientError, InfluxDBServerError) as e:
            logger.error(f'Failed to connect to InfluxDB: {e}')
            return False