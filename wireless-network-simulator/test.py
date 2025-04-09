import argparse
import logging
import os
import signal
from threading import Event, Thread
import numpy.random as random
import pandas as pd
import matplotlib.pyplot as plt
import requests
from flask import Flask, request
from api import report_ue_metrics, report_cell_metrics
from utils import simulation_report, count_users_for_bs, handel_ts_control_msg, load_bs_config, random_anomaly
from wns2.basestation.nrbasestation import NRBaseStation
from wns2.userequipment.userequipment import UserEquipment
from wns2.environment.environment import Environment
import wns2.environment.environment
from wns2.renderer.renderer_json import JSONRendererARIES

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

app = Flask(__name__)
simulation_complete = Event()


def init_network():
    x_lim = 1000
    y_lim = 1000
    logger.info(f"Initializing network topology simulation with {x_lim}x{y_lim} m^2")
    env = Environment(x_lim, y_lim, renderer=JSONRendererARIES())
    wns2.environment.environment.MIN_RSRP = -75

    for i in range(0, 100):
        pos = (random.rand() * x_lim, random.rand() * y_lim, 1)
        env.add_user(UserEquipment(env, i,
                                   initial_data_rate=25,
                                   starting_position=pos,
                                   speed=5,
                                   direction=random.randint(0, 360),
                                   _lambda_c=5,
                                   _lambda_d=15))


    bs_parm = load_bs_config('setting_file.json')

    for i in range(1, len(bs_parm)):
        env.add_base_station(NRBaseStation(env, i, bs_parm[i]["pos"], bs_parm[i]["freq"], bs_parm[i]["bandwidth"],
                                           bs_parm[i]["numerology"], bs_parm[i]["max_bitrate"], bs_parm[i]["power"],
                                           bs_parm[i]["gain"], bs_parm[i]["loss"]))

    env.plot_topology(only_save=True, title="Network Topology")
    plt.close()

    counter = 0
    logger.info("Connecting UEs to the best BS")
    for k, ue in env.ue_list.items():
        try:
            ue.connect_max_rsrp()
            counter += 1
        except KeyError as e:
            logger.error(f"Error connecting UE{ue.ue_id} to BS: {e}")
    logger.info(f"Connected {counter} UEs to the best BS")
    return env


def run_simulator(env: Environment, iterations=200, traffic_accelerator=True, anomaly=None):
    name = 'wireless simulation'
    logger.info(f"Starting {name} with {iterations} steps ... Thread: {Thread.name}")



    df = simulation_report(env)
    cell_count = count_users_for_bs(env)

    for i in range(iterations):
        env.step()
        env.plot_topology(only_save=False, title=f"Network Topology {i}")
        plt.close()
        anomaly = random_anomaly(env)
        for ue in env.ue_list.values():
            if ue.get_current_bs() not in env.compute_rsrp(ue):
                curr_bs = ue.get_current_bs()
                ue.connect_max_rsrp()
                logger.info(f"UE{ue.ue_id} moved from BS{curr_bs} to BS{ue.get_current_bs()} *max RSRP*")

        if traffic_accelerator:
            if i >= 25:
                report_ue_metrics(env.ue_list, env, anomaly, i)
            else:
                report_ue_metrics(env.ue_list, env, None, i)
        else:
            report_ue_metrics(env.ue_list, env, None, i)

        report_cell_metrics(env.bs_list, step=i)

        # concat the reports from each step
        df = pd.concat([df, simulation_report(env)])
        cell_count = pd.concat([cell_count, count_users_for_bs(env, idx=i)])

        logger.info(f"Step {i} completed")
    # df.to_csv(f"csv_reports/simulation_report_{name}.csv")
    # cell_count.to_csv(f"csv_reports/cell_count_{name}.csv")
    logger.info("Simulation completed data saved to csv_reports folder")

    simulation_complete.set()
    os.kill(os.getpid(), signal.SIGINT)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


@app.route('/api/echo', methods=['POST'])
def receive():
    global env
    logger.info(f"TS Request received\n{request.json}")
    try:
        data = request.json
        if data is not None:
            handel_ts_control_msg(data, env)
            logger.info("TS Request handled")
            return data
        else:
            logger.info("No data received")
            return "No data received"

    except Exception as e:
        logger.error(f"Error receiving data: {e}")
        return "Error"


def parse_args():
    parser = argparse.ArgumentParser(description='Run network simulator with specified parameters')
    parser.add_argument('--iter', type=int, default=98, help='Number of iterations for the simulation')
    parser.add_argument('--seed', type=int, default=78, help='Random seed for reproducibility')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    iterations = args.iter
    seed = args.seed
    print(f"Starting simulation with {iterations} iterations")
    # Set the random seed
    random.seed(seed)
    logger.info(f"Random seed set to: {seed}")
    env = init_network()
    logger.info("Network initialized successfully")
    ts_thread = Thread(target=run_simulator, args=(env, iterations))
    ts_thread.start()

    logger.info("Starting Flask app")


    def run_flask():
        app.run(host='0.0.0.0', port=80)


    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    simulation_complete.wait()

    requests.post('http://0.0.0.0:80/shutdown')
    ts_thread.join()
    flask_thread.join()
    print("Application terminated")
