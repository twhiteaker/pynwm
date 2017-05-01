#!/usr/bin/python2
"""Lists available National Water Model files from NOAA."""

import collections
from ftplib import FTP, error_perm
import re

from pynwm.constants import PRODUCTSv1_1
from pynwm.filenames import group_simulations

_FTP_URI = 'ftpprd.ncep.noaa.gov'
_FTP_ROOT = '/pub/data/nccf/com/nwm/prod/'


def _connect():
    ftp = FTP(_FTP_URI)
    ftp.login()
    ftp.cwd(_FTP_ROOT)
    return ftp

    
def _datefolder(yyyymmdd):
    return 'nwm.' + str(yyyymmdd)


def list_dates(product=None):
    """Lists available dates in yyyymmdd format.

    If no product is supplied, a folder for any product counts. If
    product is 'long_range', any long range member counts.

    Args:
        product: (Optional) String indicating product.

    Returns:
        Sorted list of dates in yyyymmdd format.
    """

    ftp = _connect()
    folders = ftp.nlst()
    if product:
        dates = []
        for date_folder in folders:
            folder = '{0}/{1}'.format(_FTP_ROOT, date_folder)
            ftp.cwd(folder)
            for available_product in ftp.nlst():
                if product in available_product:
                    dates.append(re.findall('\d{8}', date_folder)[0])
        dates = list(set(dates))
    else:
        dates = [re.findall('\d{8}', f)[0] for f in folders]
    return sorted(dates)


def _list_files(ftp, product, yyyymmdd):
    files = []
    links = []
    datefolder = _datefolder(yyyymmdd)
    folder = '{0}{1}/{2}'.format(_FTP_ROOT, datefolder, product)
    try:
        ftp.cwd(folder)
        links = ['ftp://{0}{1}/{2}'.format(_FTP_URI, folder, f)
                 for f in ftp.nlst() if 'channel' in f]
        files = [re.findall('nwm\.t.+', f)[0] for f in links]
    except error_perm as ex:
        template = 'Warning: {0} -- {1} product may not be available for {2}'
        print(template.format(ex, product, yyyymmdd))
    except Exception as ex:
        raise
    return files, links


def _add_links(sims, links):
    for key, sim in sims.iteritems():
        sim['links'] = [HS_URI + 'api/GetFile?file={0}'.format(f)
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
    ftp = _connect()
    for date in dates:
        for product in products:
            files, links = _list_files(ftp, product, yyyymmdd)
            sims = group_simulations(files, date, links)
            all_sims.update(sims)
    all_sims = collections.OrderedDict(sorted(all_sims.items()))
    return all_sims
