import pandas as pd
from TransportOrder import Order


def get_to_list():
    """Reads Transport Orders from File, Instantiates and Order for each one, and returns a list of these Orders"""

    # Read in Transport Orders from File
    tos = pd.read_csv("./Data/TransportOrders.csv")

    # Clean out units and convert to numeric
    tos['Weight'] = pd.to_numeric(tos['Weight'].str.rstrip(' kg').str.replace(',', ''))
    tos['Loading Meters'] = pd.to_numeric(tos['Loading Meters'].str.split(expand=True)[0])
    tos['Volume'] = pd.to_numeric(tos['Volume'].str.split(expand=True)[0])

    # Create a list of Instances of the Order class
    to_list = []
    for index, row in tos.iterrows():
        to_list.append(Order(row['Transport Order'],
                             row['Origin Index'],
                             row['Destination Index'],
                             row['Weight'],
                             row['Loading Meters'],
                             row['Volume'])
                       )

    return to_list

# LTL Tariff - no distance
def get_tariff(weight):
    tariff_levels = pd.Series({1.79: 0,
                               1.70: 201,
                               1.62: 501,
                               1.53: 1001,
                               1.46: 1501,
                               1.38: 2001,
                               1.32: 3001,
                               1.25: 4001,
                               1.19: 5001,
                               1.13: 7501,
                               1.07: 10001})
    cost = tariff_levels[tariff_levels <= weight].index[-1]

    tariff = cost * weight

    if tariff >= 250:
        return tariff
    else:
        return 250


# LTL Tariff - with distance
def get_tariff_dist(weight, dist):
    tariff_levels = pd.read_csv("./Data/LTLTariff.csv", index_col=0)
    tariff_levels.columns = tariff_levels.columns.astype(float)

    x = tariff_levels.columns[tariff_levels.columns <= dist][-1]
    y = tariff_levels.index[tariff_levels.index <= weight][-1]

    tariff = tariff_levels.loc[y, x]

    return tariff


# FTL Tariff
def get_tariff_ftl(dist):
    transport_cost = 50
    transport_time = 0  # will need to be updated if this comes into play
    distance_rate = 0.2  # Euro/km
    return transport_cost + (dist * distance_rate)


# Milk Run Tariff
def get_tariff_milk(dist, num_stops):
    transport_cost = 100
    transport_time = 0  # will need to be updated if this comes into play
    distance_rate = 0.6
    stop_cost = 40
    return transport_cost + distance_rate * dist + num_stops * stop_cost
