import pandas as pd
from helper_funcs import *
from MoT import MoT
from Milkrun import Milkrun

NUM_SUPPLIERS = 2

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
# tos = tos.sort_values(by=["volume"], ascending=False)
tos = tos.sort_values(by=["density"], ascending=False)

milkrun_list = []


def find_to(to_name):
    """Returns the first entry in the list of TOs which matches the passed destination"""
    for to in TO_list:
        if to.order_num == to_name:
            return to

milkrun_count = 0
while milkrun_count < NUM_SUPPLIERS:
    # if a milkrun is already created, don't create another originating from same location
    if len(milkrun_list) > 0:
        to_consider = tos[~tos["considered"] & ~tos["milkrun"] & (tos["origin"]!=next(iter(milkrun_list[0].origins)))][:1]
    else:
        to_consider = tos[~tos["considered"] & ~tos["milkrun"]][:1]
    tos.loc[tos["transportOrder"].str.match(to_consider["transportOrder"][to_consider.index[0]]), "considered"] = True
    tos.loc[tos["transportOrder"].str.match(to_consider["transportOrder"][to_consider.index[0]]), "milkrun"] = True
    new_milkrun = Milkrun(find_to(to_consider["transportOrder"][to_consider.index[0]]))
    milkrun_list.append(new_milkrun)
    while True:
        if len(milkrun_list) > 0:
            # can't do a inbound in this case, origin must match.
            to_add = tos.query(
                '~milkrun and ~considered and (origin == ' + str(to_consider["origin"][to_consider.index[0]])
                + ') and weight < '
                + str(b.max_payload - new_milkrun.total_weight())
                + ' and length < '
                + str(b.max_length - new_milkrun.total_length())
                + ' and volume <'
                + str(b.max_vol - new_milkrun.total_volume()))
        else:
            to_add = tos.query(
                '~milkrun and ~considered and ((origin == ' + str(to_consider["origin"][to_consider.index[0]])
                + ') != (destination == '
                + str(to_consider["destination"][to_consider.index[0]])
                + ')) and weight < '
                + str(b.max_payload - new_milkrun.total_weight())
                + ' and length < '
                + str(b.max_length - new_milkrun.total_length())
                + ' and volume <'
                + str(b.max_vol - new_milkrun.total_volume()))
        if len(to_add) > 0:
            type_compatible = new_milkrun.add_to(find_to(to_add.iloc[0]['transportOrder']))
            if type_compatible:
                tos.loc[tos["transportOrder"].str.match(to_add.iloc[0]['transportOrder']), "milkrun"] = True
                tos.loc[tos["transportOrder"].str.match(to_add.iloc[0]['transportOrder']), "considered"] = True
            else:
                new_milkrun.pop()
        else:
            if new_milkrun.type=="inbound":
                milkrun_count = NUM_SUPPLIERS
            elif new_milkrun.type == "outbound" or new_milkrun.type=="neither": #neither is here to prevent the case where it tries to add a 3rd milkrun if an origin only has TOs with one destination option.
                milkrun_count += 1
            break

# add the remaining TOs to direct tariff tours (Greedy)
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
for milkrun in milkrun_list:
    tot_cost += milkrun.cost
print("Total Cost: ", tot_cost)

for i in milkrun_list:
    print(i.type, i.tour, i.tariff_type, i.cost, str([str(x) for x in i.TOs_covered]), i.total_weight(), i.total_volume(), i.total_length())