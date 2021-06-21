#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 11 17:18:03 2021

@author: jackreid
"""
# import ee
# import geemap
# import folium
# import gee_custom_utilities as gcu
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import numpy as np
import dateutil

with open('./Nightlights_Data/Rio_de_Janeiro/cities_median.pickle', 'rb') as f:
    nightlights = pickle.load(f)
    

mobility = pd.read_csv('./MobilityData/RioDeJaneiro/BR_Region_Mobility_Report_state.csv')
mobility_keys = list(mobility.keys())
keep_list = ['sub_region_1', 
             'sub_region_2',  
             'date',
             'retail_and_recreation_percent_change_from_baseline',
             'grocery_and_pharmacy_percent_change_from_baseline',
             'parks_percent_change_from_baseline',
             'transit_stations_percent_change_from_baseline',
             'workplaces_percent_change_from_baseline',
             'residential_percent_change_from_baseline']

drop_list = mobility_keys.copy()
for entry in keep_list:
    drop_list.remove(entry)
    
    
# for row in mobility.iterrows:
#     mobility
mobility.drop(drop_list, inplace=True, axis=1)
# mobility.replace(nan)
mobility['date'] = [dateutil.parser.parse(x) for x in mobility['date']]
mobility_state_average = mobility.loc[pd.isnull(mobility['sub_region_2'])]
mobility_cities =  mobility.loc[(pd.notnull(mobility['sub_region_2']))]
mobility_rio = mobility.loc[mobility['sub_region_2'] == 'Rio de Janeiro']


ax = nightlights.plot(x="system:time_start", y="Rio_de_Janeiro", label='Nightlights')
ax2 = mobility_rio.plot(x="date", y='residential_percent_change_from_baseline',label='Residential Mobility', secondary_y=True, ax=ax)

ax.set_ylabel('Nighlights')
ax2.set_ylabel('Mobility')

# fig,ax = plt.subplots()
# ax.set_xlabel("date")
# ax.set_ylabel("Relative Anomaly of Nightlights")
# ax.legend(loc='best')
plt.show()

