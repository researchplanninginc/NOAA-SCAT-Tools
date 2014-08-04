# ---------------------------------------------------------------------------
# import_snapping_output.py
# Created on: Tue Oct 05 2010
#
# Usage: import_snapping_output <Snapping_Output_Directory> <Snapping_Output_Shapefile> 
#
# Date Modified: November 4, 2010 - Modified to sort mr_oiling output on date and oiling for correct draw order
#                November 5, 2010 - Modified to generate zonesurvid on mr_oiling output for joining to allzones
#                July 20, 2013 - Modified to remove partitioned segment information for maximum and most recent oiling
#
# ---------------------------------------------------------------------------

# Import system modules
import sys, string, os, datetime, arcpy
from arcpy import env

# Script arguments...
directory = sys.argv[1]
sn_all_zones = sys.argv[2]
mstr_segments = sys.argv[3]

env.qualifiedFieldNames = False
arcpy.OverWriteOutput = 1

# Script environment...
spatialRef = arcpy.SpatialReference(3083)
arcpy.outputCoordinateSystem = spatialRef

try:

# Local variables...

    # Output Filenames..
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y_%m_%d")

    arcpy.MakeFeatureLayer_management(sn_all_zones, "maxoilzones", "max_oiling <> 'NOO'")

    oil_zones = directory + "\\Oiled_HSegs_" + nowstr + ".shp"
    all_zones = directory + "\\Clipped_HSegs_" + nowstr + ".shp"
    mr_oil = directory + "\\MR_OilZones_" + nowstr + ".shp"
    mr_oil_temp = directory + "\\MR_temp.shp"
    max_oil = directory + "\\Max_OilZones_0_" + nowstr + ".shp"
    max_oil_0 = directory + "\\Max_OilZones_" + nowstr + ".shp"

    arcpy.AddMessage("Defining Projections...")

    # Process: Define Input Projections...
    arcpy.DefineProjection_management(sn_all_zones, "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]")

    # Process: Dissolves...
    arcpy.AddMessage("Dissolving to all oiled zones by segment..")
    arcpy.Dissolve_management("maxoilzones", oil_zones, "segment", "", "MULTI_PART", "DISSOLVE_LINES")
    arcpy.AddMessage("Dissolving to all zones by segment..")
    arcpy.Dissolve_management(sn_all_zones, all_zones, "segment", "", "MULTI_PART", "DISSOLVE_LINES")
    arcpy.AddMessage("Dissolving to most recent zones by segment..")
    arcpy.Dissolve_management(sn_all_zones, mr_oil_temp, "segment;mr_oiling;mr_date;mr_zone", "", "MULTI_PART", "DISSOLVE_LINES")
    arcpy.AddMessage("Dissolving to max zones by segment..")
    arcpy.Dissolve_management(sn_all_zones, max_oil, "segment;max_oiling;max_date;max_zone", "", "MULTI_PART", "DISSOLVE_LINES")
    
    # Process to remove partitioned information and keep only parent segment information
    arcpy.AddMessage("Joining max zones to parent segment information...")
    arcpy.MakeFeatureLayer_management(mr_oil_temp, "mr_oil_lyr")
    arcpy.MakeFeatureLayer_management(max_oil, "max_oil_lyr")
    arcpy.AddJoin_management("mr_oil_lyr", "segment", mstr_segments, "SegNum", "KEEP_ALL")
    arcpy.AddJoin_management("max_oil_lyr", "segment", mstr_segments, "SegNum", "KEEP_ALL")
    arcpy.SelectLayerByAttribute_management("mr_oil_lyr", "NEW_SELECTION", " \"PARENT_ID\" > ''")
    arcpy.SelectLayerByAttribute_management("max_oil_lyr", "NEW_SELECTION", " \"PARENT_ID\" > ''")
    arcpy.DeleteFeatures_management("mr_oil_lyr")
    arcpy.DeleteFeatures_management("max_oil_lyr")
    arcpy.RemoveJoin_management("mr_oil_lyr", "HSegments_CURRENT")
    arcpy.RemoveJoin_management("max_oil_lyr", "HSegments_CURRENT")
    

    # Process: Add and update oilcode field for sorting oiling characterization by severity...
    arcpy.AddMessage("Adding oilcode field for sorting...")
    arcpy.AddField_management(mr_oil_temp, "mr_oilcode", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    rows = arcpy.UpdateCursor(mr_oil_temp)
    row = rows.next()
    while row:
        if row.mr_oiling in ("Light_TB","Mod_TB","Heavy_TB","Neg_TB"):
           row.mr_oilcode = 1
        if row.mr_oiling == "Very_Light":
           row.mr_oilcode = 2
        if row.mr_oiling == "Light":
           row.mr_oilcode = 3
        if row.mr_oiling == "Moderate":
           row.mr_oilcode = 4
        if row.mr_oiling == "Heavy":
           row.mr_oilcode = 5
        rows.updateRow(row)
        row = rows.next()
    del row
    del rows
  

    # Process: Create zonesurvid for linking to allzones report DBF output for most recent oiling...
    arcpy.AddField_management(mr_oil_temp, "zonesurvid", "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")
    rows = arcpy.UpdateCursor(mr_oil_temp)
    row = rows.next()
    while row:
        idstring = str(row.segment)+str(row.mr_date)+str(row.mr_zone)
        row.zonesurvid = idstring
        rows.updateRow(row)
        row = rows.next()
    del row
    del rows

    # Process: Create zonesurvid for linking to allzones report DBF output for max oiling...
    arcpy.AddField_management(max_oil, "zonesurvid", "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")
    rows = arcpy.UpdateCursor(max_oil)
    row = rows.next()
    while row:
        idstring = str(row.segment)+str(row.max_date)+str(row.max_zone)
        row.zonesurvid = idstring
        rows.updateRow(row)
        row = rows.next()
    del row
    del rows
    
    # Process: Lengths...
    arcpy.AddMessage("Updating lengths..")
    arcpy.AddField_management(oil_zones, "length_m", "DOUBLE", 18, 11)
    arcpy.AddField_management(all_zones, "length_m", "DOUBLE", 18, 11)
    arcpy.AddField_management(mr_oil_temp, "length_m", "DOUBLE", 18, 11)
    arcpy.AddField_management(max_oil, "length_m", "DOUBLE", 18, 11)

    lExpression = "float(!SHAPE.LENGTH@METERS!)"

    arcpy.CalculateField_management(oil_zones, "length_m", lExpression, "PYTHON")
    arcpy.CalculateField_management(all_zones, "length_m", lExpression, "PYTHON")
    arcpy.CalculateField_management(mr_oil_temp, "length_m", lExpression, "PYTHON")
    arcpy.CalculateField_management(max_oil, "length_m", lExpression, "PYTHON")    

    # Process: Sort features in most recent oiling on date and oil characterization to reproduce stacked draw order...
    arcpy.AddMessage("Sorting features in most recent oiling on date and oil characterization for draw order..")
    sort_fields = [["mr_date", "ASCENDING"], ["mr_oilcode", "DESCENDING"]]
    arcpy.Sort_management(mr_oil_temp, mr_oil, sort_fields)
    #subprocess.call(["E:\RPI Projects\Kirby Spill\Report Generation Tools\ArcMapTools\shpsort.exe", mr_oil_temp, mr_oil, "mr_date;mr_oilcode", "ASCENDING;ASCENDING"])
    arcpy.Delete_management(mr_oil_temp)


    arcpy.Select_analysis(max_oil, max_oil_0, '"length_m" > 0')
    
    

except arcpy.ExecuteError:
    # Get the geoprocessing error messages
    msgs = arcpy.GetMessage(0)
    msgs += arcpy.GetMessages(2)

    # Return gp error messages for use with a script tool
    arcpy.AddError(msgs)

    # Print gp error messages for use in Python/PythonWin
    print msgs    
