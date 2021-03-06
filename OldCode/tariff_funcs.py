import pandas as pd

# LTL Tariff - no distance
def get_tariff(weight):
    tariff_levels = pd.Series({1.79:0,
                    1.70:201,
                    1.62:501,
                    1.53:1001,
                    1.46:1501,
                    1.38:2001,
                    1.32:3001,
                    1.25:4001,
                    1.19:5001,
                    1.13:7501,
                    1.07:10001})
    cost=tariff_levels[tariff_levels<=weight].index[-1]
    
    tariff = cost*weight
    
    if tariff>=250:
        return tariff
    else: 
        return 250

# LTL Tariff - with distance
def get_tariff_dist(weight,dist):
    tariff_levels = pd.read_csv("./Data/LTLTariff.csv",index_col=0)
    tariff_levels.columns = tariff_levels.columns.astype(float)
    
    x=tariff_levels.columns[tariff_levels.columns <= dist][-1]
    y=tariff_levels.index[tariff_levels.index <= weight][-1]
    
    tariff = tariff_levels.loc[y,x]   
    
    
    return tariff


# FTL Tariff
def get_tariff_ftl(dist):
    transport_cost = 50
    transport_time = 0 #will need to be updated if this comes into play
    distance_rate = 1.4 # Euro/km
    return transport_cost+(dist*distance_rate)


# Milk Run Tariff
def get_tariff_milk(dist, num_stops):
    transport_cost = 100
    transport_time = 0 #will need to be updated if this comes into play
    distance_rate = 0.6
    stop_cost = 40
    return transport_cost + distance_rate*dist + num_stops*stop_cost

# Running the script runs tests on the functions
if __name__ == "__main__":
    assert round(get_tariff(800),0) == 1296
    assert round(get_tariff_dist(800,50),2) == 57.56
    assert round(get_tariff_ftl(250),0) == 400
    assert round(get_tariff_milk(250,2),0) == 330