import json
import pandas as pd
import numpy as np
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def load_bs_config(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Check if the JSON has 'bs' or 'bs_parm' key
        if 'bs' in data:
            return data['bs']
        elif 'bs_parm' in data:
            return data['bs_parm']
        else:
            raise KeyError("JSON must contain either 'bs' or 'bs_parm' key")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except FileNotFoundError:
        print(f"Could not find file: {json_file_path}")
        return None


def handel_ts_control_msg(msg, env):
    ue_id = int(msg["ue"][2:])
    ue = env.ue_list[ue_id]
    from_cell = msg["fromCell"]
    to_cell_id = int(msg["toCell"])
    result = ue.connect_bs(to_cell_id)
    if result is None:
        logging.error(f"UE{ue_id} failed to connect to BS{to_cell_id}")
        logging.info(f"{ue} nb list: {env.compute_rsrp(ue)}")
    else:
        logging.info(f"UE{ue_id} moved from BS{from_cell} to BS{to_cell_id}")


def count_users_for_bs(env, idx=0):
    bs_users = {}
    for bs in env.bs_list.values():
        bs_users[f"BS{bs.bs_id}"] = 0
    for ue in env.ue_list.values():
        bs_users[f"BS{ue.get_current_bs()}"] += 1
    return pd.DataFrame(bs_users, index=[idx])


def simulation_report(env):
    ue_reports = []
    for ue in env.ue_list.values():
        u_report = {
            'ue-id': ue.ue_id,
            'x': ue.get_position()[0],
            'y': ue.get_position()[1],
            'nrCellIdentity': ue.get_current_bs(),
        }
        ue_reports.append(u_report)
    return pd.DataFrame(ue_reports)


def random_anomaly(env):
    np.random.seed(42)
    ue = np.random.choice(list(env.ue_list.values()))
    for _ in range(5):
        ue.move()
    return ue.ue_id
