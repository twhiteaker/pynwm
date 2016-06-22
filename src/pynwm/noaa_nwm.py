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
_root_folder = '/pub/data/nccf/com/nwm/para'


def get_latest_analysis_filename():
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
