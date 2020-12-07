from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd

# Transport Order Class
class Order():
    def __init__(self,order_num,origin,destination,weight,length,volume):
        self.order_num = order_num
        self.origin = origin
        self.destination = destination
        self.weight = weight
        self.length = length
        self.volume = volume

def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print('Objective: {} miles'.format(solution.ObjectiveValue()))
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    print(plan_output)
    plan_output += 'Route distance: {}miles\n'.format(route_distance)
    
def distance_callback(from_index, to_index):
    """Returns the distance between the two nodes."""
    # Convert from routing variable Index to distance matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data['distance_matrix'][from_node][to_node]


def get_routes(solution, routing, manager):
    routes = []
    for route_nbr in range(routing.vehicles()):
        
        index = routing.Start(route_nbr)
        route = [manager.IndexToNode(index)]
        
        while not routing.IsEnd(index):
            
            index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
        
        routes.append(route)
    return routes


TOs = pd.read_csv("./Data/TransportOrders.csv")

TOs['Weight'] = pd.to_numeric(TOs['Weight'].str.rstrip(' kg').str.replace(',',''))
TOs['Loading Meters'] = pd.to_numeric(TOs['Loading Meters'].str.split(expand=True)[0])
TOs['Volume'] = pd.to_numeric(TOs['Volume'].str.split(expand=True)[0])

TO_list = []
for index, row in TOs.iterrows():
    TO_list.append(Order(row['Transport Order'], 
                         row['Origin Index'], 
                         row['Destination Index'], 
                         row['Weight'], 
                         row['Loading Meters'], 
                         row['Volume'])
                  )
    
""""Stores the data for the problem."""
data = {}

data['distance_matrix'] = [
    [0,170,210,2219,1444],
    [170,0,243,2253,1369],
    [210,243,0,2042,1267],
    [2219,2253,2042,0,1127],
    [1444,1369,1267,1127,0]
]

data['num_vehicles'] = 43

data['depot'] = 0

#data['starts'] = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3, 3]
#data['ends'] =   [1, 0, 0, 2, 2, 0, 0, 1, 2, 0, 2, 0, 0, 1, 1, 1, 1, 1, 1, 0, 2, 2, 2, 2, 0, 0, 2, 2, 1, 0, 0, 2, 2, 2, 0, 0, 2, 2, 0, 2, 0, 1, 1]

data['starts'] = []
data['ends'] = []
for i in TO_list:
    data['starts'].append(i.origin)
    data['ends'].append(i.destination)


manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['starts'],
                                           data['ends'])


routing = pywrapcp.RoutingModel(manager)


transit_callback_index = routing.RegisterTransitCallback(distance_callback)

routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

solution = routing.SolveWithParameters(search_parameters)
if solution:
    print_solution(manager, routing, solution)

    
routes = get_routes(solution, routing, manager)
# Display the routes.
for i, route in enumerate(routes):
    print('Route', i, route)

