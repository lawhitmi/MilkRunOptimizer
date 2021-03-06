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
model.x = Var(tours, transport_orders, domain=Binary)

# Constraints  

#truck size constraints
model.weight = ConstraintList()
model.volume = ConstraintList()
model.length = ConstraintList()
for w in tours:
    model.weight.add(sum([model.x[w,to] * TO_list[to].weight for to in transport_orders]) < b.max_payload)
    model.volume.add(sum([model.x[w,to] * TO_list[to].volume for to in transport_orders]) < b.max_vol)
    model.length.add(sum([model.x[w,to] * TO_list[to].length for to in transport_orders]) < b.max_length)
   

# Objective

def cost_func(mdl):
    milkrun_list=[]
    for w in tours:
        for to in transport_orders:
            if mdl.x[w,to] = 1:
                
    return cost


model.Cost = Objective(rule=cost_func, sense=minimize)



# Solve

instance = model.create_instance()
results = SolverFactory('glpk').solve(instance)
results.write()
instance.display()
instance.solutions.load_from(results)