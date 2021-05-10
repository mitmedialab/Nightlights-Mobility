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

#%% 1 - SELECT AREAS OF INTEREST
print('1 - SELECT AREAS OF INTEREST')
aoi = ee.Geometry.Polygon(
                    [[[-43.86562188407029, -22.606165337374964],
                      [-43.86562188407029, -23.09465315896709],
                      [-42.96680291434373, -23.09465315896709],
                      [-42.96680291434373, -22.606165337374964]]])


Bairros = geemap.shp_to_ee('./Shapefiles/City/Bairros_Underscores.shp')
cidadedeus = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Cidade_de_Deus').first())
pedra = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Pedra_de_Guaratiba').first())
Copacabana = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Copacabana').first())
Ipanema = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Ipanema').first())
Centro = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Centro').first())
nova = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Cidade_Nova').first())
campo = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Campo_Grande').first())
barra = ee.Feature(Bairros.filterMetadata('BAIRRO', 'equals', 'Barra_da_Tijuca').first())

Cities = geemap.shp_to_ee('./Shapefiles/State/hc979qh6228_gcs.shp', encoding="ISO-8859-1")
city = Cities.filterMetadata('nome', 'equals','Rio de Janeiro')
city.set('BAIRRO','Municipality')

galeaoairpot = ee.Geometry.Polygon(
                    [[[-43.23685761485591, -22.83324356871556],
                      [-43.230420313220165, -22.824462648497825],
                      [-43.23153611217036, -22.821931106850233],
                      [-43.235359645886355, -22.818317892377266],
                      [-43.23729083637708, -22.816419154871188],
                      [-43.241324878735476, -22.812146898697424],
                      [-43.238621212048464, -22.8086261424378],
                      [-43.22699115375989, -22.806450348700384],
                      [-43.22454497913831, -22.80506573459566],
                      [-43.221626735730105, -22.80205909552519],
                      [-43.21883028475359, -22.798221463985623],
                      [-43.211663422265794, -22.793790381813356],
                      [-43.21217840639665, -22.79193086693171],
                      [-43.21179216829851, -22.790466975674374],
                      [-43.219388184228684, -22.785086051151122],
                      [-43.22226351229265, -22.78793480234472],
                      [-43.23646849123552, -22.790941752939236],
                      [-43.24549584565545, -22.794577118950265],
                      [-43.2581129568615, -22.800432413155413],
                      [-43.266009380201346, -22.81206312980688],
                      [-43.24772744355584, -22.824404845131014],
                      [-43.2511606710949, -22.827648315448524],
                      [-43.24000268159295, -22.833976815489148]]])
santosdumontairport =  ee.Geometry.Polygon(
                    [[[-43.16940920317302, -22.90516841335352],
                      [-43.16852319907619, -22.905916982344156],
                      [-43.168308622355, -22.909929346274648],
                      [-43.16905964087917, -22.911016419506584],
                      [-43.16902008986651, -22.911788257193198],
                      [-43.16891092111654, -22.914628779327295],
                      [-43.16842812349386, -22.914994419529307],
                      [-43.167859495182704, -22.91472760110079],
                      [-43.165595710774134, -22.91587392840776],
                      [-43.16384027899408, -22.91722207269259],
                      [-43.16160868109369, -22.917538296063405],
                      [-43.161549456664225, -22.916669302483047],
                      [-43.16165674502482, -22.914554531099384],
                      [-43.160830624648234, -22.912775725881946],
                      [-43.16121106600032, -22.90781669779702],
                      [-43.161307625524856, -22.905207645824404],
                      [-43.16249852632747, -22.90425888720608],
                      [-43.1692040488647, -22.904505960402165]]])
industrial = ee.Geometry.Polygon(
                    [[[-43.78856411622486, -22.948276735692847],
                      [-43.75182858155689, -22.944482867724663],
                      [-43.739297301039315, -22.938475692614674],
                      [-43.710801512465096, -22.906933651335525],
                      [-43.72350445435963, -22.90187359307296],
                      [-43.730800062880135, -22.89894816076502],
                      [-43.73158224791568, -22.894259208794608],
                      [-43.72248419493717, -22.886905562444028],
                      [-43.707807147207674, -22.875281244312408],
                      [-43.70960959166568, -22.87132716779013],
                      [-43.72342833251041, -22.87069450486392],
                      [-43.730037295523104, -22.873699627517723],
                      [-43.72808025552457, -22.878899449036513],
                      [-43.746104700104645, -22.8744709935858],
                      [-43.76395748330777, -22.89028624265098],
                      [-43.81940410806363, -22.896137417761295],
                      [-43.855452997223786, -22.911159549325458],
                      [-43.86266277505582, -22.934875315267025]]])

airport_gal = ee.Feature(galeaoairpot).set('BAIRRO','Galeao_Airport')
airport_san = ee.Feature(santosdumontairport).set('BAIRRO', 'Santos_Dumont_Airport')
indus = ee.Feature(industrial).set('BAIRRO','Industrial_Area')

selectedBairros = ee.FeatureCollection([cidadedeus,
                                        airport_gal,
                                        airport_san,
                                        indus,
                                        pedra,
                                        Copacabana,
                                        Ipanema,
                                        Centro,
                                        nova,
                                        barra,
                                        campo
                                        ])


#%% 2 - DRAW SELECTED AREAS ON MAP
print('2 - DRAW SELECTED AREAS ON MAP')

empty = ee.Image().byte() #Create an empty image into which to paint the features, cast to byte.
outline = empty.paint(featureCollection = selectedBairros,  #featureCollection
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

DNB_a2 = ee.ImageCollection('users/jackreid/rio_nightlights_a2_acquisitiontime')
DNB_processed = DNB_a2.map(DNBA2_Processing)

# #REDUCE DATA TO WEEKLY AVERAGES
startDate = ee.Date('2019-01-01')
endDate = ee.Date('2020-08-01')

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
      .select('b3')
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
observation_end =  '2020-08-30'


#CALCULATE THE RELATIVE ANOMALY
DNB_Anomaly = AnomalyCalc(weeklyMeans.select('b3'), ref_start, ref_end, observation_start, observation_end)

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
                                      selectedBairros,
                                      FeatureID='BAIRRO',
                                      timescale= timename,
                                      timeunit = 'date',
                                      stats='median',
                                      scale=470)



bairroslist = list(df.keys())
bairroslist.remove(timename)
print(bairroslist)
fig,ax = plt.subplots()
for name in bairroslist:
    ax.plot(df[timename],df[name],label=name)

ax.set_xlabel("year")
ax.set_ylabel("weight")
ax.legend(loc='best')
plt.show()
