# pynwm
A Python client for consuming National Water Model forecasts

pynwm includes Python scripts for accessing modeled streamflow in roughly 2.7 million river reaches in the conterminous U.S. from the National Weather Service's [National Water Model](http://water.noaa.gov/about/nwm). Use pynwm to see what files are available, query streamflow from downloaded files, subset files from a set of river identifiers, and merge files for individual time steps into a single file.

The National Water Model includes four products:

1. Analysis and assimilation: 1-hour snapshot
2. Short-Range: 18-hour deterministic (single value) forecast
3. Medium-Range: 10-day deterministic (single value) forecast
4. Long-Range: 30-day ensemble forecast

**Example:**

```python
# Find links to download the latest forecast files
from pynwm.noaa import noaa_latest
result = noaa_latest.find_latest_simulation('short_range')
msg = 'Date: {0}\nFile Count: {1}\nFirst download link: {2}'
print(msg.format(result['date'], len(result['files']), result['links'][0]))
```

# Installation and Usage

pynwm requires Python 2.7 and the following packages:

* netcdf4-python
* python-dateutil
* pytz

To use pynwm, just drop the `src/pynwm` folder next to your script and import the modules you need. See the `Examples` folder for example usage.

You ask for data for a given river using its identifier, which is the COMID from the [National Hydrography Dataset](http://www.horizon-systems.com/NHDPlus/index.php) within CONUS and arbitrary identifiers outside CONUS. To find COMIDs for rivers in your study area, you can view the NHDFlowline shapefile within the "NHDSnapshot" zip file on the NHDPlus download page for your region ([example](http://www.horizon-systems.com/NHDPlus/NHDPlusV2_12.php)), or programmatically find neaby river reaches using the [EPA WATERS Web Services](https://www.epa.gov/waterdata/waters-web-services).

The model files themselves are in netCDF format and include streamflow for all rivers at a single time step, e.g., 16:00 on June 1, 2016. All timestamps are in [UTC time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time).

## Extract Streamflow for Rivers of Interest

A single model file includes data at a single timestamp for roughly 2.7 million locations. To extract data for just the rivers in your study area from a downloaded model result file, supply a list of identifiers for those rivers. This is useful for getting a snapshot of conditions at a given date and time across all rivers in your study area.

```python
from pynwm import nwm_data
comids = [5671187, 5670795]
result = nwm_data.read_streamflow(netcdf_filename, comids)
print('ID {0}: {1} cms at {2}'.format(comids[0], 
                                      result['flows'][0],
                                      result['datetime'][0]))
```

If you want to save a subset of the data for your rivers for later use, supply an output filename.

```python
from pynwm import nwm_subset
comids = [5671187, 5670795]
nwm_subset.subset_channel_file(original_file, destination_file, comids)
```

If you have several files for a given forecast and want to combine them, supply a list of files.

```python
from pynwm import nwm_subset
file_pattern = 'nwm.t00z.short_range.channel_rt.f0{0:02d}.conus.nc'
files = [file_pattern.format(i + 1) for i in range(18)]  # 18 files in short range forecast
comids = [5671187, 5670795]
nwm_subset.combine_files(files, 'combined.nc', comids)
```

## HydroShare Access

The HydroShare subpackage within pynwm provides access to [HydroShare's](https://www.hydroshare.org/) recent archives of model results, their [API](https://apps.hydroshare.org/apps/nwm-data-explorer/api/) for querying the archive, and services supporting their [Viewer](https://apps.hydroshare.org/apps/nwm-forecasts/) and [File Explorer](https://apps.hydroshare.org/apps/nwm-data-explorer/) apps. In addition to accessing archived simulation results, you can also query for a streamflow time series directly from HydroShare without having to first download model result files.

**Example:**

```python
from pynwm.hydroshare import hs_retrieve
comid = 5671187  # Brushy Creek in Round Rock, Texas
product = 'medium_range'
series = hs_retrieve.get_latest_forecasted_streamflow(product, comid)
for s in series:
    for i, streamflow in enumerate(s['values']):
        print('{0} \t {1} cfs'.format(s['dates'][i], streamflow))
```

For more HydroShare examples, see https://github.com/twhiteaker/pynwm/tree/master/src/pynwm/hydroshare.

# What About the Rest of the Data?

In addition to streamflow forecasts, the National Water Model also produces files describing inputs into the streamflow calculation such as soil moisture and precipitation. I only targeted streamflow in pynwm since that fits my own needs. If you have a need for something more than streamflow, I welcome you to fork and contribute!
