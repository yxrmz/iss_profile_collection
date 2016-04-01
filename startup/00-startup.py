import logging

from ophyd.commands import *


from databroker import DataBroker as db, get_events, get_images, get_table

import bluesky.qt_kicker  # make matplotlib qt backend play nice with bluesky asyncio

import asyncio
from functools import partial
from functools import partial
from bluesky.standard_config import *
from bluesky.global_state import abort, stop, resume, all_is_well, panic
from bluesky.plans import *
from bluesky.callbacks import *
from bluesky.broker_callbacks import *
from bluesky.scientific_callbacks import plot_peak_stats
from bluesky import qt_kicker   # provides the libraries for live plotting
qt_kicker.install_qt_kicker()    # installs the live plotting libraries
setup_ophyd()

# Set up default metadata.
gs.RE.md['group'] = 'iss'
gs.RE.md['beamline_id'] = 'ISS'


# alias
RE = gs.RE


# Set up the logbook.
LOGBOOKS = ['Data Acquisition']
import bluesky.callbacks.olog
from pyOlog import SimpleOlogClient
simple_olog_client = SimpleOlogClient()
generic_logbook_func = simple_olog_client.log
configured_logbook_func = partial(generic_logbook_func, logbooks=LOGBOOKS)

from bluesky.callbacks.olog import logbook_cb_factory
cb = logbook_cb_factory(configured_logbook_func)
RE.subscribe('start', cb)

logbook = simple_olog_client  # this is for ophyd.commands.get_logbook

# Turn off "noisy" debugging.
loop = asyncio.get_event_loop()
loop.set_debug(False)
