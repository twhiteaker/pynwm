# Versions

v1.0 Spans from May, 2015 (beta), August, 2015 (production), to May 8, 2017, before noon UTC. It used float as the data type.

v1.1 Started on May 8, 2017, at noon UTC (except the Short Range product which started at 11:00 UTC). It uses int as the data type so file sizes are up to 10 times smaller. Georeferencing data are included in gridded products. 

To distinguish between v1.0 and v1.1 channel files, the safest bet is to look at the feature identifer dimension to see if it is 'station' (v1.0) or 'feature_id' (v1.1).

## Some v1.1 changes

* All nwm file types are significantly smaller than before and will allow for longer archiving if desired
* The "fe" files have been renamed to "forcing"
* The "forcing", "land", "terrain_rt" and "reservoir" files won't need any further post processing. They already contain the geospatial metadata needed for quick display. The "channel_rt" files will still need to be post processed as before but we have updated the post processing script: ftp://ftp.nohrsc.noaa.gov/pub/staff/keicher/WRFH_ppd/web/NWM_v1.1_nc_tools_v1.tar.gz
* The "station" dimension and "station_id" variable have been renamed to "feature_id"
* The analysis and assimilation product now includes the current hour and the two prior hours instead of just the current hour.
* The short range forecast will go out 18 hours instead of 15
* The medium range forecast will update every 6 hours instead of once a day
* The nwm data is now packed for most variables (i.e. stored as integers) but most netCDF libraries will unpack the data for you (automatically)


# Consistency in Output Files

As of National Water Model version 1.0 and 1.1, configurations within a given model version are the same. That means within a given version these parameters will be consistent across all output files even for different simulation runs.

* The order of feature identifiers
* File, variable, and attribute naming conventions
* Simulation run times each day

For version 1.1, these items are also consistent:

* 1970-01-01 00:00 in the time units
* 0.01 scale factor for streamflow

Note that across different versions, you should not assume things are the same. For example, the feature identifer order is different between v1.0 and v1.1.