#!/usr/bin/python2
"""Lists available National Water Model files in HydroShare."""

import collections
import datetime
import json
import re
from urllib import urlopen

from dateutil import parser as date_parser

from pynwm.filenames import group_simulations
from hs_constants import HS_DATA_EXPLORER_URI


def _date_to_start_date_arg(date):
    start_date = ''
    if date:
        date = date_parser.parse(str(date)).strftime('%Y-%m-%d')
        start_date = '&startDate=' + date
    return start_date


def _product_to_member_arg(product):
    matches = re.findall('\d', product)
    member = '&member=' + matches[0] if matches else ''
    return member


def _date_from_filename(filename):
    date = re.findall('\d{8}', filename)[0]
    return date


def _list_files(product, date=None):
    """Lists available files for the product and date.

    Args:
        product: String name of product, e.g., 'short_range'.
        date: (Optional) Simulation run date as string or date object.
            Ignored if product is analysis_assim; required otherwise.

    Returns:
        List of files.
    """

    config = 'long_range' if 'long_range' in product else product
    member = _product_to_member_arg(product)
    date = _date_to_start_date_arg(date)
    template = 'api/GetFileList/?config={config}&geom=channel{date}{member}'
    args = template.format(config=config, date=date, member=member)
    uri = HS_DATA_EXPLORER_URI + args
    response = urlopen(uri).read()
    files = json.loads(response)
    if not isinstance(files, list):
        return []
    if product == 'analysis_assim' and date != '':
        yyyymmdd = re.findall('\d{4}-\d{2}-\d{2}', date)[0]
        yyyymmdd = yyyymmdd.replace('-', '')
        files = [f for f in files if _date_from_filename(f) == yyyymmdd]
    return files


def list_dates(product):
    """Lists dates available for a product.

    HydroShare groups long range files together, so providing
    'long_range' as the product returns files for all long range
    ensemble members.

    Args:
        product: String name of product, e.g., 'short_range'.

    Returns:
        List of string dates in yyyymmdd format.
    """

    if product == 'analysis_assim':
        files = _list_files(product)
        dates = []
        for f in files:
            date = _date_from_filename(f)
            dates.append(date)
        dates = list(set(dates))  # Get unique dates
    else:
        template = (HS_DATA_EXPLORER_URI + 'files_explorer/get-folder-contents'
                    '/?selection_path=%2Fprojects%2Fwater%2Fnwm%2Fdata%2F{0}'
                    '%3Ffolder&query_type=filesystem')
        if 'long_range' in product:
            product = 'long_range'
        uri = template.format(product)
        response = urlopen(uri).read()
        dates = re.findall(r'\>([0-9]+)\<', response)
    return sorted(dates)


def _group_by_date(filenames):
    groups = {}
    for f in filenames:
        date = _date_from_filename(f)
        if date not in groups:
            groups[date] = []
        groups[date].append(f)
    return groups


def _add_links(sims):
    for key, sim in sims.iteritems():
        sim['links'] = [HS_DATA_EXPLORER_URI + 'api/GetFile?file={0}'.format(f)
                        for f in sim['files']]


def list_sims(product=None, yyyymmdd=None):
    """List available simulation results.

    Each simulation is represented as a dictionary describing product
    type, simulation date, and whether all expected files are present,
    and it also includes a list of filenames, e.g.
    {'product': 'long_range_mem1',
     'date': '20170401t06-00',
     'is_complete': True,
     'files': ['nwm...f006.conus.nc', 'nwm...f012.conus.nc', ...],
     'links': ['http...', ...]}

    Args:
        product: (Optional) String product name, e.g., 'short_range'.
            If None, then all products are returned.
        yyyymmdd: String date of the simulation. If None, then all
            available dates are used.

    Returns:
        An ordered dictionary of simulation dictionaries, indexed by
        product and date, e.g., 'long_range_mem1_20170401t06-00'
    """

    if yyyymmdd is not None and type(yyyymmdd) is not str:
        yyyymmdd = str(yyyymmdd)

    sims = {}
    if product is None:
        products = ['analysis_assim', 'short_range', 'medium_range',
                    'long_range']
        for p in products:
            product_sims = list_sims(p, yyyymmdd)
            sims.update(product_sims)
    elif product == 'analysis_assim':
        all_files = _list_files(product, yyyymmdd)
        groups = _group_by_date(all_files)
        for date, files in groups.iteritems():
            date_sims = group_simulations(files, date)
            _add_links(date_sims)
            sims.update(date_sims)
    elif yyyymmdd is None:
        dates = list_dates(product)
        for date in dates:
            date_sims = list_sims(product, date)
            sims.update(date_sims)
    else:
        files = _list_files(product, yyyymmdd)
        sims = group_simulations(files, yyyymmdd)
        _add_links(sims)
    sims = collections.OrderedDict(sorted(sims.items()))
    return sims
