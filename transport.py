# This is the first attempt using Pyomo to solve the problem

from pyomo.environ import *
import pandas as pd
from helper_funcs import getTOlist

data={}

data['distance_matrix'] = [
    [0,170,210,2219,1444,2428], # Nuremburg
    [170,0,243,2253,1369,2354], # Munich
    [210,243,0,2042,1267,2250], # Stuttgart
    [2219,2253,2042,0,1127,579], # Supplier Porto
    [1444,1369,1267,1127,0,996], # Supplier Barcelona
    [2428,2354,2250,579,996,0] # Depot Seville (this may not be needed)
]


TO_list = getTOlist()

data['pickups_deliveries'] = []
for i in TO_list:
    data['pickups_deliveries'].append([i.origin,i.destination])

data['no_vehicles'] = 5

model = ConcreteModel()

# Sets
places = list(range(len(data['distance_matrix'])))
vehicles = list(range(data['no_vehicles']))


# Variables
model.x = Var(
        places, places, vehicles,
        within=Binary,
        doc="1 if route from i-th to j-th place taken by k-th vehicle, 0 otherwise"
    )

# Constraints


# Objective

def cost_func(mdl):
    dist = 0
    for i in places:
        for j in places:
            if j != i:
                for k in vehicles:
                    if mdl.x[i,j,k] == 1:
                        dist+=data['distance_matrix'][i][j]
    return dist

model.Cost = Objective(rule=cost_func, sense=minimize)

# Solve

results = SolverFactory('glpk').solve(model)
results.write()

# Constraints

# Demand = {
#    'Lon':   125,        # London
#    'Ber':   175,        # Berlin
#    'Maa':   225,        # Maastricht
#    'Ams':   250,        # Amsterdam
#    'Utr':   225,        # Utrecht
#    'Hag':   200         # The Hague
# }

# Supply = {
#    'Arn':   600,        # Arnhem
#    'Gou':   650         # Gouda
# }

# T = {
#     ('Lon','Arn'): 1000,
#     ('Lon','Gou'): 2.5,
#     ('Ber','Arn'): 2.5,
#     ('Ber','Gou'): 1000,
#     ('Maa','Arn'): 1.6,
#     ('Maa','Gou'): 2.0,
#     ('Ams','Arn'): 1.4,
#     ('Ams','Gou'): 1.0,
#     ('Utr','Arn'): 0.8,
#     ('Utr','Gou'): 1.0,
#     ('Hag','Arn'): 1.4,
#     ('Hag','Gou'): 0.8
# }

# # Step 0: Create an instance of the model
# model = ConcreteModel()
# model.dual = Suffix(direction=Suffix.IMPORT)

# # Step 1: Define index sets
# CUS = list(Demand.keys())
# SRC = list(Supply.keys())

# # Step 2: Define the decision 
# model.x = Var(CUS, SRC, domain = NonNegativeReals)

# # Step 3: Define Objective
# model.Cost = Objective(
#     expr = sum([T[c,s]*model.x[c,s] for c in CUS for s in SRC]),
#     sense = minimize)

# # Step 4: Constraints
# model.src = ConstraintList()
# for s in SRC:
#     model.src.add(sum([model.x[c,s] for c in CUS]) <= Supply[s])
        
# model.dmd = ConstraintList()
# for c in CUS:
#     model.dmd.add(sum([model.x[c,s] for s in SRC]) == Demand[c])
    
# results = SolverFactory('glpk').solve(model)
# results.write()


# for c in CUS:
#     for s in SRC:
#         print(c, s, model.x[c,s]())

# if 'ok' == str(results.Solver.status):
#     print("Total Shipping Costs = ",model.Cost())
#     print("\nShipping Table:")
#     for s in SRC:
#         for c in CUS:
#             if model.x[c,s]() > 0:
#                 print("Ship from ", s," to ", c, ":", model.x[c,s]())
# else:
#     print("No Valid Solution Found")