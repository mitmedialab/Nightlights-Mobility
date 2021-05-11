#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 13:57:03 2020

@author: jackreid
"""

def ShapefileFormatter(shpfilepath, writepath):
    """Uses pandas to import an Excel matrix as a Dataframe and format it
    to pull out Median Household Income for each county in the US
    
    It then uses the pyshp library (also known as shapefile) to import a shapefile
    containing geometries of each state in the US. 
    
    Finally it saves a new shapefile that is a copy of the imported one, with 
    Median Household Income appended to the record of each county.
    
    [NOTE: CURRENTLY CONFIGURED TO LOOK FOR BAIRRO NAME MATCHES]
    
    Args:
        shpfilepath: file path to the input shapefile
        datapath: file path to the excel spreadsheet with the relevant data.
        fieldname: the column title in the spreadsheet of the data to be added
        fieldabr: the actual title of the field to be added to the shapefile
        writepath: destination and title of the output shapefile
                           
    Returns:
        r2: The output shapefile that was saved to write path.
        """
        
    import shapefile

    
    # Read in original shapefile
    r = shapefile.Reader(shpfilepath, encoding="ISO-8859-1")
    
    # Create a new shapefile in memory
    w = shapefile.Writer(writepath, encoding="ISO-8859-1")
    
    # Copy over the existing fields
    fields = r.fields
    for name in fields:
        if type(name) == "tuple":
            continue
        else:
            args = name
            w.field(*args)
        
    # Copy over exisiting records and geometries
     
    for shaperec in r.iterShapeRecords():
       
        oldstring = shaperec.record['nome']
        newstring = oldstring.replace(" ", "_")
        shaperec.record['nome'] = newstring
        print(shaperec.record)
        w.shape(shaperec.shape)
        w.record(*shaperec.record)
    
    # Close and save the altered shapefile
    w.close()
    return shapefile.Reader(writepath)



shppath = '/home/jackreid/Documents/School/Research/Space Enabled/Code/Nightlights-Mobility/Shapefiles/State/hc979qh6228_gcs.shp'
writepath = '/home/jackreid/Documents/School/Research/Space Enabled/Code/Nightlights-Mobility/Shapefiles/State/hc979qh6228_gcs_Underscores.shp'


ShapefileFormatter(shppath, writepath)



