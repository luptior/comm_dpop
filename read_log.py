import numpy as np
import pandas as pd

df = pd.DataFrame(columns=[1,2,3,4,5,6,7,8,9,10])


num_agent = 5
agent_type="list"
network_customization=True
network_speed=10
comp_customization=False
comp_speed=100

dir="log"

# domain_range=[5, 10, 20, 30, 40, 50]
domain_range=[5]
repo_range=range(1,2)
frames = {}

for network_protocol in ["TCP"]:
    frames[network_protocol] = pd.DataFrame(columns=domain_range)
    for domain_size in domain_range:
        # for repo_id in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        read_list = []
        for repo_id in repo_range:
            f = f"{dir}/{network_protocol}_a{num_agent}_d{domain_size}_r{repo_id}_p0.5p0.5_{agent_type}_network{network_customization}{network_speed}_comp{comp_customization}{comp_speed}.log"
            try:
                with open(f, "r") as log:
                    lines = log.readlines()
                    if len(lines) > 2:
                        # read_list.append(int(lines[-1].strip()))
                        # print(lines[-1])
                        read_list.append(float(lines[-1].split(" ")[1]))
            except FileNotFoundError:
                continue
                print(f"FileNotFoundError: {f}")
        # print(read_list)
        average = np.average(read_list)
        print(average)
