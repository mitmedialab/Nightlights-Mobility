#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 10:42:17 2021

@author: jackreid
"""


def nightlights_TS(imageCol,
                   aoi,
                   startDate,
                   endDate,
                   FeatureID = '',
                   boundaries = '',
                   encoding = '',
                   ref_start = '',
                   ref_end = '',
                   observation_start = '',
                   observation_end = '',
                   pandemic_start = '',
                   pandemic_end = '',
                   df_writepath = 'df_output',
                   csv_writepath = 'csv_output',
                   map_writepath = 'map_output.html'):
   
        
    import ee
    import geemap
    import folium
    
    #Import GCU from https://github.com/mitmedialab/Nightlights-Mobility
    from gee_custom_utilities import gee_custom_utilities as gcu
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import pickle
    import numpy as np
    
    
    #%% 1 - SELECT AREAS OF INTEREST
    print('1 - SELECT AREAS OF INTEREST')
   
    boundFlag = 0
    if boundaries:
        boundFlag = 1
        if type(boundaries) is str:
            if encoding:
                Cities = geemap.shp_to_ee('./Shapefiles/State/hc979qh6228_gcs_Underscores.shp', encoding="ISO-8859-1")
            else:
                Cities = geemap.shp_to_ee('./Shapefiles/State/hc979qh6228_gcs_Underscores.shp')
        elif type(boundaries) is ee.featurecollection.FeatureCollection:
            Cities = boundaries
        
        region_list = ee.List(ee.Dictionary(Cities.aggregate_histogram(FeatureID)).keys())
    
        def collapse_features(name):
            # name = ee.Feature(feat.get(FeatureID))
            filtered_feats = Cities.filterMetadata(FeatureID, 'equals', name)
            return ee.Feature(ee.Algorithms.If(filtered_feats.size().eq(1),
                                        filtered_feats.first(),
                                       filtered_feats.union().first().set(FeatureID, name)))
        
    
        Cities_simple = ee.FeatureCollection(region_list.map(collapse_features))
    else:
        Cities_simple = aoi
        Cities = aoi
    
       
   
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
    
    DNB_a2 = ee.ImageCollection(imageCol)
    DNB_processed = DNB_a2.map(DNBA2_Processing)
    
    # #REDUCE DATA TO WEEKLY AVERAGES

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
    

    
    #CALCULATE THE RELATIVE ANOMALY
    if not ref_start:
        ref_start = startDate
    if not ref_end:
        ref_end = endDate
    if not observation_start:
        observation_start = ref_start
    if not observation_end:
        observation_end = ref_end
        
    DNB_Anomaly = AnomalyCalc(weeklyMeans, ref_start, ref_end, startDate, endDate)
    
    #CALCULATE THE MEAN ANOMALY
    DNB_MeanAnomaly = AnomalyMeanCalc(weeklyMeans.select('b3'), ref_start, ref_end, observation_start, observation_end)
    
    #%% 5 - CALCULATE THE THEIL-SEN ESTIMATOR FOR POST-PANDEMIC PERIOD
    print('5 - CALCULATE THE THEIL-SEN ESTIMATOR FOR POST-PANDEMIC PERIOD')
    
    if not pandemic_start:
        pandemic_start = observation_start
    if not pandemic_end:
        pandemic_end = observation_end
        

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
    
    
    
    MeanAnomalyVisParams = {"opacity":1,
                            "min":-100,
                            "max":100,
                            "gamma":1}

    
    m.add_ee_layer(DNB_MeanAnomaly,
                    MeanAnomalyVisParams,
                    'Nightlights Mean Anomaly', True, 1, 9)
    
    BairrosVisParams = {"opacity":1,
                            'palette': 'd62ccd'}
    m.add_ee_layer(outline,
                    BairrosVisParams,
                    'edges', True, 1, 9)
    
    
    # Add a layer control panel to the map.
    m.add_child(folium.LayerControl())
    
    # Display the map.
    m.save(map_writepath)
    
    
    #%% 7 - GENERATE TIME SERIES PLOTS
    print('7 - GENERATE TIME SERIES PLOTS')
    
    timename = 'system:time_start'
    df = gcu.time_series_regions_reducer(DNB_Anomaly,
                                          ['b3'],
                                          Cities_simple,
                                          FeatureID=FeatureID,
                                          timescale= timename,
                                          timeunit = 'date',
                                          stats='median',
                                          scale=470)
    
    with open(df_writepath, 'wb') as f:
        pickle.dump(df, f)
        
    df.to_csv(csv_writepath)
    
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



import ee

#%% Rio de Janeiro State

# imageCol = 'users/jackreid/nightlights/rio_state_nightlights_2019_01_to_2021_05'
# aoi = ee.Geometry.Polygon(
#                 [[[-44.96879073675279, -20.600786671961583],
#                   [-44.96879073675279, -23.502425722766645],
#                   [-40.75004073675279, -23.502425722766645],
#                   [-40.75004073675279, -20.600786671961583]]])

# ID = 'nome'
# bound = './Shapefiles/State/hc979qh6228_gcs_Underscores.shp'
# enc = "ISO-8859-1"
# startDate = ee.Date('2019-01-01')
# endDate = ee.Date('2021-01-01')
# #DEFINE THE REFERENCE PERIOD
# ref_start = startDate
# ref_end =  '2020-03-01'

# #DEFINE THE OBSERVATION PERIOD
# observation_start = ref_end
# observation_end =  endDate
    
# pandemic_start = '2020-03-01'
# pandemic_end =  '2020-08-30'

# write_path = './Nightlights_Data/Rio_de_Janeiro/cities_median.pickle'
# nightlights_TS(imageCol,
#                aoi,
#                startDate,
#                endDate,
#                FeatureID = ID,
#                boundaries = bound,
#                encoding = enc,
#                ref_start = ref_start,
#                ref_end = ref_end,
#                observation_start = observation_start,
#                observation_end = observation_end,
#                df_writepath = write_path)

# #%% Guatemala
# imageCol = 'users/jackreid/nightlights/guatemala_transit_nightlights_2019_01_to_2020_12'
# aoi = ee.Geometry.Polygon(
#                     [[[-90.68273918718909, 14.753966023114078],
#                       [-90.68273918718909, 14.400430324763159],
#                       [-90.33254997820471, 14.400430324763159],
#                       [-90.33254997820471, 14.753966023114078]]]);

# CentraSur_geo = ee.Geometry.Polygon(
#                     [[[-90.56444166931351, 14.560997264128014],
#                       [-90.56360482010086, 14.560851884837696],
#                       [-90.56310861143311, 14.56112447092845],
#                       [-90.5615770700856, 14.560831116359832],
#                       [-90.56037870952217, 14.561902085342767],
#                       [-90.55981008121101, 14.564020449726058],
#                       [-90.55965987750618, 14.56557805761448],
#                       [-90.56113905943248, 14.568101476382914],
#                       [-90.56326336897227, 14.568392225309234],
#                       [-90.5634135726771, 14.56793533396716]]])

# CentraSur_feat = ee.Feature(CentraSur_geo,{'name': 'Centra_Sur'})

# CentraNorte_geo= ee.Geometry.Polygon(
#                     [[[-90.45174091182079, 14.64531587554577],
#                       [-90.45033006987896, 14.645507910102339],
#                       [-90.44963269553509, 14.645886788599052],
#                       [-90.44970632086307, 14.64627131196354],
#                       [-90.45080066214115, 14.647984039199049],
#                       [-90.45080066214115, 14.64933345123238],
#                       [-90.45149803648502, 14.649317881140908],
#                       [-90.45173407087833, 14.648061890119074],
#                       [-90.45222223291904, 14.647080966506167],
#                       [-90.4521417666486, 14.64617269998806]]]);

# CentraNorte_feat = ee.Feature(CentraNorte_geo, {'name': 'Centra_Norte'})

# TransitStations = ee.FeatureCollection([CentraSur_feat, CentraNorte_feat])

# ID = 'name'
# bound = TransitStations
# # enc = "ISO-8859-1"
# startDate = ee.Date('2019-01-01')
# endDate = ee.Date('2021-01-01')
# #DEFINE THE REFERENCE PERIOD
# ref_start = startDate
# ref_end =  '2019-12-31'

# #DEFINE THE OBSERVATION PERIOD
# observation_start = ref_end
# observation_end =  endDate
    
# pandemic_start = '2020-02-01'
# pandemic_end =  '2020-05-01'

# write_path = './Nightlights_Data/Guatemala/cities_median.pickle'
# map_writepath = './Nightlights_Data/Guatemala/map_output.html'
# csv_writepath = './Nightlights_Data/Guatemala/RelativeAnomaly.csv'
# nightlights_TS(imageCol,
#                 aoi,
#                 startDate,
#                 endDate,
#                 FeatureID = ID,
#                 boundaries = bound,
#                 # encoding = enc,
#                 ref_start = ref_start,
#                 ref_end = ref_end,
#                 observation_start = observation_start,
#                 observation_end = observation_end,
#                 df_writepath = write_path,
#                 map_writepath = map_writepath,
#                 csv_writepath = csv_writepath)

#%% San Salvador
# imageCol = 'users/jackreid/nightlights/sansalvador_transit_nightlights_2019_01_to_2020_12'
# aoi = ee.Geometry.Polygon(
#                         [[[-89.32748630288565, 13.762322718735758],
#                           [-89.32748630288565, 13.634570369885033],
#                           [-89.01883914712393, 13.634570369885033],
#                           [-89.01883914712393, 13.762322718735758]]])

# Occidente_geo = ee.Geometry.Polygon(
#                         [[[-89.22018135449503, 13.693094259183754],
#                           [-89.21928549668405, 13.692875357236094],
#                           [-89.21869004628275, 13.692526156088281],
#                           [-89.21809459588144, 13.69413664661517],
#                           [-89.21929086110208, 13.694485845371421],
#                           [-89.22000432870004, 13.694496269206912]]])

# Occidente_feat = ee.Feature(Occidente_geo,{'name': 'Occidente'})

# Oriente_geo= ee.Geometry.Polygon(
#                         [[[-89.13997689485689, 13.69695578494485],
#                           [-89.14078155756135, 13.69388076559937],
#                           [-89.13952628374238, 13.693583685328935],
#                           [-89.1388074517264, 13.696695191644803]]])

# Oriente_feat = ee.Feature(Oriente_geo, {'name': 'Oriente'})

# TransitStations = ee.FeatureCollection([Occidente_feat, Oriente_feat])

# ID = 'name'
# bound = TransitStations
# # enc = "ISO-8859-1"
# startDate = ee.Date('2019-01-01')
# endDate = ee.Date('2021-01-01')
# #DEFINE THE REFERENCE PERIOD
# ref_start = startDate
# ref_end =  '2019-12-31'

# #DEFINE THE OBSERVATION PERIOD
# observation_start = ref_end
# observation_end =  endDate
    
# pandemic_start = '2020-02-01'
# pandemic_end =  '2020-05-01'

# write_path = './Nightlights_Data/SanSalvador/cities_median.pickle'
# map_writepath = './Nightlights_Data/SanSalvador/map_output.html'
# csv_writepath = './Nightlights_Data/SanSalvador/RelativeAnomaly.csv'
# nightlights_TS(imageCol,
#                aoi,
#                startDate,
#                endDate,
#                 FeatureID = ID,
#                 boundaries = bound,
#                # encoding = enc,
#                ref_start = ref_start,
#                ref_end = ref_end,
#                observation_start = observation_start,
#                observation_end = observation_end,
#                df_writepath = write_path,
#                map_writepath = map_writepath,
#                csv_writepath = csv_writepath)

#%% Tegucigalpa

imageCol = 'users/jackreid/nightlights/tegucigalpa_transit_nightlights_2019_01_to_2020_12'
aoi = ee.Geometry.Polygon(
                            [[[-87.28230388149557, 14.13751643714509],
                              [-87.28230388149557, 14.020630070279841],
                              [-87.11338908657369, 14.020630070279841],
                              [-87.11338908657369, 14.13751643714509]]])

Oriente_geo = ee.Geometry.Polygon(
                            [[[-87.18418940544665, 14.069109483230708],
                              [-87.18357249737322, 14.06918233225756],
                              [-87.18312188625872, 14.069372259968437],
                              [-87.18312725067675, 14.069538771804336],
                              [-87.1834249758774, 14.070092943134675],
                              [-87.18367173910677, 14.070543043742996],
                              [-87.18433424473345, 14.070527433332103]]])

Oriente_feat = ee.Feature(Oriente_geo,{'name': 'Oriente'})

CentroCommunal_geo= ee.Geometry.Polygon(
                            [[[-87.24356772497772, 14.074845138700962],
                              [-87.24306883410095, 14.075183357642256],
                              [-87.24360259369492, 14.076000284404982],
                              [-87.24422754839539, 14.075716701878799],
                              [-87.2439244587767, 14.075048070125812]]])

CentroCommunal_feat = ee.Feature(CentroCommunal_geo, {'name': 'Centro_Communal'})

TransitStations = ee.FeatureCollection([Oriente_feat, CentroCommunal_feat])

ID = 'name'
bound = TransitStations
# enc = "ISO-8859-1"
startDate = ee.Date('2019-01-01')
endDate = ee.Date('2021-01-01')
#DEFINE THE REFERENCE PERIOD
ref_start = startDate
ref_end =  '2019-12-31'

#DEFINE THE OBSERVATION PERIOD
observation_start = ref_end
observation_end =  endDate
    
pandemic_start = '2020-02-01'
pandemic_end =  '2020-05-01'

write_path = './Nightlights_Data/Tegucigalpa/cities_median.pickle'
map_writepath = './Nightlights_Data/Tegucigalpa/map_output.html'
csv_writepath = './Nightlights_Data/Tegucigalpa/RelativeAnomaly.csv'
nightlights_TS(imageCol,
                aoi,
                startDate,
                endDate,
                FeatureID = ID,
                boundaries = bound,
                # encoding = enc,
                ref_start = ref_start,
                ref_end = ref_end,
                observation_start = observation_start,
                observation_end = observation_end,
                df_writepath = write_path,
                map_writepath = map_writepath,
                csv_writepath = csv_writepath)