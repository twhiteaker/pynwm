#!/usr/bin/python2
"""Accesses National Water Model streamflow results directly from NOAA.

NOAA provides National Water Model results on their NCEP FTP server. These
model result files do not include geospatial coordinates, so they are smaller
than the equivalent files from the HydroShare archive. They are also typically
more current than what's on HydroShare by an hour or two. However, NOAA does
not keep files available for more than two days, nor does NOAA provide time
series retrieval functionality, so this script is most useful if you want the
latest model results for a given time stamp across several river features.
"""

from ftplib import FTP
import os
import gzip
import urllib

_ftp_url = 'ftpprd.ncep.noaa.gov'
_root_folder = '/pub/data/nccf/com/nwm/prod/'
_long_range_products = ['long_range_mem1', 'long_range_mem2',
                        'long_range_mem3', 'long_range_mem4']
_all_products = (['analysis_assim', 'short_range', 'medium_range'] +
                 _long_range_products)


def get_datefolders():
    """Returns a list of available folders from NOAA's FTP server.

    Returns a list of available folders (named by forecast simulation date)
    from NOAA's FTP server.

    Returns:
        List of folder names, e.g., ['nwm.20160927', 'nwm.20160928']
    """

    ftp = FTP(_ftp_url)
    ftp.login()
    ftp.cwd(_root_folder)
    return sorted(ftp.nlst())


def list_files(datefolders=None, products=None):
    """Returns model result filenames for the given dates and products.

    Returns model result filenames for the given forecast dates and products
    from NOAA's FTP server.  Only 'channel' filenames are returned.

    Args:
        datefolders: (Optional) List of datefolders or string of a single
            date folder to crawl, e.g., ['nwm.20160927', 'nwm.20160928'].
            Use get_datefolders() to get a list of available date folders. If
            not provided, all available date folders are crawled.
        products: (Optional) List of NWM products or string of a single
            product to find, e.g., ['short_range', 'medium_range']. If not
            provided, all products are returned.  If 'long_range' product is
            provided, all available long range members are returned. Valid
            values are:
                analysis_assim
                short_range
                medium_range
                long_range
                long_range_mem1
                long_range_mem2
                long_range_mem3
                long_range_mem4

    Returns:
        List of filenames including directory of available files.
    """

    if not datefolders:
        datefolders = get_datefolders()
    elif type(datefolders) is str:
        datefolders = [datefolders]
    datefolders = sorted({f.lower() for f in datefolders})
    if not products:
        products = _all_products
    elif type(products) is str:
        products = [products.lower()]
    else:
        products = {p.lower() for p in products}
    if 'long_range' in products:
        products.remove('long_range')
        products |= set(_long_range_products)
    products = [p for p in products if p in _all_products]

    ftp = FTP(_ftp_url)
    ftp.login()
    ftp.cwd(_root_folder)
    all_files = []
    for datefolder in datefolders:
        for product in products:
            folder = '{0}/{1}/{2}'.format(_root_folder, datefolder, product)
            try:
                ftp.cwd(folder)
                files = ['{0}/{1}'.format(folder, f) for f in ftp.nlst()
                         if 'channel' in f]
                all_files.extend(files)
            except Exception as ex:
                print str(ex)
            break
    return all_files


def get_latest_analysis_filename():
    """Gets name of latest analysis and assimilation file from NOAA.

    Gets name of latest analysis and assimilation file from NOAA. Filename
    includes FTP folder, e.g.,
    /pub/data/nccf/com/nwm/prod/nwm.20160928/analysis_assim/nwm.t15z.analysis_assim.channel_rt.tm00.conus.nc.gz

    Returns:
        Filename, including FTP directory, of the file.
    """

    ftp = FTP(_ftp_url)
    ftp.login()
    ftp.cwd(_root_folder)

    filename = None
    dates = ftp.nlst()
    for date in reversed(dates):
        ftp.cwd('{0}/{1}/analysis_assim'.format(_root_folder, date))
        files = [f for f in ftp.nlst() if 'channel' in f]
        if len(files):
            filename = '{0}/{1}'.format(ftp.pwd(), files[-1])
            break
    ftp.quit()
    if not filename:
        raise Exception('No channel files available')
    return filename


def get_latest_analysis_file(output_folder):
    """Downloads latest analysis and assimilation file.

    Downloads latest analysis and assimilation file to the output folder and
    unzips it.

    Args:
        output_folder: Path to the folder where the file will be saved.

    Returns:
        Filename, including directory, of the downloaded file.
    """

    uri = 'ftp://{0}/{1}'.format(_ftp_url, get_latest_analysis_filename())
    zip_filename = os.path.join(output_folder, uri.split('/')[-1])
    urllib.urlretrieve(uri, zip_filename)
    nc_filename = zip_filename[:-3]
    with gzip.open(zip_filename, 'rb') as zipped:
        with open(nc_filename, 'wb') as unzipped:
            unzipped.write(zipped.read())
    os.remove(zip_filename)
    return nc_filename
