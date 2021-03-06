import pandas as pd
from helper_funcs import *
from MoT import MoT
from Milkrun import Milkrun

TO_list = get_to_list()

# Build MilkRuns

# a = MoT('Standard 25to', 50, 25000, 13.6, 2.5, 2.48)
b = MoT('MEGA', 70, 25000, 13.62, 2.48, 3)
# c = MoT('PICKUP 3.5t', 60, 3500, 6.4, 2.5, 2.5)

# Build TO list Dataframe
tos = pd.DataFrame({"transportOrder": [to.order_num for to in TO_list], "origin": [to.origin for to in TO_list],
                    "destination": [to.destination for to in TO_list], "weight": [to.weight for to in TO_list],
                    "length": [to.length for to in TO_list], "volume": [to.volume for to in TO_list],
                    "milkrun": False, "considered": False})
tos['density'] = tos['weight'] / tos['volume']

# Sort by various columns to find minimum baseline cost
# tos = tos.sort_values(by=["weight"], ascending=False)
# tos = tos.sort_values(by=["length"], ascending=False)
tos = tos.sort_values(by=["volume"], ascending=False)
# tos = tos.sort_values(by=["density"], ascending=False)

milkrun_list = []


def find_to(to_name):
    """Returns the first entry in the list of TOs which matches the passed destination"""
    for to in TO_list:
        if to.order_num == to_name:
            return to

# Greedy Knapsack packs trucks with TOs sharing origin/destination (order based on sorting above)
while len(tos[~tos["considered"]].index) > 0:
    to_consider = tos[~tos["considered"] & ~tos["milkrun"]][:1]
    tos.loc[tos["transportOrder"].str.match(to_consider["transportOrder"][to_consider.index[0]]), "considered"] = True
    tos.loc[tos["transportOrder"].str.match(
                to_consider["transportOrder"][to_consider.index[0]]), "milkrun"] = True
    new_milkrun = Milkrun(find_to(to_consider["transportOrder"][to_consider.index[0]]))
    milkrun_list.append(new_milkrun)
    while True:
        added=False
        to_add = tos.query(
            '~milkrun and ~considered and ((origin == ' + str(to_consider["origin"][to_consider.index[0]])
            + ') and (destination == '
            + str(to_consider["destination"][to_consider.index[0]])
            + ')) and weight < '
            + str(b.max_payload - new_milkrun.total_weight())
            + ' and length < '
            + str(b.max_length - new_milkrun.total_length())
            + ' and volume <'
            + str(b.max_vol - new_milkrun.total_volume()))
        if len(to_add) > 0:
            new_milkrun.add_to(find_to(to_add.iloc[0]['transportOrder']))
            tos.loc[tos["transportOrder"].str.match(to_add.iloc[0]['transportOrder']), "milkrun"] = True
            tos.loc[tos["transportOrder"].str.match(to_add.iloc[0]['transportOrder']), "considered"] = True
        else:
            break
        
 
tot_cost = 0
assigned_TOs = 0
for milkrun in milkrun_list:
    tot_cost += milkrun.cost
    assigned_TOs += len(milkrun.TOs_covered)

print('Total Cost: ', tot_cost)
# by volume : 7441
# by density : 7881.4
# by weight : 7881.4
# by length : 7441

print("Assigned Transport Orders: "+ str(assigned_TOs) + '/' + str(len(TO_list)))


#Print Results
for i in milkrun_list:
    print(i.type, i.tour, i.tariff_type, i.cost, str([str(x) for x in i.TOs_covered]), i.total_weight(), i.total_volume(), i.total_length())