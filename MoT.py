class MoT:
    def __init__(self, name, avg_speed, payload, length, width, height):
        self.name = name
        self.avg_speed = avg_speed
        self.max_payload = payload
        self.max_length = length
        self.max_width = width
        self.max_height = height
        self.rem_length = length
        self.rem_width = width
        self.rem_height = height
        self.rem_payload = payload
        self.max_vol = length * width * height
        self.TOs_loaded = []

    def load_truck(self, TO):
        if self._check_fits():
            pass
        pass

    def unload_truck(self, TO):
        pass

    def empty_truck(self, TO):
        pass

    def _check_fits(self, TO):
        fits = True
        pass
