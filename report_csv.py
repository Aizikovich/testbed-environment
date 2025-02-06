import argparse
from influxdb import InfluxDBClient
import csv


def export_influx_to_csv(host, port, user, password, database, measurement, output_file):
    # Connect to InfluxDB
    client = InfluxDBClient(host=host, username=user, password=password, port=port, database=database)

    # Query data from InfluxDB
    query = f'SELECT * FROM "{measurement}"'
    result = client.query(query)

    # Write data to CSV file
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header
        csv_writer.writerow(result.raw['series'][0]['columns'])

        # Write data
        for row in result.raw['series'][0]['values']:
            csv_writer.writerow(row)

    print(f'Data exported to {output_file}')


def main():
    # InfluxDB connection details
    host = "10.98.44.43"
    port = 8086
    user = "admin"
    password = "JOmxp6DIOD"
    database = "RIC-Test"
    # measurement = "UEReports"
    # output_file = "UE_test.csv"
    parser = argparse.ArgumentParser(description='Export data from InfluxDB to CSV')
    parser.add_argument('--msr', required=True, help='InfluxDB measurement')
    parser.add_argument('--out', required=True, help='Output CSV file name')
    args = parser.parse_args()
    print(args)
    print("start exporting")
    export_influx_to_csv(host, port, user, password, database, args.msr, args.out)
    print("finished")


if __name__ == "__main__":
    main()
