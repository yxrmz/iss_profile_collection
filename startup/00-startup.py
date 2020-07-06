import time
import sys
from bluesky.simulators import summarize_plan

# Check version of bluesky and act accordingly
from distutils.version import LooseVersion
import bluesky
if bluesky.__version__ < LooseVersion('1.6'):
    OLD_BLUESKY = True
else:
    OLD_BLUESKY = False

# Set up a RunEngine and use metadata backed by a sqlite file.
print(__file__)
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

if OLD_BLUESKY:
    # Make plots update live while scans run.
    from bluesky.utils import install_qt_kicker
    install_qt_kicker()

    from pathlib import Path
    from historydict import HistoryDict

    try:
        RE.md = HistoryDict('/nsls2/xf08id/metadata/bluesky_history.db')
        print('gpfs')
    except Exception as exc:
        print('local')
        print(exc)
        RE.md = HistoryDict('{}/.config/bluesky/bluesky_history.db'.format(str(Path.home())))
else:
    # Patch to fix Tom's terrible deeds
    import matplotlib.backends.backend_qt5
    from matplotlib.backends.backend_qt5 import _create_qApp
    from matplotlib._pylab_helpers import Gcf

    _create_qApp()
    qApp = matplotlib.backends.backend_qt5.qApp

    from bluesky.utils import PersistentDict
    RE.md = PersistentDict('/nsls2/xf08id/metadata/bluesky-md')

RE.is_aborted = False

start = timer()

def ensure_proposal_id(md):
    if 'proposal_id' not in md:
        raise ValueError("You forgot the proposal_id.")

# Set up default metadata.
RE.md['group'] = 'iss'
RE.md['Facility'] = 'NSLS-II'
RE.md['beamline_id'] = 'ISS (8-ID)'
RE.md['proposal_id'] = None
stop2 = timer()
RE.md_validator = ensure_proposal_id
stop = timer()

print("MD handling complete in {} sec".format(stop - start))


# the file paths for acquitision and analysis
ROOT_PATH = '/nsls2/xf08id'
RAW_FILEPATH = 'data'
USER_FILEPATH = 'users'


def print_to_gui(string, stdout=sys.stdout):
    print(string, file=stdout, flush=True)

