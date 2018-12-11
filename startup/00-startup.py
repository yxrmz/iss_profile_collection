import time
t1 = time.time()
# Make ophyd listen to pyepics.
from ophyd import setup_ophyd
# setup_ophyd()

# Set up a RunEngine and use metadata backed by a sqlite file.
from bluesky import RunEngine
from bluesky.utils import get_history
RE = RunEngine({})

# Set up a Broker.
from databroker import Broker
db = Broker.named('iss')
db_analysis = Broker.named('iss-analysis')

# Subscribe metadatastore to documents.
# If this is removed, data is not saved to metadatastore.
RE.subscribe(db.insert)

# Set up SupplementalData.
from bluesky import SupplementalData
sd = SupplementalData()
RE.preprocessors.append(sd)

# Add a progress bar.
from timeit import default_timer as timer


from bluesky.utils import ProgressBarManager
pbar_manager = ProgressBarManager()
#RE.waiting_hook = pbar_manager

# Register bluesky IPython magics.
from bluesky.magics import BlueskyMagics
get_ipython().register_magics(BlueskyMagics)

# Set up the BestEffortCallback.
from bluesky.callbacks.best_effort import BestEffortCallback
bec = BestEffortCallback()
bec.disable_plots()
bec.disable_table()
RE.subscribe(bec)
peaks = bec.peaks  # just as alias for less typing

# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved
# RE.subscribe(post_run(verify_files_saved), 'stop')

# Import matplotlib and put it in interactive mode.
#import matplotlib.pyplot as plt
#plt.ion()

# Make plots update live while scans run.
from bluesky.utils import install_qt_kicker
install_qt_kicker()

# Optional: set any metadata that rarely changes.
# RE.md['beamline_id'] = 'YOUR_BEAMLINE_HERE'

# convenience imports
from bluesky.callbacks import *
from bluesky.callbacks.broker import *
from bluesky.simulators import *
from bluesky.plans import *
import numpy as np

from pyOlog.ophyd_tools import *

# Uncomment the following lines to turn on verbose messages for
# debugging.
# import logging
# ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


from pathlib import Path
from historydict import HistoryDict

try:
    RE.md = HistoryDict('/nsls2/xf08id/metadata/bluesky_history.db')
    print('gpfs')
except Exception as exc:
    print('local')
    print(exc)
    RE.md = HistoryDict('{}/.config/bluesky/bluesky_history.db'.format(str(Path.home())))
RE.is_aborted = False

#mds = MDS({'host': 'xf08id-ca1.cs.nsls2.local', 'port': 7770,'timezone': 'US/Eastern'})

#db = Broker(mds, FileStore({'host':'xf08id-ca1.cs.nsls2.local', 'port': 27017, 'database':'filestore'}))



# register_builtin_handlers(db.fs)
start = timer()

def ensure_proposal_id(md):
    if 'proposal_id' not in md:
        raise ValueError("You forgot the proposal_id.")

# Set up default metadata.
RE.md['group'] = 'iss'
RE.md['beamline_id'] = 'ISS'
RE.md['proposal_id'] = None
#RE.md['proposal_id'] = None
stop2 = timer()
RE.md_validator = ensure_proposal_id
stop = timer()

print("MD handling complete in {} sec".format(stop - start))


# the file paths for acquitision and analysis
ROOT_PATH = '/nsls2/xf08id'
RAW_FILEPATH = 'data'
USER_FILEPATH = 'users'



