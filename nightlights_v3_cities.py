#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 10:42:17 2021

@author: jackreid
"""

import ee
import geemap
import folium
import gee_custom_utilities as gcu
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import numpy as np


#%% 1 - SELECT AREAS OF INTEREST
print('1 - SELECT AREAS OF INTEREST')
aoi =     ee.Geometry.Polygon(
                [[[-44.96879073675279, -20.600786671961583],
                  [-44.96879073675279, -23.502425722766645],
                  [-40.75004073675279, -23.502425722766645],
                  [-40.75004073675279, -20.600786671961583]]])


FeatureID = 'nome'
Cities = geemap.shp_to_ee('./Shapefiles/State/hc979qh6228_gcs_Underscores.shp', encoding="ISO-8859-1")
region_list = ee.List(ee.Dictionary(Cities.aggregate_histogram(FeatureID)).keys())



def collapse_features(name):
    # name = ee.Feature(feat.get(FeatureID))
    filtered_feats = Cities.filterMetadata(FeatureID, 'equals', name)
    return ee.Feature(ee.Algorithms.If(filtered_feats.size().eq(1),
                                filtered_feats.first(),
                               filtered_feats.union().first().set(FeatureID, name)))


Cities_simple = ee.FeatureCollection(region_list.map(collapse_features))


#%% 2 - DRAW SELECTED AREAS ON MAP
print('2 - DRAW SELECTED AREAS ON MAP')

empty = ee.Image().byte() #Create an empty image into which to paint the features, cast to byte.
outline = empty.paint(featureCollection = Cities,  #featureCollection
                      color = 1,                #color
                      width = 2                 #width
                      )

#%% 3 - PROCESSING FUNCTIONS
print('3 - PROCESSING FUNCTIONS')

def DNBA2_Processing(img):
  
    # Clip to area of interest and mask for water
    img = img.clip(aoi)
    cloudband = img.select('b6')
    qualityMask = (cloudband.bitwiseAnd(0).eq(0) #include day images
                .And(cloudband.bitwiseAnd(128).eq(0)) #include cloud
                .And(cloudband.bitwiseAnd(4).eq(0))) #include water
    newMask = qualityMask
    img = img.mask(newMask)
    output = img.select('b3')          #add computed indices to bands
  
    return output

def AnomalyCalc(imgcol, refstart, refend, obstart, obend):
    
    # Reference Image Collection
    reference = (imgcol.filterDate(refstart, refend)
                        .sort('system:time_start', True))  # Sort chronologically in descending order.
  
    # Compute the median for the Reference Period.
    Refmedian = reference.median()
    
    # Compute relative anomalies by subtracting the REFERENCE MEDIAN from each image in the OBSERVATION PERIOD
    
    def anom_rel(img):
        return (img.subtract(Refmedian).divide(Refmedian)
                .set('system:time_start', img.get('system:time_start')))  # Copy the date properties over to the new collection.
    
    observation = imgcol.filterDate(obstart,obend).map(anom_rel)
    return observation

def AnomalyMeanCalc(imgcol, refstart, refend, obstart, obend):

    # Reference Image Collection
    reference = (imgcol.filterDate(refstart, refend)
                  .sort('system:time_start', True)) # Sort chronologically in descending order.

    # Compute the median for the Reference Period.
    Refmedian = reference.mean()
    
    # Compute anomalies by subtracting the REFERENCE MEDIAN from each image in the OBSERVATION PERIOD
    def anom(img):
        return (img.subtract(Refmedian)
                .set('system:time_start', img.get('system:time_start')))  # Copy the date properties over to the new collection.
    
    observation = imgcol.filterDate(obstart,obend).map(anom)
 
    # Sum of the observations
    anomaly = observation.sum()
    # Determine the number of good images for each pixel
    numimages = observation.count()
    # Divide the sum by the number of images to correct for number of images in collection
    anomalyMean = anomaly.divide(numimages)
  
    return anomalyMean

#%% 4 - RUN PROCESSING
print('4 - RUN PROCESSING')

DNB_a2 = ee.ImageCollection('users/jackreid/nightlights/rio_state_nightlights_2019_01_to_2021_05')
DNB_processed = DNB_a2.map(DNBA2_Processing)

# #REDUCE DATA TO WEEKLY AVERAGES
startDate = ee.Date('2019-01-01')
endDate = ee.Date('2021-05-01')

dayOffsets = ee.List.sequence(
                          0, 
                          endDate.difference(startDate, 'days').subtract(1),
                          7 # Single day every week
                          )

def weekCalc(dayOffset):
    start = startDate.advance(dayOffset, 'days')
    end = start.advance(1, 'week')
    year = start.get('year')
    dayOfYear = start.getRelative('day', 'year')
    return (DNB_processed
      .filterDate(start, end)
      .mean()
      .set('year', year)
      .set('day_of_year', dayOfYear)
      .set('system:time_start', ee.Date(start).millis()))

weeklyMeans = ee.ImageCollection.fromImages(dayOffsets.map(weekCalc)) 

#DEFINE THE REFERENCE PERIOD
ref_start = '2019-01-01'
ref_end =  '2020-03-01'

#DEFINE THE OBSERVATION PERIOD
observation_start = '2019-01-01'
observation_end =  '2021-05-01'


#CALCULATE THE RELATIVE ANOMALY
DNB_Anomaly = AnomalyCalc(weeklyMeans, ref_start, ref_end, observation_start, observation_end)

#CALCULATE THE MEAN ANOMALY
DNB_MeanAnomaly = AnomalyMeanCalc(weeklyMeans.select('b3'), ref_start, ref_end, observation_start, observation_end)

#%% 5 - CALCULATE THE THEIL-SEN ESTIMATOR FOR POST-PANDEMIC PERIOD
print('5 - CALCULATE THE THEIL-SEN ESTIMATOR FOR POST-PANDEMIC PERIOD')

pandemic_start = '2020-03-01'
pandemic_end =  '2020-08-30'
postPandemicWeeklyMeans = weeklyMeans.filterDate(pandemic_start, pandemic_end)


afterFilter = ee.Filter.lessThan(
    leftField = 'system:time_start',
    rightField = 'system:time_start'
    )

joined = ee.ImageCollection(ee.Join.saveAll('after').apply(
    primary = postPandemicWeeklyMeans,
    secondary = postPandemicWeeklyMeans,
    condition = afterFilter
    ))

def slope_nested(after, current):
   
    def slope(i, j): # i and j are images
        return (ee.Image(j).subtract(i)
          .divide(ee.Image(j).date().difference(ee.Image(i).date(), 'days'))
          .rename('slope')
          .float())
    def slope_images(image):
        return ee.Image(slope(current, image))
    
    return after.map(slope_images)

def slope_after(current):
    afterCollection = ee.ImageCollection.fromImages(current.get('after'))
    current = current
    return slope_nested(afterCollection, current)

slopes = ee.ImageCollection(joined.map(slope_after).flatten())

sensSlope = slopes.reduce(ee.Reducer.median(), 2) # Set parallelScale.



#%% 6 - GENERATE MAPS
print('6 - GENERATE MAPS')

folium.Map.add_ee_layer = gcu.add_ee_layer

zoom = 10

# Create a folium map object.
center = aoi.centroid(10).coordinates().reverse().getInfo()
m = folium.Map(location=center, zoom_start=zoom)

# Add layers to the folium map.



NightlightsVisParams = {"opacity":1,
                        "bands":["b3"],
                        "min":-1000,
                        "max":1000,
                        "gamma":1}
m.add_ee_layer(weeklyMeans.first(),
                NightlightsVisParams,
                'Nightlights Processed First', True, 1, 9)

TSVisParams = {"opacity":1,
                "bands":["slope_median"],
                "min":-2,
                "max":2,
                "palette":["440154",
                          "481567",
                          "482677",
                          "453781",
                          "404788",
                          "39568c",
                          "33638d",
                          "2d708e",
                          "287d8e",
                          "238a8d",
                          "1f968b",
                          "20a387",
                          "29af7f",
                          "3cbb75",
                          "55c667",
                          "73d055",
                          "95d840",
                          "b8de29",
                          "dce319",
                          "fde725"]}
m.add_ee_layer(sensSlope,
                TSVisParams,
                'Nightlights TS Estimator', True, 1, 9)

BairrosVisParams = {"opacity":1,
                        'palette': 'd62ccd'}
m.add_ee_layer(outline,
                BairrosVisParams,
                'edges', True, 1, 9)


# Add a layer control panel to the map.
m.add_child(folium.LayerControl())

# Display the map.
m.save('output' + '.html')


#%% 7 - GENERATE TIME SERIES PLOTS
print('7 - GENERATE TIME SERIES PLOTS')

timename = 'system:time_start'
df = gcu.time_series_regions_reducer(DNB_Anomaly,
                                      ['b3'],
                                      Cities_simple,
                                      FeatureID='nome',
                                      timescale= timename,
                                      timeunit = 'date',
                                      stats='median',
                                      scale=470)

with open('./Nightlights_Data/Rio_de_Janeiro/cities_median.pickle', 'wb') as f:
    pickle.dump(df, f)

bairroslist = list(df.keys())
bairroslist.remove(timename)
# print(bairroslist)
fig,ax = plt.subplots()
for name in bairroslist:
    ax.plot(df[timename],df[name],label=name)

ax.set_xlabel("date")
ax.set_ylabel("Relative Anomaly of Nightlights")
ax.legend(loc='best')
plt.show()



