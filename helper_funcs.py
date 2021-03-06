import pandas as pd
from TransportOrder import Order

def print_results(milkrun_list,TO_list,filename):
    tot_cost = 0
    assigned_TOs = 0
    for milkrun in milkrun_list:
        tot_cost += milkrun.cost
        assigned_TOs += len(milkrun.TOs_covered)

    print('Total Cost: ', tot_cost)
    print("Assigned Transport Orders: "+ str(assigned_TOs) + '/' + str(len(TO_list)))

    results = []
    for i in milkrun_list:
        print(i.type, i.tour, i.tariff_type, round(i.cost,2), str([str(x) for x in i.TOs_covered]), round(i.total_weight(),2), round(i.total_volume(),2), round(i.total_length(),2))
        results.append([i.type, i.tour, i.tariff_type, round(i.cost,2), str([str(x) for x in i.TOs_covered]), round(i.total_weight(),2), round(i.total_volume(),2), round(i.total_length(),2)])
    
    res_df = pd.DataFrame(results, columns=['Type', 'Tour', 'Tariff Type', 'Cost', 'TOs', 'Tot Weight', 'Tot Vol', 'Tot Length'])
    res_df.to_csv(filename, index=False)



def get_to_list():
    """Reads Transport Orders from File, Instantiates an Order for each one, and returns a list of these Orders"""

    # Read in Transport Orders from File
    # Note that the weight for TO-IB-200015 was changed to 15,920 as the other value didn't fit on a truck 
    # and the density of the order was similar to that of a solid block of titanium.
    # A dummy order was also added originating out of Barcelona so that a second milkrun could be generated. (TO-0160050)
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

def get_tariff_class(milkrun):
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
    cost = tariff_levels[tariff_levels <= milkrun.total_weight()].index[-1]

    tariff = cost * milkrun.total_weight()
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

def get_tariff_dist_class(milkrun):
    tariff_levels = pd.read_csv("./Data/LTLTariff.csv", index_col=0)
    tariff_levels.columns = tariff_levels.columns.astype(float)

    x = tariff_levels.columns[tariff_levels.columns <= milkrun.get_dist()][-1]
    y = tariff_levels.index[tariff_levels.index <= milkrun.total_weight()][-1]

    tariff = tariff_levels.loc[y, x]

    return tariff

# FTL Tariff
def get_tariff_ftl(dist):
    speed = 70.0 # avg speed of MEGA truck
    transport_cost = 50
    time_rate = 2.0  
    distance_rate = 0.2  # Euro/km original value
    # distance_rate = 0.5
    return transport_cost + (dist * distance_rate) + time_rate * (dist/speed)

def get_tariff_ftl_class(milkrun):
    speed = 70.0 # avg speed of MEGA truck
    transport_cost = 50
    time_rate = 2.0
    distance_rate = 0.2 # original value
    # distance_rate = 0.5 #to make milkrun more viable
    return transport_cost + (milkrun.get_dist() * distance_rate) + (time_rate *(milkrun.get_dist()/speed))

# Milk Run Tariff
def get_tariff_milk(dist, num_stops):
    speed = 70.0 # avg speed of MEGA truck
    transport_cost = 100
    time_rate = 2.0
    distance_rate = 0.6
    stop_cost = 40
    return transport_cost + (distance_rate * dist) + (num_stops * stop_cost) + (time_rate * (dist/speed)) 

def get_tariff_milk_class(milkrun):
    speed = 70.0 # avg speed of MEGA truck
    transport_cost = 100 #original value
    # transport_cost = 50 #try lower value to make milkrun viable
    time_rate = 2.0
    distance_rate = 0.6 # original value
    # distance_rate = 0.2 #try lower value to make milkrun viable
    stop_cost = 40
    return transport_cost + (distance_rate * milkrun.get_dist()) + ((len(milkrun.origins)+len(milkrun.destinations)-2) * stop_cost) + (time_rate * (milkrun.get_dist()/speed))

# Running the script runs tests on the functions (using original values)
if __name__ == "__main__":
    assert round(get_tariff(800),0) == 1296
    assert round(get_tariff_dist(800,50),2) == 57.56
    assert round(get_tariff_ftl(250),0) == 100
    assert round(get_tariff_milk(250,2),0) == 330
