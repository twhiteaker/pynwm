The scripts in pynwm's `hydroshare` package provide an interface into HydroShare's National Water Model API.

HydroShare is a National Science Foundation funded project which provides a number of services to the hydrologic sciences community, including archiving and providing access to National Water Model (NWM) results.  HydroShare stores a rolling archive of model results due to size limitations, so the start date of available results changes over time. Forecast products are available for a couple of weeks, while the analysis and assimilation product archive extends for many months.

In addition to archive access, another HydroShare feature is the ability to return a streamflow time series for a given river feature. If you just want time series for a few rivers, you may find it much more convenient to get the time series from HydroShare rather than to download result files for the entire nation and parse out data for just your rivers of interest.

HydroShare includes an API for accessing data and a couple of demonstration apps. The API is described at https://apps.hydroshare.org/apps/nwm-data-explorer/api/.  HydroShare attempts to add value to the model product by adding latitude and longitude coordinates as variables within each model file. The increases file size, but enables the file to be displayed in common netCDF viewing software. During this process, NWM v1.0 files are converted from NetCDF-3 format to NetCDF-4 format.

In addition to documented API methods, the HydroShare API includes a couple of hidden methods used by the demonstration apps. The apps include a time series viewer and a file explorer, available at (respectively):
https://apps.hydroshare.org/apps/nwm-forecasts/
https://appsdev.hydroshare.org/apps/nwm-data-explorer/

HydroShare organizes its data a bit differently from how NOAA does it. For example, all four long range ensemble members are generally grouped together. Therefore, access to data may differ from patterns used to retrieve data directly from NOAA. For example, instead of specifying an individual `long_range_mem1` product, use `long_range` to get all members instead.

# Examples

## See What's Available

This queries for available date folders in HydroShare. Note that sometimes older folders are empty, so consider this to be a list of possible dates for which files are available. Determining which folders are empty is a more expensive operation so we don't do that here.

```python
from pprint import pprint
from pynwm.hydroshare import hs_list
product = 'medium_range'
dates = hs_list.list_dates(product)
pprint(dates)  # in yyyymmdd format
```

Find simulation results in a given folder:

```python
from pynwm.hydroshare import hs_list
product = 'long_range'
dates = hs_list.list_dates(product)
date = dates[-3]  # a recent date
simulation_results = hs_list.list_sims(product, date)
print(len(simulation_results))  # 16 ensemble members
for key, sim in simulation_results.iteritems():
    print(sim['product'])  # For long range, indicates ensemble member
    print(sim['date'])  # Valid date for the entire simulation
sim = simulation_results[key]
print(len(sim['files']))  # One file per time step
print(sim['is_complete'])  # True if HydroShare got all files from NOAA
print(sim['files'][0])  # Filename as stored in HydroShare
print(sim['links'][0])  # Link to download the file
```

Find the latest complete simulation results:

```python
from pynwm.hydroshare import hs_latest
product = 'short_range'
simulation_results = hs_latest.find_latest_simulation(product)
for key, sim in simulation_results.iteritems():
    print(sim['date'])  # Valid date for the entire simulation
    print(sim['is_complete'])  # True if HydroShare got all files from NOAA
```

## Download Time Series

Assemble a time series from several months ago from the analysis and assimilation product:

```python
from datetime import datetime, timedelta
from pynwm.hydroshare import hs_retrieve
now = datetime.now()
start_date = now - timedelta(days=90)
end_date = now - timedelta(days=60)
feature_id = 5671187
series = hs_retrieve.get_analysis_streamflow(feature_id, start_date, end_date)
print(len(series))  # Ensembles would have more than one
dates = series[0]['dates']
print(len(dates))
# HydroShare converts streamflow units to cubic feet per second
streamflow_cfs = series[0]['values']
print_me = '{0}\t{1}'
for i in range(5):
    print(print_me.format(dates[i], streamflow_cfs[i]))
```

Get the latest short range forecast:

```python
from pynwm.hydroshare import hs_retrieve
product = 'short_range'
feature_id = 5671187
series = hs_retrieve.get_latest_forecasted_streamflow(product, feature_id)
dates = series[0]['dates']
print(len(dates))
streamflow_cfs = series[0]['values']
print_me = '{0}\t{1}'
for i in range(5):
    print(print_me.format(dates[i], streamflow_cfs[i]))

```
