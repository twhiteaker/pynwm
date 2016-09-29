# pynwm
A Python client for consuming National Water Model forecasts

pynwm includes Python scripts for accessing modeled streamflow in roughly 2.7 million river reaches in the conterminous U.S. from the National Weather Service's [National Water Model](http://water.noaa.gov/about/nwm). Access is enhanced
by using [HydroShare's](https://www.hydroshare.org/) recent archives of model results, their
[API](https://apps.hydroshare.org/apps/nwm-data-explorer/api/) for querying the archive, and services supporting their [Viewer](https://apps.hydroshare.org/apps/nwm-forecasts/) and [File Explorer](https://apps.hydroshare.org/apps/nwm-data-explorer/) apps. Use pynwm to download a time series of recent or forecasted streamflow, download result files, or extract a subset of data from a given file.

The National Water Model includes four products:

1. Analysis and assimilation: 1-hour snapshot
2. Short-Range: 18-hour deterministic (single value) forecast
3. Medium-Range: 10-day deterministic (single value) forecast
4. Long-Range: 30-day ensemble forecast

The model uses COMID identifiers from the [National Hydrography Dataset](http://www.horizon-systems.com/NHDPlus/index.php) to index data for each river reach.

**Example:**

```python
from pynwm import nwm
comid = 5671187  # Brushy Creek in Round Rock, Texas
model_product = 'long_range'  # 16-member 30-day ensemble forecast
series = nwm.get_streamflow(model_product, comid)
for s in series:
    for i, streamflow_value in enumerate(s['values']):
        print('{0} \t {1} cfs'.format(s['dates'][i], streamflow_value))
```

# Installation and Usage

pynwm requires Python 2.7 and the following packages:

* netcdf4-python
* python-dateutil
* pytz

To use pynwm, just drop the `pynwm` folder with `nwm.py` and `__init__.py` next to your script and import it with:

```python
from pynwm import nwm
```

You ask for data for a given river using its COMID. To find COMIDs for rivers in your study area, you can view the NHDFlowline shapefile within the "NHDSnapshot" zip file on the NHDPlus download page for your region ([example](http://www.horizon-systems.com/NHDPlus/NHDPlusV2_12.php)), or programmatically find neaby river reaches using the [EPA WATERS Web Services](https://www.epa.gov/waterdata/waters-web-services).

The model files themselves include streamflow for all rivers at a single time step, e.g., 16:00 on June 1, 2016, with each file typically being a few dozen megabytes in size. All timestamps are in [UTC time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time).

## Download Streamflow Time Series for a River Feature

You can download a time series of streamflow values for a single COMID from HydroShare.  Simply provide a COMID and a model product to get all available historical results (analysis and assimilation product) or the most recent forecast (all forecast products).

```python
series = nwm.get_streamflow('short_range', 5671187)
```

To see how well the model predicted a recent storm, supply the date and UTC time for the historical model run. The HydroShare archive is a rolling archive, so you may want to check their [File Explorer app](https://apps.hydroshare.org/apps/nwm-data-explorer/) to see what's available first.

```python
series = nwm.get_streamflow('short_range', 5671187, sim_datetime_utc='2016-06-21 06:00')
```

To have timestamps in the results converted from UTC to a different time zone, supply a [time zone name recognized by pytz](http://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones).

```python
series = nwm.get_streamflow('short_range', 5671187, timezone='US/Central')
```

## Download Latest Analysis and Assimilation File

To get the latest analysis and assimilation file, supply an output folder where the file will be saved. 

```python
filename = nwm.get_latest_analysis_file('output_folder')
```

## Extract Streamflow for Rivers of Interest

A single model file includes data at a single timestamp for roughly 2.7 million locations. To extract data for just the rivers in your study area from a downloaded model result file, supply a list of COMIDs for those rivers. This is useful for getting a snapshot of conditions at a given date and time across all rivers in your study area.

```python
comids = [5671187, 5670795]
result = nwm.read_q_for_comids(model_file, comids)
```

If you want to save a subset of the data for your rivers for later use, supply an output filename.

```python
comids = [5671187, 5670795]
nwm.subset_channel_file(original_model_file, subsetted_model_file, comids)
```

If you have several files for a given forecast and want to combine them, supply a list of files.

```python
file_pattern = 'nwm.t00z.short_range.channel_rt.f00{0}.conus.nc.gz'
files = [file_pattern.format(i + 1) for i in range(15)]  # 15 files in short range forecast
comids = [5671187, 5670795]
nwm.combine_files(files, 'combined.nc', comids)
```

# What About the Rest of the Data?

In addition to streamflow forecasts, the National Water Model also produces files describing inputs into the streamflow calculation such as soil moisture and precipitation. I only targeted streamflow in pynwm since that fits my own needs. The scripts could be modified to include variable names (e.g., `precipitation`), and the  HydroShare API already supports this. If you have a need for something more than streamflow, I welcome you to fork and contribute!
