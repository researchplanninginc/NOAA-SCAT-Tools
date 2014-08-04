# ---------------------------------------------------------------------------
# make_snapping_zones.py
# Created on: Thu Oct 07 2010
# 
# Usage: make_snapping_zones <OilZones_Current_Shapefile> <All_Zones_DBF_From_ReportGen> <Snapping_OilZones_Shapefile> 
# ---------------------------------------------------------------------------

# Import system modules
import sys, string, os, datetime, arcpy
from arcpy import env

# Load required toolboxes...
#arcpy.AddToolbox("E:\RPI Projects\Kirby Spill\GIS_Data\Kirby SCAT.gdb\SCAT_Tools.tbx")

env.qualifiedFieldNames = False
arcpy.OverWriteOutput = 1

# Script arguments...
all_zones_shp = sys.argv[1]
table = sys.argv[2]
output = sys.argv[3]

now = datetime.datetime.now()
nowstr = now.strftime("%Y-%m-%d")

if all_zones_shp == '#':
    all_zones_shp = "D:\Data\Shapefiles\OilZones_CURRENT.shp" # provide a default value if unspecified

if output == '#':
    output = "D:\\Data\\SnappingRPT\\OilZones_" + nowstr + ".shp" # provide a default value if unspecified 
    
tmpout = output.replace(".shp", "_tmp.shp")
addzones = "D:\\Data\\SpecialRequest\SegmentPartitions\Additional_SnapZones.shp"
mrgin = tmpout + ";" + addzones    

try:
    # Make a layer from the feature class
    arcpy.MakeFeatureLayer_management(all_zones_shp,"zones_shape")
    arcpy.MakeTableView_management(table,"zones_table")

    # Process: Add Join...
    arcpy.AddJoin_management("zones_shape", "ZoneSurvID", "zones_table", "UniqueZnID", "KEEP_ALL")
    fieldlist = arcpy.ListFields("zones_shape")
    arcpy.AddMessage("Joining...")
    
    # Process: Create Feature Class...
    arcpy.CopyFeatures_management("zones_shape", tmpout)

    # Process: Delete Field...
    arcpy.DeleteField_management(tmpout, "lat1;lon1;lat2;lon2;DateAdded;OID_;UniqueZnID;Segment;State;County;OpDiv;SegName;SegLength;SurvDate_1;SStartTime;TeamNum;IsMRSurv;IsMaxSurv;ZoneName;ZoneLat;ZoneLon;ZoneEndLat;ZoneEndLon;TidalZone;IsPrimary;CleanConcn;ZoneLength;ZoneWidth;HtOnPlants;PctOverlap;ZoneCommnt;Debris;OiledDebri;SODistro;SOThicknes;OilingChar;TBCount;TBArea;TBAreaUnit;TBAvgSize;TBMaxSize;TBType;TBCount1;TBType1;TBCount2;TBType2;TBCount3;TBType3;Team1;Team2;Team3;Team4;Team5;Team6;Team7;Team8")
    arcpy.AddMessage("Dropping Fields..")
    arcpy.Merge_management(mrgin, output)
    arcpy.Delete_management(tmpout)
    
except arcpy.ExecuteError:
    # Get the geoprocessing error messages
    msgs = arcpy.GetMessage(0)
    msgs += arcpy.GetMessages(2)

    # Return gp error messages for use with a script tool
    arcpy.AddError(msgs)

    # Print gp error messages for use in Python/PythonWin
    print msgs  
