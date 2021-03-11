from numpy import inf, array
from helper_funcs import *
from itertools import permutations
from MoT import MoT

LOC_NAME_LOOKUP = {0:'Nuremburg', 1: 'Munich', 2: 'Stuttgart', 3:'Supplier Porto', 4: 'Supplier Barcelona'}


class Milkrun:
    def __init__(self, to):
        self.TOs_covered = [to]
        self.origins = {to.origin}
        self.destinations = {to.destination}
        self.type = "direct"
        self.cost = inf
        self.dist_matrix = array([
            [0, 170, 210, 2219, 1444, 2428],  # Nuremberg
            [170, 0, 243, 2253, 1369, 2354],  # Munich
            [210, 243, 0, 2042, 1267, 2250],  # Stuttgart
            [2219, 2253, 2042, 0, 1127, 579],  # Supplier Porto
            [1444, 1369, 1267, 1127, 0, 996]  # Supplier Barcelona
        ])
        self.tariff_type = ""
        self.select_tariff()

    def number_of_tos(self):
        return len(self.TOs_covered)

    def add_to(self, to):
        self.origins.add(to.origin)
        self.destinations.add(to.destination)
        if len(self.origins) > 1 and len(self.destinations) > 1:
            self.origins.pop()
            self.destinations.pop()
            return False
        if len(self.origins) > 1:
            self.type = "inbound"
        if len(self.destinations) > 1:
            self.type = "outbound"
        self.TOs_covered.append(to)
        self.select_tariff()
        return True

    def total_weight(self):
        weight = 0
        for to in self.TOs_covered:
            weight += to.weight
        return weight

    def total_length(self):
        length = 0
        for to in self.TOs_covered:
            length += to.length
        return length

    def total_volume(self):
        volume = 0
        for to in self.TOs_covered:
            volume += to.volume
        return volume

    def pop(self):
        self.TOs_covered.pop()
        self.recalc_ods()

    def recalc_ods(self):
        self.origins = set()
        self.destinations = set()
        for to in self.TOs_covered:
            self.origins.add(to.origin)
            self.destinations.add(to.destination)
        if len(self.origins) > 1:
            self.type = "inbound"
        elif len(self.destinations) > 1:
            self.type = "outbound"
        else:
            self.type = "direct"
        self.select_tariff()

    def get_dist(self):
        """
        This method returns the distance between the origin and destination in the case of a direct route, otherwise it fully enumerates the 
        TSP and chooses the shortest distance. In all cases, the best route is set in the tour field.
        """
        if self.type == "direct":
            self.tour = LOC_NAME_LOOKUP[next(iter(self.origins))] + '->' + LOC_NAME_LOOKUP[next(iter(self.destinations))]
            return self.dist_matrix[next(iter(self.origins)),next(iter(self.destinations))]
        else:
            if self.type == "inbound":
                perm = permutations(self.origins)
                min_dist = 1E6
                best_route = ()
                for i in perm:
                    dist = self.dist_matrix[i[0],i[1]]+self.dist_matrix[i[1],next(iter(self.destinations))]
                    if dist < min_dist:
                        min_dist = dist
                        best_route = (i[0],i[1],next(iter(self.destinations)))
                self.tour = '->'.join([LOC_NAME_LOOKUP[x] for x in best_route])
                return min_dist
            elif self.type == "outbound":
                perm = permutations(self.destinations)
                min_dist = 1E6
                best_route = ()
                for i in perm:
                    dist = self.dist_matrix[next(iter(self.origins)),i[0]]
                    for j in range(len(i)-1):
                        dist += self.dist_matrix[i[j],i[j+1]]
                    if dist < min_dist:
                        min_dist = dist
                        best_route = tuple(i)
                self.tour = LOC_NAME_LOOKUP[next(iter(self.origins))] + '->' + '->'.join([LOC_NAME_LOOKUP[x] for x in best_route])
                return min_dist


    def select_tariff(self):
        if self.type == "direct":
            ftl_tariff = get_tariff_ftl_class(self)
            ltl1_tariff = get_tariff_class(self)
            ltl2_tariff = get_tariff_dist_class(self)
            min_tariff = min([ftl_tariff,ltl1_tariff,ltl2_tariff])
            if min_tariff == ltl1_tariff:
                self.cost = ltl1_tariff
                self.tariff_type = 'LTL1'
            elif min_tariff == ltl2_tariff:
                self.cost = ltl2_tariff
                self.tariff_type = 'LTL2'
            else:
                self.cost = ftl_tariff
                self.tariff_type = 'FTL'
        elif self.type == "inbound" or self.type == "outbound":
            milk_tariff = get_tariff_milk_class(self)
            self.cost = milk_tariff
            self.tariff_type = 'Milkrun'

    def __str__(self):
        if self.type == "direct":
            output = "Direct route \n Fusion of runs: "
        else:
            output = self.type + " milkrun \n covering: "
        for to in self.TOs_covered:
            output += to.order_num + " "
        output += "\n from: "
        for origin in self.origins:
            output += str(origin) + " "
        output += "\n to: "
        for destination in self.destinations:
            output += str(destination) + " "
        output += "\n cost: " + str(self.cost)
        return output

    def __add__(self,other):
        truck = MoT('MEGA', 70, 25000, 13.62, 2.48, 3)
        if self.total_weight() + other.total_weight() > truck.max_payload:
            return False
        elif self.total_volume() + other.total_volume() > truck.max_vol:
            return False
        elif self.total_length() + other.total_weight() > truck.max_length:
            return False
        elif self.origins != other.origins and self.destinations != other.destinations:
            return False
        else:
            return True