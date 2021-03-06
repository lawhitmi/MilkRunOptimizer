import pandas as pd
from helper_funcs import *
from MoT import MoT
from Milkrun import Milkrun
from pyomo.environ import *

a = MoT('Standard 25to', 50, 25000, 13.6, 2.5, 2.48)
b = MoT('MEGA', 70, 25000, 13.62, 2.48, 3)
c = MoT('PICKUP 3.5t', 60, 3500, 6.4, 2.5, 2.5)

TO_list = get_to_list()

model = ConcreteModel()

# Sets
tours = list(range(20))
transport_orders = list(range(len(TO_list)))

# Variables
model.x = Var(tours, transport_orders, domain=Binary, initialize=0)

# Constraints  

#TO must be assigned
model.delivered = ConstraintList()
for to in transport_orders:
    model.delivered.add(sum([model.x[w,to] for w in tours]) == 1)

#truck size constraints
model.weight = ConstraintList()
model.volume = ConstraintList()
model.length = ConstraintList()
for w in tours:
    model.weight.add(sum([model.x[w,to] * TO_list[to].weight for to in transport_orders]) <= b.max_payload)
    model.volume.add(sum([model.x[w,to] * TO_list[to].volume for to in transport_orders]) <= b.max_vol)
    model.length.add(sum([model.x[w,to] * TO_list[to].length for to in transport_orders]) <= b.max_length)
   
# All direct transports
model.direct_orig = ConstraintList()
model.direct_dest = ConstraintList()
for w in tours:
    model.direct_orig.add((0,len([model.x[w,to] * TO_list[to].origin for to in transport_orders]) <= 1))
    model.direct_orig.add((0,len([model.x[w,to] * TO_list[to].destination for to in transport_orders]),1))


# Objective

def cost_func(mdl):
    milkrun_list=[]
    for w in tours:
        to_add = []
        for to in transport_orders:
            if mdl.x[w,to] == 1:
                to_add.append(TO_list[to])
        if len(to_add) > 0:
            new_milkrun = Milkrun(to_add[0])
            for i in range(1,len(to_add)):
                new_milkrun.add_to(to_add[i])
            milkrun_list.append(new_milkrun)

    tot_cost = 0
    for milkrun in milkrun_list:
        tot_cost += milkrun.cost
    return tot_cost


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
    for to in transport_orders:
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