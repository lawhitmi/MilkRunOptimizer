# This is the first attempt using Pyomo to solve the problem

from pyomo.environ import *
import pandas as pd
from helper_funcs import *
import numpy as np
from MoT import MoT
from Milkrun import Milkrun
from itertools import permutations

data = {'distance_matrix': np.array([
    [0, 170, 210, 2219, 1444, 2428],  # Nuremberg
    [170, 0, 243, 2253, 1369, 2354],  # Munich
    [210, 243, 0, 2042, 1267, 2250],  # Stuttgart
    [2219, 2253, 2042, 0, 1127, 579],  # Supplier Porto
    [1444, 1369, 1267, 1127, 0, 996]  # Supplier Barcelona
])}

TO_list = get_to_list()

data['pickups_deliveries'] = []
for i in TO_list:
    data['pickups_deliveries'].append([i.origin, i.destination])

model = ConcreteModel()

# Sets
tariffs = list(range(1, 1 + len(TO_list)))

# Variables
model.x = Var(
    tariffs, [1, 2],
    within=Binary,
    doc="TO utilizes LTL if (i,1) is 1 or FTL if (i,2) is 1"
)
# Constraints

# TO must have a tariff applied (i.e. must be pickedup and delivered)
model.Constraint1 = ConstraintList()
for i in range(1, 1 + len(TO_list)):
    model.Constraint1.add(expr=model.x[i, 1] + model.x[i, 2] >= 1)

# Objective

def cost_func(mdl):
    cost = 0
    for i in range(1, 1 + len(TO_list)):
        cost += mdl.x[i, 1] * get_tariff_dist(data['distance_matrix'][tuple(data['pickups_deliveries'][i - 1])],
                                              TO_list[i - 1].weight) + mdl.x[i, 2] * get_tariff_ftl(
            data['distance_matrix'][tuple(data['pickups_deliveries'][i - 1])])
    return cost


def cost_to(to, ltl, ftl):
    return ltl * get_tariff_dist(data['distance_matrix'][tuple(data['pickups_deliveries'][to - 1])],
                                 TO_list[to - 1].weight) + ftl * get_tariff_ftl(
        data['distance_matrix'][tuple(data['pickups_deliveries'][to - 1])])


model.Cost = Objective(rule=cost_func, sense=minimize)



# Solve

instance = model.create_instance()
results = SolverFactory('glpk').solve(instance)
results.write()
instance.display()
instance.solutions.load_from(results)


# Build MilkRuns

a = MoT('Standard 25to', 50, 25000, 13.6, 2.5, 2.48)
b = MoT('MEGA', 70, 25000, 13.62, 2.48, 3)
c = MoT('PICKUP 3.5t', 60, 3500, 6.4, 2.5, 2.5)

# Build TO list using tariffs chosen from pyomo above
tos = pd.DataFrame({"transportOrder": [to.order_num for to in TO_list], "origin": [to.origin for to in TO_list],
                    "destination": [to.destination for to in TO_list], "weight": [to.weight for to in TO_list],
                    "length": [to.length for to in TO_list], "volume": [to.volume for to in TO_list],
                    "cost": [cost_to(to, instance.x[(to, 1)].value, instance.x[(to, 2)].value) for to in
                             range(1, 1 + len(TO_list))], "milkrun": False, "considered": False})
tos = tos.sort_values(by=["cost"], ascending=False)
milkrun_list = []


def find_to(to_name):
    """Returns the first entry in the list of TOs which matches the passed destination"""
    for to in TO_list:
        if to.order_num == to_name:
            return to

def tsp_dist(milkrun):
    """
    Fully enumerates the possibilities for a tour in each case (inbound and outbound) 
    and returns the shortest distance for use in milkrun tariff calculation.
    """
    if milkrun.type == "inbound":
        perm = permutations(milkrun.origins)
        min_dist = 1E6
        for i in perm:
            dist = data['distance_matrix'][i[0],i[1]]+data['distance_matrix'][i[1],next(iter(milkrun.destinations))]
            if dist < min_dist:
                min_dist = dist
                best = i
        return min_dist
    elif milkrun.type == "outbound":
        perm = permutations(milkrun.destinations)
        min_dist = 1E6
        for i in perm:
            dist = data['distance_matrix'][next(iter(milkrun.origins)),i[0]]
            for j in range(len(i)-1):
                dist += data['distance_matrix'][i[j],i[j+1]]
            if dist < min_dist:
                min_dist = dist
                best = i
        return min_dist

def calc_milkrun_cost(milkrun):
    if milkrun.type == "neither":
        result = min(get_tariff_dist(
            data['distance_matrix'][(next(iter(milkrun.origins)), next(iter(milkrun.destinations)))],
            milkrun.total_weight()), get_tariff_ftl(
            data['distance_matrix'][(next(iter(milkrun.origins)), next(iter(milkrun.destinations)))]))
    else:
        #This equation needs to be updated to reflect the actual distance (mini-TSP)
        dist = tsp_dist(milkrun)
        num_stops = len(milkrun.origins)+len(milkrun.destinations)-2 #subtract origin and destination stops
        result = get_tariff_milk(dist, num_stops)
    milkrun.cost = result
    return result


total_cost_no_milkrun = tos["cost"].sum()

while len(tos[~tos["considered"]].index) > 0:
    to_consider = tos[~tos["considered"] & ~tos["milkrun"]][:1]
    tos.loc[tos["transportOrder"].str.match(to_consider["transportOrder"][to_consider.index[0]]), "considered"] = True
    new_milkrun = Milkrun(find_to(to_consider["transportOrder"][to_consider.index[0]]))
    while True:
        # first consider true milkruns
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
        old_cost = calc_milkrun_cost(new_milkrun)
        added = False
        for add in to_add.index:
            type_compatible = new_milkrun.add_to(find_to(to_add["transportOrder"][add]))
            if type_compatible:
                if calc_milkrun_cost(new_milkrun) < old_cost + to_add["cost"][add]:
                    added = True
                    tos.loc[tos["transportOrder"].str.match(
                        to_consider["transportOrder"][to_consider.index[0]]), "milkrun"] = True
                    tos.loc[tos["transportOrder"].str.match(to_add["transportOrder"][add]), "milkrun"] = True
                    tos.loc[tos["transportOrder"].str.match(to_add["transportOrder"][add]), "considered"] = True
                    break
                else:
                    new_milkrun.pop()
        if added:
            continue
        # now consider fake milkruns, i.e. combinations of TO with same OD
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
        for add in to_add.index:
            type_compatible = new_milkrun.add_to(find_to(to_add["transportOrder"][add]))
            if type_compatible:
                if calc_milkrun_cost(new_milkrun) < old_cost + to_add["cost"][add]:
                    added = True
                    tos.loc[tos["transportOrder"].str.match(
                        to_consider["transportOrder"][to_consider.index[0]]), "milkrun"] = True
                    tos.loc[tos["transportOrder"].str.match(to_add["transportOrder"][add]), "milkrun"] = True
                    tos.loc[tos["transportOrder"].str.match(to_add["transportOrder"][add]), "considered"] = True
                    break
                else:
                    new_milkrun.pop()
        if ~added:
            if new_milkrun.number_of_tos() > 1:
                milkrun_list.append(new_milkrun)
            break

print(tos[~tos["milkrun"]])
total_cost = tos[~tos["milkrun"]]["cost"].sum()
for milkrun in milkrun_list:
    total_cost += milkrun.cost
    print(str(milkrun) + "\n")
print("Total cost without milkruns: " + str(total_cost_no_milkrun))
print("Total cost: " + str(total_cost))