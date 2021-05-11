#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 10 13:20:12 2021

@author: jackreid
"""

import ee
import folium
from datetime import datetime as dt
import pandas as pd
import numpy as np
from dateutil.parser import parse

# Define a method for displaying Earth Engine image tiles to a folium map.
def add_ee_layer(self, ee_image_object, vis_params, name, show=True, opacity=1, min_zoom=0):
    """ From s2cloudless"""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        show=show,
        opacity=opacity,
        min_zoom=min_zoom,
        overlay=True,
        control=True
        ).add_to(self)
    
    

# Define a function to transfer feature properties to a dictionary.
def fc_to_dict(fc):
  prop_names = fc.first().propertyNames()
  prop_lists = fc.reduceColumns(
      reducer=ee.Reducer.toList().repeat(prop_names.size()),
      selectors=prop_names).get('list')

  return ee.Dictionary.fromLists(prop_names, prop_lists)



def time_series_regions_reducer(imgcol, 
                                bands, 
                                geometry, 
                                FeatureID='BAIRRO', 
                                timescale = 'system:time_start', 
                                timeunit = 'constant',
                                stats='median', 
                                scale=470):
    if stats == 'mean':
        fun = ee.Reducer.mean()
    elif stats == 'median':
        fun = ee.Reducer.median()
    elif stats == 'max':
        fun = ee.Reducer.max()
    elif stats == 'min':
        fun = ee.Reducer.min()
    
    def list_simplify(entry):
        val = ee.List(entry).get(0)
        return val

    def run_reduce(img):
        feat_reduce = (img.select(bands).reduceRegions(
                    collection = geometry,
                    reducer = fun,
                    scale = scale))
        
        data_list_bairro = ee.List(feat_reduce.reduceColumns(ee.Reducer.toList(1), [FeatureID]).get('list'))
        data_list_median = ee.List(feat_reduce.reduceColumns(ee.Reducer.toList(1), [stats]).get('list'))
    
    
        data_list_bairro_simple = ee.List(data_list_bairro.map(list_simplify))
        data_list_median_simple = ee.List(data_list_median.map(list_simplify))
        data_list_median_simple = ee.Algorithms.If(data_list_median_simple.length().lt(ee.List(data_list_bairro_simple).length())
                                                   ,ee.List.repeat(-999999,data_list_bairro_simple.length()),
                                                   data_list_median_simple)
    
        data_dict = ee.Dictionary.fromLists(data_list_bairro_simple, data_list_median_simple)
    
        return img.set(data_dict)
    reduced_collection = imgcol.map(run_reduce)
    # print(test3.getInfo())
    bairros_list_temp = ee.List(geometry.reduceColumns(ee.Reducer.toList(1), [FeatureID]).get('list'))
    bairros_list = bairros_list_temp.map(list_simplify)
    bairros_list_complete = bairros_list.add('system:time_start')
    nested_list = reduced_collection.reduceColumns(ee.Reducer.toList(bairros_list_complete.length()), bairros_list_complete).values().get(0)
    df = (pd.DataFrame(nested_list.getInfo(), columns=list(bairros_list_complete.getInfo())).replace(-999999,np.nan))
    
    if timeunit == 'date':
        for index in df.index.values.tolist():
            df.at[index,'system:time_start'] = dt.fromtimestamp(df.at[index,'system:time_start'] / 1000)
    
    
    return df
