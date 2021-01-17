class Milkrun:
    def __init__(self, to):
        self.TOs_covered = [to]
        self.origins = {to.origin}
        self.destinations = {to.destination}
        self.type = "neither"

    def number_of_tos(self):
        return len(self.TOs_covered)

    def add_to(self, to):
        self.origins.push(to.origin)
        self.destinations.push(to.origin)
        if len(self.origins) > 1 and len(self.destinations) > 1:
            self.origins.pop()
            self.destinations.pop()
            return False
        if len(self.origins) > 1:
            self.type = "inbound"
        if len(self.destinations) > 1:
            self.type = "outbound"
        self.TOs_covered.append(to)

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
