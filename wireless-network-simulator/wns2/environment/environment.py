import logging
from wns2.userequipment.multipath_userequipment import MultiPathUserEquipment
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec
import numpy as np

# import wns2.environment.util as util
MIN_RSRP = -140

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


class Environment:
    def __init__(self, h, l, sampling_time=1, renderer=None):
        self.h = h
        self.l = l
        self.ue_list = {}
        self.connection_advertisement = []
        self.bs_list = {}
        self.sampling_time = sampling_time  # in seconds
        self.renderer = renderer
        self.plt_run = 0

        self.drone_aps = []
        return

    def add_user(self, ue):
        if ue.get_id() in self.ue_list:
            raise Exception("UE ID mismatch for ID %s", ue.get_id())
        self.ue_list[ue.get_id()] = ue
        return

    def remove_user(self, ue_id):
        if ue_id in self.ue_list:
            if self.ue_list[ue_id].get_current_bs() != None:
                bs = self.ue_list[ue_id].get_current_bs()
                self.ue_list[ue_id].disconnect(bs)
            del self.ue_list[ue_id]

    def add_base_station(self, bs):
        if bs.get_id() in self.bs_list:
            raise Exception("BS ID mismatch for ID %s", bs.get_id())
        self.bs_list[bs.get_id()] = bs
        if bs.bs_type == "drone":
            self.drone_aps.append(bs.get_id())
        return

    def compute_rsrp(self, ue):
        rsrp = {}
        for bs in self.bs_list:
            rsrp_i = self.bs_list[bs].compute_rsrp(ue)
            if rsrp_i > MIN_RSRP or self.bs_list[bs].get_bs_type() == "sat":
                rsrp[bs] = rsrp_i
        return rsrp

    def advertise_connection(self, ue_id):
        self.connection_advertisement.append(ue_id)
        return

    def step(self, substep=False):
        # substep indicates if it is just a substep or it is a complete step
        # if substep, then the connection advertisement list should not be updated
        # nor the UEs should update their internal timers to decide if it is time to connect/disconnect
        if not substep:
            self.connection_advertisement.clear()
        for ue in self.ue_list:
            # print(type(self.ue_list[ue]))
            # self.ue_list[ue].step(substep)

            self.ue_list[ue].step()
        for bs in self.bs_list:
            self.bs_list[bs].step()
        '''       
        # disconnect all the users, in order to reconnect them to the right AP and with the right datarate
        for i in range(len(self.ue_list)):
            self.ue_by_id(i).disconnect_all()
        # call here the optimizator, taking the w from users (with data_generation_status and input_data_rate)    
        N = len(self.connection_advertisement)
        M = len(self.bs_list)
        q = np.zeros(N)
        w = np.zeros(N)
        P = np.zeros((N, M))
        for i in range(N):
            ue = self.ue_by_id(self.connection_advertisement[i])
            q[i] = ue.get_queue()
            w[i] = ue.get_current_input_data_rate()
            rsrp = ue.measure_rsrp()
            for bs in rsrp:
                P[i, bs] = 1
        u_final = util.output_datarate_optimization(q, w, N, M, P, self.sampling_time, Q_max = MultiPathUserEquipment.MAX_QUEUE)
        # set the desired data rate for all the users, connecting to the BSs
        for i in range(N):
            ue = self.ue_by_id(self.connection_advertisement[i])
            connection_list = []
            for bs in range(M):
                if u_final[i, bs] > 0 and P[i, bs] == 1:
                    ue.output_data_rate[bs] = u_final[i, bs]
                    connection_list.append(bs)
            ue.connect_bs(connection_list)
        # move the drone AP according to the weighted average of the positions of the UEs connected to it
        for drone_ap in self.drone_aps:
            u_drone = []
            x_ue = []
            y_ue = []
            for i in range(N):
                if P[i, drone_ap] == 1:
                    u_drone.append(u_final[i, drone_ap])
                    pos = self.ue_by_id(i).get_position()
                    x_ue.append(pos[0])
                    y_ue.append(pos[1])
            bs = self.bs_by_id(drone_ap)
            u_0 = 0 # weight of the current position of the drone
            x_drone = bs.get_position()[0]
            y_drone = bs.get_position()[1]
            z_drone = bs.get_position()[2]
            new_drone_pos = util.build_drone_pos_ref(u_drone, x_ue, y_ue, u_0, x_drone, y_drone)
            new_drone_pos = (new_drone_pos[0], new_drone_pos[1], z_drone)
            #print("OLD DRONE POSITION: (%s, %s) ---> NEW DRONE POSITION: (%s, %s)" %(x_drone, y_drone, new_drone_pos[0], new_drone_pos[1]))
            bs.move(new_drone_pos, speed=15)
        '''
        return

    def render(self):
        if self.renderer != None:
            return self.renderer.render(self)

    def bs_by_id(self, id):
        return self.bs_list[id]

    def ue_by_id(self, id):
        return self.ue_list[id]

    def get_sampling_time(self):
        return self.sampling_time

    def get_x_limit(self):
        return self.l

    def get_y_limit(self):
        return self.h

    def plot_topology(self, annomaly=0, title="Topology", only_save=False):

        colors = cm.rainbow(np.linspace(0, 1, len(self.bs_list)+1))

        x_bs = {j: self.bs_list[j].get_position()[0] for j in self.bs_list}
        y_bs = {j: self.bs_list[j].get_position()[1] for j in self.bs_list}
        x_ue = {i: self.ue_list[i].get_position()[0] for i in self.ue_list}
        y_ue = {i: self.ue_list[i].get_position()[1] for i in self.ue_list}

        fig, ax = plt.subplots()

        bs_colors = {j: colors[k] for k, j in enumerate(self.bs_list)}
        for i in self.ue_list:
            for k, j in enumerate(self.bs_list):
                if j in self.ue_list[i].bs_data_rate_allocation:
                    curr_ue = self.ue_list[i]
                    if curr_ue.ue_id == annomaly:

                        ax.scatter(x_ue[i], y_ue[i], color="red")
                    else:
                        ax.scatter(x_ue[i], y_ue[i], color=bs_colors[curr_ue.get_current_bs()])
                    break
            else:
                ax.scatter(x_ue[i], y_ue[i], color="tab:grey")
        for i in self.ue_list:
            ax.annotate(str(i + 1), (x_ue[i], y_ue[i]))

        for k, j in enumerate(self.bs_list):
            ax.scatter(x_bs[j], y_bs[j], color=colors[k], label=f"BS{j}", marker="s", s=400)

        for j in self.bs_list:
            ax.annotate("BS" + str(j), (x_bs[j], y_bs[j]))
        ax.grid(True)
        ax.set_ylabel("[m]")
        ax.set_xlabel("[m]")
        ax.set_xlim(0, self.l)
        ax.set_ylim(0, self.h)
        plt.title(title)
        plt.savefig(f"plots/{title}.png")
        if not only_save:
            plt.show()
        return

    def plot_special_topology(self,annomaly=0, mali_cell=5, title="Topology", only_save=False, stolen_ues=None):

        colors = cm.rainbow(np.linspace(0, 1, 3))
        # print(colors)
        colors = ["lightblue", "pink", "red"]

        x_bs = {j: self.bs_list[j].get_position()[0] for j in self.bs_list}
        y_bs = {j: self.bs_list[j].get_position()[1] for j in self.bs_list}
        x_ue = {i: self.ue_list[i].get_position()[0] for i in self.ue_list}
        y_ue = {i: self.ue_list[i].get_position()[1] for i in self.ue_list}

        fig, ax = plt.subplots()

        # bs_colors = {j: colors[k] for k, j in enumerate(self.bs_list)}
        bs_colors = {}
        for k, j in enumerate(self.bs_list):

            if j == mali_cell:
                bs_colors[j] = colors[1]
            else:
                bs_colors[j] = colors[0]

        for i in self.ue_list:
            for k, j in enumerate(self.bs_list):
                if j in self.ue_list[i].bs_data_rate_allocation:
                    curr_ue = self.ue_list[i]

                    if curr_ue.ue_id in stolen_ues:
                        ax.scatter(x_ue[i], y_ue[i], color="red")
                        break
                    # if curr_ue.ue_id in stolen_ue:
                    #     # print("stolen_ue", curr_ue.ue_id)
                    #     ax.scatter(x_ue[i], y_ue[i], color="red")
                    # elif curr_ue.ue_id == annomaly:
                    #     ax.scatter(x_ue[i], y_ue[i], color="red")
                    else:
                        ax.scatter(x_ue[i], y_ue[i], color=bs_colors[curr_ue.get_current_bs()])
                    break
            else:
                ax.scatter(x_ue[i], y_ue[i], color="tab:grey")
        for i in self.ue_list:
            ax.annotate(str(i + 1), (x_ue[i], y_ue[i]))

        for k, j in enumerate(self.bs_list):

            if j == mali_cell:

                ax.scatter(x_bs[j], y_bs[j], color=colors[1], label=f"BS{j}", marker="s", s=400)
            else:
                ax.scatter(x_bs[j], y_bs[j], color=colors[0], label=f"BS{j}", marker="s", s=400)


        for j in self.bs_list:
            ax.annotate("BS" + str(j), (x_bs[j], y_bs[j]))
        ax.grid(True)
        ax.set_ylabel("[m]")
        ax.set_xlabel("[m]")
        ax.set_xlim(0, self.l)
        ax.set_ylim(0, self.h)
        plt.title(title)
        plt.savefig(f"plots/{title}.png")
        if not only_save:
            plt.show()
        return