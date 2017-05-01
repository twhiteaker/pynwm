# Get the Latest Forecast for Bull Creek Watershed

**Use Case:**
Support a Web application for flood warning and response in the Bull Creek Watershed by maintaining a netCDF file with the latest forecasted streamflow.

The get_latest_forecast.py script downloads forecasted streamflow for rivers of interest and merges the result into a single netCDF file.  It also computes the maximum streamflow for each river and stores that as a variable in the same file. The Web application can then read data from the file.  Run as a scheduled task or cron job to keep your data current.

Related files:
* bull_creek_comids.txt - List of river identifiers in the watershed.
* config.json - Configuration parameters such as where to save the result.
* nhd_flowline.json - GeoJSON of river locations.