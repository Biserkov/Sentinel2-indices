dates = ["2018-09-01", "2018-05-29", "2018-06-08", "2018-08-07", "2018-10-06", "2018-10-16"]
base = "E:\\VB\Vitosha\\"
target = base + "Target_area_10km2.shp"

formulas = {
    #  # 10m
    "NDVI": "($B08 - $B04) / ($B08 + $B04)",
    "NDVI-GREEN": "$B03 * ($B08 - $B04) / ($B08 + $B04)",
    "CRI1": "1 / $adj02 - 1 / $adj03",
    "PSSRa": "$B08 / $B04",
    "PSSRc": "$B08 / $B02",
    "SAVI": "1.5 * ($B08 - $B04) / ($B08 + $B04 + 0.5)",
    "NDWI": "($B03 - $B08) / ($B03 + $B08)",
    "MSAVI": "(2 * $B08 + 1 - SquareRoot((2 * $B08 + 1) ** 2 - 8 * ($B08 - $B04) ))/2",
    #"BAI": "1 / ( (0,1 - $adj04) ** 2 + (0.06 - $adj08) ** 2)",

    #  # 20m
    # "Red edge NDVI": "($B08 - $B06) / ($B08 + $B06)",
    # "GNDVI": "($B8A - $B03) / ($B8A + $B03)",
    # "NDVI705": "($B06 - $B05) / ($B06 + $B05)",  
    # "CRI2": "1 / $adj02 - 1 / $adj05",
    # "MSI":  "$B11 / $B08",
    # "EVI": "2.5 * ($B8A - $B04)/(1 + $B8A + 6 * $B04 - 7.5 * $B02)",
    # "MCARI": "1 - 0.2 * ($adj05 - $adj03) / ($adj05 - $adj04)",
    # "NBR": "($B08 - $B12) / ($B08 + $B12)",
    # "S2REP": "705 + 35 * (0.5 * ($B07 + $B04) - $B05) / ($B06 - $B05)",
    # "PSRI": "($B04 - $B02) / $B05",
    # "MNDWI": "($B03 - $B11) / ($B03 + $B11)",
    # "RE-NDWI": "($B03 - $B05) / ($B03 + $B05)",
    # "NDII": "($B08 - $B11) / ($B08 + $B11)",
    # "NDBI": "($B11 - $B08) / ($B11 + $B08)",
    # "MTCI": "($B06 - $B05) / ($B05 - $B04)",

    #  # 60m
    # "mSR705": "($B06 - $B01) / ($B05 - $B01)",
    # "mNDVI705": "($B06 - $B05) / ($B06 + $B05 - (2 * $B01))",
    # "SIPI": "($B08 - $B01) / ($B08 - $B04)",
}


### DON'T EDIT BELOW

selected_indexes = formulas.keys()

import string
import os
import arcpy
from time import gmtime, strftime
arcpy.env.pyramid = "PYRAMIDS -1 CUBIC LZ77 NO_SKIP"
print(strftime("%H:%M:%S", gmtime()) + " start processing")
#arcpy.CheckOutExtension('Spatial')
from arcpy.sa import *
rasters = base + "Rasters\\"
if not os.path.exists(rasters):
		os.makedirs(rasters)
Bands_folder = base + "Bands\\"        
if not os.path.exists(Bands_folder):
		os.makedirs(Bands_folder)

maxes = {
    "adj10": "($B10 / $B10_max)",    
    "adj11": "($B11 / $B11_max)",
    "adj12": "($B12 / $B12_max)",
    "adj8A": "($B8A / $B8A_max)",
    }

for i in range(1, 10):
    maxes["adj0" + str(i)] = "($B0"+str(i)+"_max / $B0"+str(i)+")"

for f, defn in formulas.items():
    formulas[f] = string.Template(defn).safe_substitute(maxes)

s2 = os.listdir(base + "S2")

bands_by_res = {
    "10": ["B02", "B03", "B04", "B08", "TCI"],
    "20": ["B05", "B06", "B07", "B8A", "B11", "B12"],
    "60": ["B01", "B09"]
}

for d in dates:
    date_no_dash = d.replace("-", "")
    prefix_2A = "S2A_MSIL2A_" + date_no_dash
    prefix_2B = "S2B_MSIL2A_" + date_no_dash
    a = [item for item in s2 if (item.startswith(prefix_2A) or item.startswith(prefix_2B)) ][0]
    b = base + "S2\\"+a+r"\GRANULE"
    c = os.listdir(b)[0]  
    bands = {}

    for res in ["10", "20", "60"]:
        path = b + "\\"+c + "\\IMG_DATA\\R"+ res + "m\\"
        for r in bands_by_res[res]:
            f = [item for item in os.listdir(path) if r in item][0]
            bands[r] = path + f

    if not os.path.exists(rasters+d):
        os.makedirs(rasters+d)
    if not os.path.exists(Bands_folder+d):
        os.makedirs(Bands_folder+d)
        
   
    my_bands = {}
    my_max = {}
    
    for b in bands.keys():
        my_band = Bands_folder + d + "\\" + b + ".tif"
        my_bands[b] = my_band
        #print(my_band)
        arcpy.sa.ExtractByMask(bands[b], target).save(my_band); 
        my_max[b+"_max"] = arcpy.GetRasterProperties_management(my_band, "MAXIMUM").getOutput(0)

    my_vars = {}
    for key, value in my_bands.items():
        my_vars[key] = "Raster(r\"" + value + "\")"

    for f in selected_indexes:
        expr = string.Template(formulas[f]).substitute({**my_vars, **my_max})
        
        #print(f, expr)
        out = rasters + d + "\\" + f + " " + d + ".tif"
        res = eval(expr, globals(), locals()).save(out)

    print(strftime("%H:%M:%S", gmtime()) + " done processing " + d)