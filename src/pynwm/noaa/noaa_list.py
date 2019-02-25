#!/usr/bin/python2
"""Lists available National Water Model files from NOAA."""

import collections
import re
import urllib2

from bs4 import BeautifulSoup

from pynwm.constants import PRODUCTSv1_1
from pynwm.filenames import group_simulations

_URI_ROOT = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/'


def _get_links(uri):
    f = urllib2.urlopen(uri)
    soup = BeautifulSoup(f.read(), 'html.parser')
    links = [a.get('href') for a in soup.find_all('a')
             if a.text[:6] != 'Parent']
    return links

    
def list_dates(product=None):
    """Lists available dates in yyyymmdd format.

    If no product is supplied, a folder for any product counts. If
    product is 'long_range', any long range member counts.

    Args:
        product: (Optional) String indicating product.

    Returns:
        Sorted list of dates in yyyymmdd format.
    """

    date_folders = _get_links(_URI_ROOT)
    if product:
        dates = []
        for date_folder in date_folders:
            uri = '{0}/{1}'.format(_URI_ROOT, date_folder)
            products = [p[:-1] for p in _get_links(uri)]  # remove slash
            for available_product in products:
                if product in available_product:
                    dates.append(re.findall('\d{8}', date_folder)[0])
        dates = list(set(dates))
    else:
        dates = [re.findall('\d{8}', d)[0] for d in date_folders]
    return sorted(dates)


def _list_files(product, yyyymmdd):
    files = []
    links = []
    datefolder = 'nwm.' + str(yyyymmdd)
    uri = '{0}{1}/{2}/'.format(_URI_ROOT, datefolder, product)
    try:
        matches = [m for m in _get_links(uri) if 'channel' in m]
        links = ['{0}{1}'.format(uri, m) for m in matches]
        files = [re.findall('nwm\.t.+', f)[0] for f in links]
    except urllib2.HTTPError as ex:
        if ex.code == 404:
            msg = 'Warning: {0} -- {1} product may not be available for {2}'
            print(msg.format(ex, product, yyyymmdd))
        else:
            raise
    except Exception as ex:
        raise
    return files, links


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
        yyyymmdd: String date of the simulation in yyyymmdd format.
            If None, then all available dates are used.

    Returns:
        An ordered dictionary of simulation dictionaries, indexed by
        product and date, e.g., 'long_range_mem1_20170401t06-00'
    """

    dates = [yyyymmdd] if yyyymmdd else list_dates()
    if product == 'long_range':
        products = [k for k in PRODUCTSv1_1 if 'long_range' in k]
    else:
        products = [product] if product else [k for k in PRODUCTSv1_1]
    all_sims = {}
    for date in dates:
        for product in products:
            files, links = _list_files(product, yyyymmdd)
            sims = group_simulations(files, date, links)
            all_sims.update(sims)
    all_sims = collections.OrderedDict(sorted(all_sims.items()))
    return all_sims
