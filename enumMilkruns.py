from helper_funcs import *
import numpy as np
from itertools import permutations

data = np.array([
    [0, 170, 210, 2219, 1444, 2428],  # Nuremberg
    [170, 0, 243, 2253, 1369, 2354],  # Munich
    [210, 243, 0, 2042, 1267, 2250],  # Stuttgart
    [2219, 2253, 2042, 0, 1127, 579],  # Supplier Porto
    [1444, 1369, 1267, 1127, 0, 996]  # Supplier Barcelona
])

suppliers = [3,4]
plants = [0,1,2]

# Build inbound possibilities (and choose best)
perm = permutations(suppliers)


# Build outbound possibilities
perm = permutations(plants)