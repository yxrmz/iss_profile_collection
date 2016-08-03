from functools import partial
from pyOlog import SimpleOlogClient
from bluesky.callbacks.olog import logbook_cb_factory

# Set up the logbook. This configures bluesky's summaries of
# data acquisition (scan type, ID, etc.).

LOGBOOKS = ['Data Acquisition']  # list of logbook names to publish to
simple_olog_client = SimpleOlogClient()
generic_logbook_func = simple_olog_client.log
configured_logbook_func = partial(generic_logbook_func, logbooks=LOGBOOKS)

cb = logbook_cb_factory(configured_logbook_func)

#DICT_OF_TEMPLATES = {'relative_scan': "BLAH",
#                     'execute_trajectory': "BLERG"}

#cb = logbook_cb_factory(configured_logbook_func,
#                        desc_template=CUSTOM_DEFAULT_TEMPLATE,
#                        desc_dispatch=DICT_OF_TEMPLATES)
RE.subscribe('start', cb)
