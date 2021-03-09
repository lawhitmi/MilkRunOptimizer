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

tos = pd.DataFrame({"transportOrder": [to.order_num for to in TO_list], "origin": [to.origin for to in TO_list],
                    "destination": [to.destination for to in TO_list], "weight": [to.weight for to in TO_list],
                    "length": [to.length for to in TO_list], "volume": [to.volume for to in TO_list]})

data['pickups_deliveries'] = []
for i in TO_list:
    data['pickups_deliveries'].append([i.origin, i.destination])

data['pickups_deliveries'] = np.array(data['pickups_deliveries'])

def bin_packing(TO_list, dist):
    model = ConcreteModel()

    # Sets
    tours = list(range(10)) # 20 is just a high estimate for # trucks required
    # transport_orders = list(range(len(TO_list)))
    model.transport_orders = RangeSet(0,len(TO_list)-1)


    # Variables
    model.x = Var(tours, model.transport_orders, domain=Binary, initialize=0)
    model.z = Var(tours, domain=Binary, initialize=0) #truck used?

    # Constraints  

    # TO must be assigned
    model.delivered = ConstraintList()
    for to in model.transport_orders:
        model.delivered.add(sum([model.x[w,to] for w in tours]) == 1)

    # truck size constraints
    model.weight = ConstraintList()
    model.volume = ConstraintList()
    model.length = ConstraintList()
    for w in tours:
        model.weight.add(sum([model.x[w,to] * TO_list.iloc[to]['weight'] for to in model.transport_orders]) <= b.max_payload)
        model.volume.add(sum([model.x[w,to] * TO_list.iloc[to]['volume'] for to in model.transport_orders]) <= b.max_vol)
        model.length.add(sum([model.x[w,to] * TO_list.iloc[to]['length'] for to in model.transport_orders]) <= b.max_length)
    
    # no TOs are allowed on a truck that isn't used
    model.used = ConstraintList()
    for w in tours:
        for to in model.transport_orders:
            model.used.add(model.x[w,to]<=model.z[w])

    # Objective

    # Cost function to minimize remaining space
    def cost_func(mdl):
        return sum([model.z[w] for w in tours])

    model.Cost = Objective(rule=cost_func, sense=minimize)

    # Solve

    instance = model.create_instance()
    results = SolverFactory('glpk').solve(instance)
    results.write()
    instance.display()
    instance.solutions.load_from(results)
    
    return instance

def find_to(to_name):
    """returns instance from TO_list which matches passed name"""
    for to in TO_list:
        if to.order_num == to_name:
            return to

def create_milkrun(to_add):
    new_milkrun = Milkrun(to_add[0])
    for i in range(1, len(to_add)):
        new_milkrun.add_to(to_add[i])

    return new_milkrun

milkrun_list = []
for i in set(data['pickups_deliveries'][:,0]):
    for j in set(data['pickups_deliveries'][:,1]):
        to_list = tos.query('origin == ' + str(i) + 'and destination == ' + str(j))
        dist = data['distance_matrix'][i,j]
        if len(to_list.index) > 0:
            result = bin_packing(to_list, dist)
            truck_to_matx = np.zeros((list(result.x.extract_values())[-1][0]+1,len(to_list)))
            # Convert sparse matrix to np.array
            for truck in result.x.extract_values():
                truck_to_matx[truck] = result.x.extract_values()[truck]
            
            for z in result.z.get_values():
                to_add = []
                if result.z.get_values()[z] > 0:
                    for to in range(len(truck_to_matx[z,:])):
                        if truck_to_matx[z,to] > 0:
                            to_add.append(find_to(to_list.iloc[to]['transportOrder']))
                    milkrun_list.append(create_milkrun(to_add))


print_results(milkrun_list,TO_list)


# Attempt to combine runs with the most remaining margin in truck (Milkruns)
tours = pd.DataFrame({"Tour": [i for i in range(len(milkrun_list))], "origin": [next(iter(to.origins)) for to in milkrun_list],
                    "destination": [next(iter(to.destinations)) for to in milkrun_list], "weight": [i.total_weight() for i in milkrun_list],
                    "length": [i.total_length() for i in milkrun_list], "volume": [i.total_volume() for i in milkrun_list]})
tours['rem_weight'] = (b.max_payload - tours['weight'])/b.max_payload
tours['rem_vol'] = (b.max_vol - tours['volume'])/b.max_vol
tours['rem_len'] = (b.max_length - tours['length'])/b.max_length
tours['avg_rem'] = sum((tours['rem_weight'],tours['rem_vol'], tours['rem_len']))/3
tours = tours.sort_values(by=['avg_rem'],ascending=False)

index0 = int(tours.iloc[0]['Tour'])
index1 = int(tours.iloc[1]['Tour'])
if milkrun_list[index0] + milkrun_list[index1]:
    for i in milkrun_list[index0].TOs_covered:
        milkrun_list[index1].add_to(i)
    milkrun_list.pop(index0)

print_results(milkrun_list,TO_list)