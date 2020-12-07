from pandas import read_csv, to_numeric
from TransportOrder import Order

def getTOlist():
    """Reads Transport Orders from File, Instantiates and Order for each one, and returns a list of these Orders"""
    
    # Read in Transport Orders from File
    TOs = read_csv("./Data/TransportOrders.csv")

    # Clean out units and convert to numeric
    TOs['Weight'] = to_numeric(TOs['Weight'].str.rstrip(' kg').str.replace(',',''))
    TOs['Loading Meters'] = to_numeric(TOs['Loading Meters'].str.split(expand=True)[0])
    TOs['Volume'] = to_numeric(TOs['Volume'].str.split(expand=True)[0])

    # Create a list of Instances of the Order class
    TO_list = []
    for index, row in TOs.iterrows():
        TO_list.append(Order(row['Transport Order'], 
                            row['Origin Index'], 
                            row['Destination Index'], 
                            row['Weight'], 
                            row['Loading Meters'], 
                            row['Volume'])
                    )
    
    return TO_list