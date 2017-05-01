#!/usr/bin/python2
"""Downloads forecasted streamflow for rivers of interest.

This script downloads forecasted streamflow for rivers of interest. Run
as a scheduled task or cron job to keep your database current.
"""

import gzip
import json
import os
import tempfile
from urllib import urlretrieve

from netCDF4 import Dataset
import numpy as np

from pynwm.noaa import noaa_latest
from pynwm.nwm_data import get_schema
from pynwm.nwm_subset import combine_files


def _unzip(filename):
    """If zip file, unzips and deletes the zip."""

    if filename[-3:] == '.gz':
        tmpdir = tempfile.gettempdir()
        nc_file = os.path.join(tmpdir, os.path.basename(filename[:-3]))
        with gzip.open(filename, 'rb') as z, open(nc_file, 'wb') as uz:
            uz.write(z.read())
        os.remove(filename)
        return nc_file
    else:
        return filename


def _add_max_q(nc_filename):
    """Adds a variable storing maximum streamflow for each river."""

    with Dataset(nc_filename, 'a') as nc:
        schema = get_schema(nc)
        streamflow_var = nc.variables['streamflow']
        max_q = np.amax(streamflow_var[:], axis=0)
        var = nc.createVariable('max_streamflow', 'i', (schema['id_dim'],))
        var.long_name = 'Maximum River Flow'
        var.units = streamflow_var.units
        var.scale_factor = 0.01
        var.add_offset = 0.0
        var[:] = max_q

    
def main():
    # Config tells us what we want and where to put it
    with open('config.json') as f:
        cfg = json.load(f)
    with open(cfg['river_id_file']) as f:
        ids = [x.strip() for x in f.readlines()]
    output_folder = cfg['output_folder']
    product = cfg['product']
    existing_files = [f for f in os.listdir(output_folder)
                      if f.endswith('.nc')]
    current_files = []
    tmpdir = tempfile.gettempdir()

    # Get the latest simulation. 'long_range' may have more than one.
    sims = noaa_latest.find_latest_simulation(product)
    for key, sim in sims.iteritems():
        filename = key + '.nc'
        if filename in existing_files:
            print(filename + ' is current.')
            current_files.append(filename)
        else:
            # We don't have it yet. Download, subset and merge files.
            print('\nRetrieving files to build ' + filename)
            dl_files = []
            for index, nwm_file in enumerate(sim['files']):
                dl_file = os.path.join(tmpdir, nwm_file)
                print('Downloading ' + nwm_file)
                urlretrieve(sim['links'][index], dl_file)
                nc_file = _unzip(dl_file)
                dl_files.append(nc_file)
            print('Building cube')
            filepath = os.path.join(output_folder, filename)
            combine_files(dl_files, filepath, ids)
            # Max streamflow can be useful to quickly identify floods
            _add_max_q(filepath)
            current_files.append(filepath)
            # With our subset, now we don't need the downloaded files
            for nc_file in dl_files:
                os.remove(nc_file)
    if current_files:
        # Delete obsolete files. You may want to archive or manage differently.
        old_files = [x for x in existing_files if x not in current_files]
        for old_file in old_files:
            filename = os.path.join(output_folder, old_file)
            if os.path.isfile(filename):
                os.remove(filename)
    print('\nFinished')


if __name__ == '__main__':
    main()
