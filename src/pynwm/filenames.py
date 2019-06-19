#!/usr/bin/python2
"""Utilities related to National Water Model filenames."""

import collections
import re

import pynwm.constants as constants


def product_from_filename(filename):
    """Extracts the product type from the filename.

    E.g., from 'nwm.t00z.long_range.channel_rt_1.f006.conus.nc',
    return 'long_range_mem1'.

    Args:
        filename: The simulation result filename

    Returns:
        Product name, e.g., 'short_range'
    """

    pattern = r'(?<=z.)([\w]+)'  # Finds between 'z.' and next '.'
    product = re.search(pattern, filename).group(0)
    if product == 'long_range':
        pattern = r'(?<=channel_rt_)([\d])'
        member_number = re.search(pattern, filename).group(0)
        product += '_mem' + member_number
    return product


def hour_from_filename(filename):
    """Extracts the hour the simulation was run from the filename.

    E.g., from 'nwm.t06z.long_range.channel_rt_1.f006.conus.nc',
    return 't06z'.

    Args:
        filename: The simulation result filename

    Returns:
        String for the hour the simulation was run, e.g., 't06z'
    """

    pattern = r'(?<=\.)(t[\d]{2}z)'  # Finds, e.g., t06z
    hour = re.search(pattern, filename).group(0)
    return hour


def is_sim_complete(sim):
    """Checks that file count matches expected number of time steps.

    Args:
        sim: Simulation dictionary with these items:
            product: The product, e.g., 'short_range'
            date: Simulation date, e.g., '20170401t06-00'
            files: List of files in the simulation

    Returns:
        True if all expected files are listed; False otherwise.
    """

    product = sim['product']
    if sim['date'] >= constants.V1_1_DATE:
        expected_steps = constants.PRODUCTSv1_1[product]['steps']
    else:
        expected_steps = constants.PRODUCTSv1_0[product]['steps']
    return (len(sim['files']) == expected_steps)


def group_simulations(filenames, yyyymmdd, links=None):
    """Group files into dictionaries representing simulations.

    A given simulation dictionary describes the product type,
    simulation date, and whether all expected files are present,
    and includes a list of filenames, e.g.
    {'product': 'long_range_mem1',
     'date': '20170401t06-00',
     'is_complete': True,
     'files': ['nwm...f006.conus.nc', 'nwm...f012.conus.nc', ...]
     'links': ['http...', ...]}

     Args:
         filenames: List of filenames to be grouped.
         yyyymmdd: String date of the simulation. This is required
             since the date is not included in the filename.
         links: (Optional) List of links to download each file.

    Returns:
        An ordered dictionary of simulation dictionaries, indexed by
        product and date, e.g., 'long_range_mem1_20170401t06-00'
    """

    if type(yyyymmdd) is not str:
        yyyymmdd = str(yyyymmdd)
    sims = {}
    for index, f in enumerate(filenames):
        product = product_from_filename(f)
        hour = hour_from_filename(f)
        date = yyyymmdd + hour.replace('z', '-00')  # for date parsing
        key = product + '_' + date
        if key in sims:
            sim = sims[key]
        else:
            sim = {'product': product,
                   'date': date,
                   'is_complete': False,
                   'files': [],
                   'links': []}
            sims[key] = sim
        sim['files'].append(f)
        if links:
            sim['links'].append(links[index])
    for key, sim in sims.iteritems():
        sim['is_complete'] = is_sim_complete(sim)
    sims = collections.OrderedDict(sorted(sims.items()))
    return sims
