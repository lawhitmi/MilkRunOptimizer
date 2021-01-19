from numpy import inf


class Milkrun:
    def __init__(self, to):
        self.TOs_covered = [to]
        self.origins = {to.origin}
        self.destinations = {to.destination}
        self.type = "neither"
        self.cost = inf

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
