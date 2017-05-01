#!/usr/bin/python2
"""Identifies the latest National Water Model files in HydroShare."""

from hs_list import list_sims, list_dates


def _find_complete_sim(sims):
    for key in reversed(sims):
        sim = sims[key]
        if sim['is_complete']:
            return (key, sim)
    return (None, None)


def find_latest_simulation(product):
    """Identifies files for the most recent complete simulation.

    As files arrive at HydroShare from NOAA, a folder for the forecast
    date is created although all files may have not yet arrived from
    NOAA. This function checks that all files for the simulation are
    present before returning details of that simulation.

    Each simulation is represented as a dictionary describing product
    type, simulation date, and whether all expected files are present,
    and it also includes a list of filenames, e.g.
    {'product': 'long_range_mem1',
     'date': '20170401t06-00',
     'is_complete': True,
     'files': ['nwm...f006.conus.nc', 'nwm...f012.conus.nc', ...],
     'links': ['http...', ...]}

    Args:
        product: String product name, e.g., 'short_range'.

    Returns:
        An ordered dictionary of simulation dictionaries, indexed by
        product and date, e.g., 'long_range_mem1_20170401t06-00', or
        empty dictionary if no complete simulations found.
    """

    sims = {}
    if product == 'analysis_assim':
        # Warning: This may change with NWM v1.1 since assim has 3 files, not one
        all_sims = list_sims(product)
        key, sim = _find_complete_sim(all_sims)
        if key:
            sims[key] = sim
    else:
        dates = reversed(list_dates(product))
        for date in dates:
            date_sims = list_sims(product, date)
            if product == 'long_range' and len(date_sims) == 16:
                is_complete = True
                for key, sim in date_sims.iteritems():
                    if not sim['is_complete']:
                        is_complete = False
                        break
                if is_complete:
                    sims = date_sims
                    break
            elif product != 'long_range':
                key, sim = _find_complete_sim(date_sims)
                if key:
                    sims[key] = sim
                    break
    return sims
