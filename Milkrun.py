from numpy import inf, array


class Milkrun:
    def __init__(self, to):
        self.TOs_covered = [to]
        self.origins = {to.origin}
        self.destinations = {to.destination}
        self.type = "neither"
        self.cost = inf
        self.dist_matrix = array([
            [0, 170, 210, 2219, 1444, 2428],  # Nuremberg
            [170, 0, 243, 2253, 1369, 2354],  # Munich
            [210, 243, 0, 2042, 1267, 2250],  # Stuttgart
            [2219, 2253, 2042, 0, 1127, 579],  # Supplier Porto
            [1444, 1369, 1267, 1127, 0, 996]  # Supplier Barcelona
        ])

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
            self.type = "neither"

    def get_dist(self):
        if len(self.origins)==1 and len(self.destinations)==1:
            return self.dist_matrix[next(iter(self.origins)),next(iter(self.destinations))]

    def __str__(self):
        if self.type == "neither":
            output = "fake milkrun \n Fusion of runs: "
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
