import pandas as pd
from helper_funcs import *
from MoT import MoT
from Milkrun import Milkrun
from pyomo.environ import *
import numpy as np

NUM_SUPPLIERS = 2

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

def createTO_df(TO_list):
    tos = pd.DataFrame({"transportOrder": [to.order_num for to in TO_list], "origin": [to.origin for to in TO_list],
                    "destination": [to.destination for to in TO_list], "weight": [to.weight for to in TO_list],
                    "length": [to.length for to in TO_list], "volume": [to.volume for to in TO_list], "milkrun": False, "considered": False})
    return tos

tos = createTO_df(TO_list)

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


print_results(milkrun_list,TO_list,'optBinPacking.csv')


def tryMilkruns(tos):
    milkrun_list = []
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
        index_to_use = 0 # this index is to allow the loop below to "skip" TOs that are incompatible.
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
                type_compatible = new_milkrun.add_to(find_to(to_add.iloc[index_to_use]['transportOrder']))
                if type_compatible:
                    tos.loc[tos["transportOrder"].str.match(to_add.iloc[index_to_use]['transportOrder']), "milkrun"] = True
                    tos.loc[tos["transportOrder"].str.match(to_add.iloc[index_to_use]['transportOrder']), "considered"] = True
                    index_to_use = 0
                else:
                    new_milkrun.pop()
                    index_to_use += 1
            else:
                if new_milkrun.type=="inbound":
                    milkrun_count = NUM_SUPPLIERS
                elif new_milkrun.type == "outbound" or new_milkrun.type=="direct": #direct is here to prevent the case where it tries to add a 3rd milkrun if an origin only has TOs with one destination option.
                    milkrun_count += 1
                break
    
    # Use Pyomo to load the remaining TOs on trucks (Bin Packing)
    for i in set(data['pickups_deliveries'][:,0]):
        for j in set(data['pickups_deliveries'][:,1]):
            to_list = tos.query('origin == ' + str(i) + 'and destination == ' + str(j) + 'and milkrun==False')
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
          
    return milkrun_list

# Attempt to combine runs with the most remaining margin in truck (Milkruns)
tours = pd.DataFrame({"Tour": [i for i in range(len(milkrun_list))], "origin": [next(iter(to.origins)) for to in milkrun_list],
                    "destination": [next(iter(to.destinations)) for to in milkrun_list], "weight": [i.total_weight() for i in milkrun_list],
                    "length": [i.total_length() for i in milkrun_list], "volume": [i.total_volume() for i in milkrun_list]})
tours['rem_weight'] = (b.max_payload - tours['weight'])/b.max_payload
tours['rem_vol'] = (b.max_vol - tours['volume'])/b.max_vol
tours['rem_len'] = (b.max_length - tours['length'])/b.max_length
tours['avg_rem'] = sum((tours['rem_weight'],tours['rem_vol'], tours['rem_len']))/3
tours = tours.sort_values(by=['avg_rem'],ascending=False)

new_to_list = []
to_remove = []
for i in tours[tours['avg_rem']>0.49].iterrows():
    new_to_list.append(milkrun_list[int(i[1]['Tour'])].TOs_covered)
    to_remove.append(int(i[1]['Tour']))
milkrun_list = [mr for i, mr in enumerate(milkrun_list) if i not in to_remove]
new_to_list = sum(new_to_list,[]) #hacky way to flatten the list of lists
new_tos = createTO_df(new_to_list)
new_tos = new_tos.sort_values(by=["weight"], ascending=False)
milkrun_list.append(tryMilkruns(new_tos))

# Attempt to join runs (note that there is no inbound/outbound check here)
# for i in range(len(milkrun_list)):
#     for j in range(len(milkrun_list)):
#         if j != i and milkrun_list[i]+milkrun_list[j]:
#             print('Joining: ',str(i), str(j))
#             for to in milkrun_list[i].TOs_covered:
#                 milkrun_list[j].add_to(to)
#             milkrun_list.pop(i)

#flatten milkrun_list
flat_list = []
for i in milkrun_list:
    if type(i) is list:
        for j in i:
            flat_list.append(j)
    else:
        flat_list.append(i)

print_results(flat_list,TO_list,'optBinPackingwMilkruns.csv')