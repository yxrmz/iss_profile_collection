print(__file__)

import logging
import sys
import time
from pathlib import Path
from timeit import default_timer as timer

import appdirs
import bluesky
import nslsii
from bluesky.simulators import summarize_plan

# Check version of bluesky and act accordingly
from distutils.version import LooseVersion

if bluesky.__version__ < LooseVersion('1.6'):
    OLD_BLUESKY = True
else:
    OLD_BLUESKY = False


if OLD_BLUESKY:
    nslsii.configure_base(get_ipython().user_ns, 'iss') #, pbar=False)
else:
    import ophyd

    ophyd.EpicsSignal.set_default_timeout(timeout=60, connection_timeout=60)

    # We need to use v0 to have a pandas.Dataframe type returned via hdr.data() using the APBBinFileHandler handler.
    from databroker.v0 import Broker
    db = Broker.named('iss')
    nslsii.configure_base(get_ipython().user_ns, db, pbar=False)

# nslsii.configure_base(get_ipython().user_ns, 'iss',  publish_documents_to_kafka=True)

# Temporary fix before it's fixed in ophyd
logger = logging.getLogger('ophyd')
logger.setLevel('WARNING')


bec.disable_plots()
bec.disable_table()
RE.subscribe(bec)
peaks = bec.peaks  # just as alias for less typing




try:
    from bluesky.utils import PersistentDict
except ImportError:
    import msgpack
    import msgpack_numpy
    import zict

    class PersistentDict(zict.Func):
        def __init__(self, directory):
            self._directory = directory
            self._file = zict.File(directory)
            super().__init__(self._dump, self._load, self._file)

        @property
        def directory(self):
            return self._directory

        def __repr__(self):
            return f"<{self.__class__.__name__} {dict(self)!r}>"

        @staticmethod
        def _dump(obj):
            "Encode as msgpack using numpy-aware encoder."
            # See https://github.com/msgpack/msgpack-python#string-and-binary-type
            # for more on use_bin_type.
            return msgpack.packb(
                obj,
                default=msgpack_numpy.encode,
                use_bin_type=True)

        @staticmethod
        def _load(file):
            return msgpack.unpackb(
                file,
                object_hook=msgpack_numpy.decode,
                raw=False)

runengine_metadata_dir = Path('/nsls2/xf08id/metadata/') / Path("runengine-metadata")

# PersistentDict will create the directory if it does not exist
RE.md = PersistentDict(runengine_metadata_dir)


if OLD_BLUESKY:
    # Make plots update live while scans run.
    from bluesky.utils import install_qt_kicker
    install_qt_kicker()
else:
    # Patch to fix Tom's terrible deeds
    import matplotlib.backends.backend_qt5
    from matplotlib._pylab_helpers import Gcf
    from matplotlib.backends.backend_qt5 import _create_qApp

    _create_qApp()
    qApp = matplotlib.backends.backend_qt5.qApp


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
