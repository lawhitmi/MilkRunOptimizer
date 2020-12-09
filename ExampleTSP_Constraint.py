import sys, os, math
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import matplotlib.pyplot as plt
import numpy as np
from six.moves import xrange
#from urllib3.connectionpool import xrange

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts


def main():
    cmd_opts = getopts(sys.argv)
    # configuration, problem description
    depot = 0
    num_vehicles = '--vehicles' in cmd_opts and int(cmd_opts['--vehicles']) or 10
    vehicle_capacity = '--capacity' in cmd_opts and int(cmd_opts['--capacity']) or 10
    speed = '--speed' in cmd_opts and int(cmd_opts['--speed']) or 40
    search_time_limit = '--search_time_limit' in cmd_opts and int(
        cmd_opts['--search_time_limit']) or 10 * 1000  # milliseconds
    trip_service_duration_max = 0
    max_dur_mult = '--max_dur_mult' in cmd_opts and float(cmd_opts['--max_dur_mult']) or 1.3
    glob_span_cost_coef = '--glob_span_cost_coef' in cmd_opts and int(cmd_opts['--glob_span_cost_coef']) or None
    plot = '--plot' in cmd_opts

    print(
    {
        'vehicles': num_vehicles,
        'capacity': vehicle_capacity,
        'speed': speed,
        'max_dur_mult': max_dur_mult,
        'glob_span_cost_coef': glob_span_cost_coef,
    })

    customers = []
    locations = []
    demands = []
    start_times = []
    end_times = []
    pickups = []
    dropoffs = []
    data = [
        # customer  lat         lng  demand  start end pickup_index dropoff_index
        [-1, 37.477749, -122.148499, 0, -1, -1, 0, 0],
        [1, 37.467112, -122.253060, 1, 487, 2287, 0, 2],
        [1, 37.477995, -122.148442, -1, 2623, 4423, 1, 0],
        [2, 37.444040, -122.214423, 1, 678, 2478, 0, 4],
        [2, 37.478331, -122.149008, -1, 2623, 4423, 3, 0],
        [3, 37.455956, -122.285887, 1, 23, 1823, 0, 6],
        [3, 37.478002, -122.148850, -1, 2623, 4423, 5, 0],
        [4, 37.452259, -122.240702, 1, 537, 2337, 0, 8],
        [4, 37.481572, -122.152584, -1, 2623, 4423, 7, 0],
        [5, 37.447776, -122.257816, 1, 0, 1800, 0, 10],
        [5, 37.485104, -122.147462, -1, 2623, 4423, 9, 0],
        [6, 37.473287, -122.271279, 1, 704, 2504, 0, 12],
        [6, 37.480284, -122.167614, -1, 2623, 4423, 11, 0],
        [7, 37.558294, -122.263208, 1, 823, 2610, 0, 14],
        [7, 37.481087, -122.166956, -1, 2640, 4423, 13, 0],
        [8, 37.558294, -122.263208, 1, 0, 1800, 0, 16],
        [8, 37.481087, -122.166956, -1, 2623, 4423, 15, 0],
    ]
    for i in range(0, len(data)):
        row = data[i]
        customers.append(row[0])
        locations.append([row[1], row[2]])
        demands.append(row[3])
        start_times.append(row[4])
        end_times.append(row[5])
        pickups.append(row[6])
        dropoffs.append(row[7])

    # build model
    num_locations = len(locations)
    #model_parameters = pywrapcp.RoutingModel.DefaultModelParameters()
    model_parameters = pywrapcp.DefaultRoutingModelParameters()
    # print model_parameters
    manager = pywrapcp.RoutingIndexManager(num_locations,num_vehicles,depot)

    routing = pywrapcp.RoutingModel(manager,model_parameters)
    #routing = pywrapcp.RoutingModel(num_locations, num_vehicles, depot, model_parameters)

    #search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.seconds = search_time_limit
    search_parameters.log_search = True

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
    # print search_parameters

    #time_between_locations = CreateCustomTimeCallback(locations, speed)
    time_between_locations = CreateCustomTimeCallback(manager, locations,speed)

    arc_cost_callback = time_between_locations.Duration
    arc_cost_callback1 = routing.RegisterTransitCallback(arc_cost_callback)
    #arc_cost_callback = routing.RegisterTransitCallback(time_between_locations.Duration)

    routing.SetArcCostEvaluatorOfAllVehicles(arc_cost_callback1)

    demands_at_locations = CreateDemandCallback(manager, demands)
    demands_callback = demands_at_locations.Demand
    demands_callback1 = routing.RegisterUnaryTransitCallback(demands_callback)

    routing.AddDimension(demands_callback1, 0, vehicle_capacity, True, "Capacity")

    # time taken to load/unload at each location
    service_times = CreateServiceTimeCallback(manager, demands, trip_service_duration_max)
    service_time_callback = service_times.ServiceTime
    # time taken to travel between locations
    travel_time_callback = time_between_locations.Duration

    total_times = CreateTotalTimeCallback(service_time_callback, travel_time_callback)
    total_time_callback = total_times.TotalTime
    total_time_callback1 = routing.RegisterTransitCallback(total_time_callback)

    horizon = max(end_times) + 7600  # buffer beyond latest dropoff
    routing.AddDimension(total_time_callback1, horizon, horizon, False, "Time")

    # build pickup and delivery model
    time_dimension = routing.GetDimensionOrDie("Time")
    if glob_span_cost_coef:
        time_dimension.SetGlobalSpanCostCoefficient(glob_span_cost_coef)

    solver = routing.solver()
    for i in range(1, num_locations):
        #index = routing.IndexToNode(i)
        index = manager.NodeToIndex(i)

        time_dimension.CumulVar(i).SetRange(start_times[i], end_times[i])

        if demands[i] != depot and pickups[i] == 0 and dropoffs[i] != 0:  # don't setup precedence for depots
            #delivery_index = routing.IndexToNode(dropoffs[i])
            delivery_index = manager.NodeToIndex(dropoffs[i])
            if delivery_index > 0:
                solver.Add(routing.VehicleVar(index) == routing.VehicleVar(delivery_index))
                solver.Add(time_dimension.CumulVar(index) <= time_dimension.CumulVar(delivery_index))
                min_dur = int(travel_time_callback(index, delivery_index))
                max_dur = int(max_dur_mult * min_dur)
                dur_expr = time_dimension.CumulVar(delivery_index) - time_dimension.CumulVar(index)
                solver.Add(dur_expr <= max_dur)
                routing.AddPickupAndDelivery(i, dropoffs[i])

    if plot:
        plt.barh(customers, np.array(end_times) - np.array(start_times), left=start_times)
        plt.yticks(customers)
        plt.xlabel('pickup start,end .. dropoff start,end')
        plt.ylabel('customers')
        plt.show()

    print('begin solving')
    assignment = routing.SolveWithParameters(search_parameters)
    if assignment:
        print('solution exists')
        printer = ConsolePrinter(num_vehicles, customers, demands, start_times,
                                 end_times, pickups, dropoffs, travel_time_callback,
                                 max_dur_mult, routing, assignment)
        printer.print_solution()
    else:
        print('solution not found')


class ConsolePrinter():
    def __init__(self, num_vehicles, customers, demands, start_times, end_times,
                 pickups, dropoffs, calc_travel_time, max_dur_mult, routing, assignment):
        self.num_vehicles = num_vehicles
        self.customers = customers
        self.demands = demands
        self.start_times = start_times
        self.end_times = end_times
        self.pickups = pickups
        self.dropoffs = dropoffs
        self.calc_travel_time = calc_travel_time
        self.max_dur_mult = max_dur_mult
        self.routing = routing
        self.assignment = assignment

    def print_solution(self):
        print("Total duration of all routes: " + str(self.assignment.ObjectiveValue()) + "\n")
        capacity_dimension = self.routing.GetDimensionOrDie("Capacity")
        time_dimension = self.routing.GetDimensionOrDie("Time")

        errors = None
        plan_output = ''
        rides = {}
        for vehicle_nbr in range(self.num_vehicles):
            veh_output = ''
            index = self.routing.Start(vehicle_nbr)

            empty = True
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                customer = self.customers[node_index]
                demand = self.demands[node_index]
                load_var = capacity_dimension.CumulVar(index)
                time_var = time_dimension.CumulVar(index)

                visit = Visit(vehicle_nbr, node_index, customer, demand,
                              self.assignment.Value(load_var),
                              self.assignment.Min(time_var),
                              self.assignment.Max(time_var),
                              self.assignment.Value(time_var))
                ride = rides.get(customer)
                if not ride:
                    ride = rides[customer] = Ride(customer, vehicle_nbr)
                if visit.is_pickup():
                    ride.pickup_visit = visit
                else:
                    ride.dropoff_visit = visit

                veh_output += \
                    "{route_id} {node_index} {customer} {demand} {load} {tmin} {tmax} {tval}".format(
                        route_id=vehicle_nbr,
                        node_index=node_index,
                        customer=customer,
                        demand=demand,
                        load=self.assignment.Value(load_var),
                        tmin=self.assignment.Min(time_var),
                        tmax=self.assignment.Max(time_var),
                        tval=self.assignment.Value(time_var))
                if self.assignment.Value(load_var) > 0:
                    empty = False
                veh_output += "\n"
                index = self.assignment.Value(self.routing.NextVar(index))

            node_index = self.manager.IndexToNode(index)
            customer = self.customers[node_index]
            demand = self.demands[node_index]
            load_var = capacity_dimension.CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            visit = Visit(vehicle_nbr, node_index, customer, demand,
                          self.assignment.Value(load_var),
                          self.assignment.Min(time_var),
                          self.assignment.Max(time_var),
                          self.assignment.Value(time_var))
            veh_output += \
                "{route_id} {node_index} {customer} {demand} {load} {tmin} {tmax} {tval}".format(
                    route_id=vehicle_nbr,
                    node_index=node_index,
                    customer=customer,
                    demand=demand,
                    load=self.assignment.Value(load_var),
                    tmin=self.assignment.Min(time_var),
                    tmax=self.assignment.Max(time_var),
                    tval=self.assignment.Value(time_var))
            veh_output += "\n"
            if not empty:
                plan_output += veh_output
        print("route_id node_index customer demand load tmin tmax tval")
        print(plan_output)

        ride_list = rides.values()
        cols = ['cust (pnode..dnode)', 'route',
                'pickup_at..dropoff_at',
                'cnstr_pickup', 'cnstr_dropoff',
                'plan_dur',
                'cnstr_dur',
                'plan_pickup_range',
                'plan_dropoff_range',
                'plan_min_poss_dur']
        row_format = "".join(map(lambda c: "{:>" + str(len(c) + 4) + "}", cols))
        print(row_format.format(*cols))
        for i in range(0, len(ride_list)):
            ride = ride_list[i]
            if not ride.pickup_visit:
                continue
            min_dur = self.calc_travel_time(ride.pickup_visit.node_index, ride.dropoff_visit.node_index)
            vals = ["{} {}..{}".format(ride.customer, ride.pickup_visit.node_index, ride.dropoff_visit.node_index),
                    ride.route,
                    "{}..{}".format(ride.pickup_visit.tval, ride.dropoff_visit.tval),
                    "{}..{}".format(time_dimension.CumulVar(ride.pickup_visit.node_index).Min(),
                                    time_dimension.CumulVar(ride.pickup_visit.node_index).Max()),
                    "{}..{}".format(time_dimension.CumulVar(ride.dropoff_visit.node_index).Min(),
                                    time_dimension.CumulVar(ride.dropoff_visit.node_index).Max()),
                    ride.dropoff_visit.tval - ride.pickup_visit.tval,
                    "{}..{}".format(int(min_dur), int(self.max_dur_mult * min_dur)),
                    "{}..{}".format(ride.pickup_visit.tmin, ride.pickup_visit.tmax),
                    "{}..{}".format(ride.dropoff_visit.tmin, ride.dropoff_visit.tmax),
                    ride.dropoff_visit.tmin - ride.pickup_visit.tmax
                    ]
            print(row_format.format(*vals))


class Ride(object):
    def __init__(self, customer, route):
        self.customer = customer
        self.route = route
        self.pickup_visit = None
        self.dropoff_visit = None


class Visit(object):
    def __init__(self, route_id, node_index, customer, demand, load, tmin, tmax, tval):
        self.route_id = route_id
        self.node_index = node_index
        self.customer = customer
        self.demand = demand
        self.load = load
        self.tmin = tmin
        self.tmax = tmax
        self.tval = tval

    def is_pickup(self):
        return self.demand > 0


# Custom travel time callback
class CreateCustomTimeCallback(object):
    def __init__(self, manager, locations, speed):
        self.manager = manager
        self.locations = locations
        self.speed = speed
        self._durations = {}
        num_locations = len(self.locations)

        # precompute distance between location to have distance callback in O(1)
        for from_node in xrange(num_locations):
            self._durations[from_node] = {}
            for to_node in xrange(num_locations):
                if from_node == to_node:
                    self._durations[from_node][to_node] = 0
                else:
                    loc1 = self.locations[from_node]
                    loc2 = self.locations[to_node]
                    dist = self.distance(loc1[0], loc1[1], loc2[0], loc2[1])
                    dur = self._durations[from_node][to_node] = (3600 * dist) / self.speed
                    # print "{} {} {}".format(from_node, to_node, dur)

    def Duration(self, from_index, to_index):
        from_node = self.manager.IndexToNode(from_index)
        to_node = self.manager.IndexToNode(to_index)
        return self._durations[from_node][to_node]

    #def Duration(self, manager,from_node, to_node):


        #return self._durations[manager.NodeToIndex(from_node)][manager.NodeToIndex(to_node)]

    def distance(self, lat1, long1, lat2, long2):
        # Note: The formula used in this function is not exact, as it assumes
        # the Earth is a perfect sphere.

        # Mean radius of Earth in miles
        radius_earth = 3959

        # Convert latitude and longitude to
        # spherical coordinates in radians.
        degrees_to_radians = math.pi / 180.0
        phi1 = lat1 * degrees_to_radians
        phi2 = lat2 * degrees_to_radians
        lambda1 = long1 * degrees_to_radians
        lambda2 = long2 * degrees_to_radians
        dphi = phi2 - phi1
        dlambda = lambda2 - lambda1

        a = self.haversine(dphi) + math.cos(phi1) * math.cos(phi2) * self.haversine(dlambda)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius_earth * c
        return d



    def haversine(self, angle):
        h = math.sin(angle / 2) ** 2
        return h


class CreateDemandCallback(object):
    def __init__(self, manager, demands):
        self.manager = manager
        self.matrix = demands

    def Demand(self, from_index):
        from_node = self.manager.IndexToNode(from_index)
        return self.matrix[from_node]


class CreateServiceTimeCallback(object):
    def __init__(self, manager, demands=None, max_service_time=0):
        self.manager = manager
        self.matrix = demands
        self.max_service_time = max_service_time

    def ServiceTime(self, from_index):
        from_node = self.manager.IndexToNode(from_index)
        if self.matrix is None:
            return self.max_service_time
        else:
            return self.matrix[from_node]


class CreateTotalTimeCallback(object):
    """Create callback to get total times between locations."""
    def __init__(self, service_time_callback, travel_time_callback):
        self.service_time_callback = service_time_callback
        self.travel_time_callback = travel_time_callback

    def TotalTime(self, from_index, to_index):
        service_time = self.service_time_callback(from_index)
        travel_time = self.travel_time_callback(from_index, to_index)
        return service_time + travel_time


if __name__ == '__main__':
    main()