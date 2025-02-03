import copy
import datetime
import json
import logging
import random
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


# logging.getLogger()

def report_ue_metrics(ues, env, anomaly_ue_id=-1, step=0):
    """
    ['DRB.UEThpDl', 'RF.serving.RSRP', 'RF.serving.RSSINR', 'RRU.PrbUsedDl', 'x', 'y']
    """
    data = []
    for ue in ues.values():
        ue_report = {
            "DRB.UEThpDl": random.uniform(1.0, 100.0),
            "RF.serving.RSRP": random.uniform(1.0, 100.0),
            "RF.serving.RSRQ": -40.0,
            "RF.serving.RSSINR": random.uniform(1.0, 100.0),
            "RRU.PrbUsedDl": random.uniform(1.0, 100.0),
            "Viavi.UE.anomalies": random.randint(0, 1),
            "step": step,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nbCellIdentity_0": None,
            "nbCellIdentity_1": None,
            "nbCellIdentity_2": None,
            "nbCellIdentity_3": None,
            "nbCellIdentity_4": None,
            "nrCellIdentity": None,
            "rsrp_nb0": random.uniform(1.0, 100.0),
            "rsrp_nb1": random.uniform(1.0, 100.0),
            "rsrp_nb2": random.uniform(1.0, 100.0),
            "rsrp_nb3": random.uniform(1.0, 100.0),
            "rsrp_nb4": random.uniform(1.0, 100.0),
            "rsrq_nb0": -40.0,  # 'x' means 'not available'
            "rsrq_nb1": -40.0,
            "rsrq_nb2": -40.0,
            "rsrq_nb3": -40.0,
            "rsrq_nb4": -40.0,
            "rssinr_nb0": random.uniform(1.0, 100.0),
            "rssinr_nb1": random.uniform(1.0, 100.0),
            "rssinr_nb2": random.uniform(1.0, 100.0),
            "rssinr_nb3": random.uniform(1.0, 100.0),
            "rssinr_nb4": random.uniform(1.0, 100.0),
            "targetTput": random.uniform(1.0, 100.0),
            "ue-id": f'UE{ue.ue_id}',
            "x": 0.0,
            "y": 0.0,
        }

        # positions
        x, y = ue.get_position()[0], ue.get_position()[1]
        ue_report["x"] = x
        ue_report["y"] = y
        # serving cell
        serving_bs = ue.get_current_bs()
        ue_report["nrCellIdentity"] = str(serving_bs)
        # throughput
        # print("\n",ue.bs_data_rate_allocation ,f"{ue}","\n")
        discover = ue.bs_data_rate_allocation
        if discover == {}:
            print("discover is empty")
        serving_thp = ue.bs_data_rate_allocation[serving_bs]
        ue_report["DRB.UEThpDl"] = serving_thp
        # rsrp
        bss_rsrp = env.compute_rsrp(ue)

        try:
            serving_rsrp = bss_rsrp[serving_bs]
        except KeyError:
            print(f"Error while computing RSRP for UE{ue.ue_id} at BS{serving_bs}")
            print(f"bss_rsrp: {bss_rsrp}")
            return None

        ue_report["RF.serving.RSRP"] = serving_rsrp
        # sinr
        serving_sinr = env.bs_list[serving_bs].compute_sinr(bss_rsrp)
        ue_report["RF.serving.RSSINR"] = serving_sinr
        # get neighboring cells
        nb_cells = copy.deepcopy(bss_rsrp)
        # remove serving cell from neighboring cells dict
        nb_cells.pop(serving_bs)
        for j, (i, nb_cell) in enumerate(nb_cells.items()):
            # update neighboring cells
            ue_report[f"nbCellIdentity_{j}"] = str(i)
            rsrp = nb_cell
            sinr = env.bs_list[i].compute_sinr(bss_rsrp)
            ue_report[f"rsrp_nb{j}"] = rsrp
            ue_report[f"rssinr_nb{j}"] = sinr

        if anomaly_ue_id == ue.ue_id:
            # print(f"Anomaly detected at UE{ue.ue_id}")
            # print(f"RSRP before: {ue_report['RF.serving.RSRP']}, RSSINR before: {ue_report['RF.serving.RSSINR']}")
            ue_report["RF.serving.RSSINR"] += random.randint(-100, 100)
            ue_report["RF.serving.RSRQ"] += random.randint(-100, 100)
            # print(f"RSRP after: {ue_report['RF.serving.RSRP']}, RSSINR after: {ue_report['RF.serving.RSSINR']}")

        data.append(ue_report)

    ue_data = json.dumps(data)
    try:
        response = requests.post("http://127.0.0.1:5001/receive_ue", json=json.loads(ue_data))
        return response
    except Exception as e:
        logging.error(f"Error While sending UE data: {e}")
        # print(f"Error While sending UE data:\n{e}")


def report_cell_metrics(bss_list, step=0):
    data = []
    for j, (i, bs) in enumerate(bss_list.items()):
        actual_data_rate = bs.allocated_data_rate

        cell_report = {
            "step": step,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nrCellIdentity": str(i),  # as string
            "throughput": actual_data_rate,
            "x": bs.position[0],
            "y": bs.position[1],
            "availPrbDl": random.randint(1, 100),
            "availPrbUl": random.randint(1, 100),
            "measPeriodPrb": bs.allocated_prb,
            "pdcpBytesUl": actual_data_rate,
            "pdcpBytesDl": actual_data_rate,
            "measPeriodPdcpBytes": random.randint(1, 100)
        }
        data.append(cell_report)
    cell_data = json.dumps(data)

    try:
        response = requests.post('http://127.0.0.1:5002/receive_cell', json=json.loads(cell_data))
        return response
    except Exception as e:
        logging.error(f"Error While sending cell data: {e}")
