from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd
from helper_funcs import getTOlist


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    total_distance = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        total_distance += route_distance
    print('Total Distance of all routes: {}m'.format(total_distance))

def distance_callback(from_index, to_index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

def demand_callback(from_index):
    """Returns the demand of the node."""
    # Convert from routing variable Index to demands NodeIndex.
    from_node = manager.IndexToNode(from_index)
    return data['demands'][from_node]

TO_list = getTOlist()

data = {}
#Define Distance Matrix
# Note that a 6th location was added here as the 'depot' from which the trucks leave and return
data['distance_matrix'] = [
    [0,1700,2100,22190,14440,24280], #Nuremburg
    [1700,0,2430,22530,13690,23540], #Munich
    [2100,2430,0,20420,12670,22500], #Stuttgart
    [22190,22530,20420,0,11270,5790], #Supplier: Porto
    [14440,13690,12670,11270,0,9960], #Supplier: Barcelona
    [24280,23540,22500,5790,996,0]  #Depot: Seville
]

data['pickups_deliveries'] = []
for i in TO_list:
    data['pickups_deliveries'].append([i.origin,i.destination])

data['num_vehicles'] = 6
data['depot']=2 #set starting point for all vehicles
data['demands']= [45000,55000,100000,25000,30000,100]
data['vehicle_capacities']= [25000]*data['num_vehicles'] # length must match num_vehicles

manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

routing = pywrapcp.RoutingModel(manager)

transit_callback_index = routing.RegisterTransitCallback(distance_callback)

# This sets the cost of travel between any two locations (this is where our tariff information will
# eventually go)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
# NOTE: 
# You can also define multiple arc cost evaluators that depend on which 
# vehicle is traveling between locations, using the method routing.SetArcCostEvaluatorOfVehicle(). 
# For example, if the vehicles have different speeds, you could define the cost of travel between 
# locations to be the distance divided by the vehicle's speed—in other words, the travel time

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

routing.AddDimension(
    transit_callback_index,
    0,  # no slack
    10000,  # vehicle maximum travel distance
    True,  # start cumul to zero
    'Distance')

#routing.AddDimensionWithVehicleCapacity(
#    demand_callback_index,
#    0,  # null capacity slack
#    data['vehicle_capacities'],  # vehicle maximum capacities
#    True,  # start cumul to zero
#    'Capacity')

distance_dimension = routing.GetDimensionOrDie('Distance')
distance_dimension.SetGlobalSpanCostCoefficient(10000)

for request in data['pickups_deliveries']:
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        # Creates a pickup and delivery request
        routing.AddPickupAndDelivery(pickup_index, delivery_index)

        # Requirement that the item must be picked up and delivered by the same vehicle
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(
                delivery_index))
        
        # Requirement that item must be picked up before being delivered
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) <=
            distance_dimension.CumulVar(delivery_index))

        


search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)

solution = routing.SolveWithParameters(search_parameters)

if solution:
        print_solution(data, manager, routing, solution)