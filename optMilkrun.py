import pandas as pd
from helper_funcs import *
from MoT import MoT
from Milkrun import Milkrun
from pyomo.environ import *
import numpy as np

# a = MoT('Standard 25to', 50, 25000, 13.6, 2.5, 2.48)
b = MoT('MEGA', 70, 25000, 13.62, 2.48, 3)
# c = MoT('PICKUP 3.5t', 60, 3500, 6.4, 2.5, 2.5)

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

data['pickups_deliveries'] = np.array(data['pickups_deliveries'])

model = ConcreteModel()

# Sets
tours = list(range(20)) # 20 is just a high estimate for # trucks required
# transport_orders = list(range(len(TO_list)))
model.transport_orders = RangeSet(0,len(TO_list)-1)
tariffs = list(range(3)) # 3 number of tariffs considered (0: LTL, 1: FTL, 2: Milkrun)


# Variables
model.x = Var(tours, model.transport_orders, domain=Binary, initialize=0)
model.y = Var(tours, tariffs, domain=Binary, initialize=0)

# Params
def orig_init(model, i):
    return data['pickups_deliveries'][:,0][i]

def dest_init(model, i):
    return data['pickups_deliveries'][:,1][i]

model.orig = Param(model.transport_orders, initialize = orig_init)
model.dest = Param(model.transport_orders, initialize = dest_init)

# Constraints  

# Tour must have one tariff
model.tariff = ConstraintList()
for w in tours:
    model.tariff.add(sum([model.y[w,ta] for ta in tariffs]) == 1)

# TO must be assigned
model.delivered = ConstraintList()
for to in model.transport_orders:
    model.delivered.add(sum([model.x[w,to] for w in tours]) == 1)

# truck size constraints
model.weight = ConstraintList()
model.volume = ConstraintList()
model.length = ConstraintList()
for w in tours:
    model.weight.add(sum([model.x[w,to] * TO_list[to].weight for to in model.transport_orders]) <= b.max_payload)
    model.volume.add(sum([model.x[w,to] * TO_list[to].volume for to in model.transport_orders]) <= b.max_vol)
    model.length.add(sum([model.x[w,to] * TO_list[to].length for to in model.transport_orders]) <= b.max_length)
   
# All direct transports (starting point before adding Milkruns)
model.direct_orig = ConstraintList()
model.direct_dest = ConstraintList()
for w in tours:
    model.direct_orig.add(sum([model.orig[to] for to in model.transport_orders]) <= 1)
    model.direct_dest.add(sum([model.dest[to] for to in model.transport_orders if model.x[w,to] == 1]) <= 1)


# Objective

# Cost function using the Milkrun class - gives an error
# def cost_func(mdl):
#     milkrun_list=[]
#     for w in tours:
#         to_add = []
#         for to in transport_orders:
#             if mdl.x[w,to] == 1:
#                 to_add.append(TO_list[to])
#         if len(to_add) > 0:
#             new_milkrun = Milkrun(to_add[0])
#             for i in range(1,len(to_add)):
#                 new_milkrun.add_to(to_add[i])
#             milkrun_list.append(new_milkrun)

#     tot_cost = 0
#     for milkrun in milkrun_list:
#         tot_cost += milkrun.cost
#     return tot_cost

# Cost function allowing pyomo to choose tariff
def cost_func(mdl):
    cost = 0
    for i in range(len(tours)):
        cost += mdl.y[i, 0] * get_tariff_dist(data['distance_matrix'][tuple(data['pickups_deliveries'][i - 1])],
                                              sum([value(model.x[i,to])*TO_list[to].weight for to in model.transport_orders])) + mdl.y[i, 1] * get_tariff_ftl(
            data['distance_matrix'][tuple(data['pickups_deliveries'][i - 1])]) + mdl.y[i,2]*1e6
    return cost

model.Cost = Objective(rule=cost_func, sense=minimize)

# Solve

instance = model.create_instance()
results = SolverFactory('glpk').solve(instance)
results.write()
# instance.display()
instance.solutions.load_from(results)


# Print Results 

milkrun_list=[]
for w in tours:
    to_add = []
    for to in model.transport_orders:
        if instance.x[(w,to)] == 1:
            to_add.append(TO_list[to])
    if len(to_add) > 0:
        new_milkrun = Milkrun(to_add[0])
        for i in range(1,len(to_add)):
            new_milkrun.add_to(to_add[i])
        milkrun_list.append(new_milkrun)

tot_cost = 0
assigned_TOs = 0
for milkrun in milkrun_list:
    tot_cost += milkrun.cost
    assigned_TOs += len(milkrun.TOs_covered)

print('Total Cost: ', tot_cost)
print("Assigned Transport Orders: "+ str(assigned_TOs) + '/' + str(len(TO_list)))

for i in milkrun_list:
    print(i.type, i.tour, i.tariff_type, i.cost, str([str(x) for x in i.TOs_covered]), i.total_weight(), i.total_volume(), i.total_length())