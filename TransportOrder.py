

# Transport Order Class
class Order():
    def __init__(self,order_num,origin,destination,weight,length,volume):
        self.order_num = order_num
        self.origin = origin
        self.destination = destination
        self.weight = weight
        self.length = length
        self.volume = volume