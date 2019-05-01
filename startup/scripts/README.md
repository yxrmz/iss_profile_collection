## Description
`kill_all_ipython_for_xf08id.sh` script is used to kill all IPython processes for the ISS beamline user xf08id.

## Usage
```bash
✔ ~/.ipython/profile_collection/startup/scripts [master|…1] 
11:00 $ ./kill_all_ipython_for_xf08id.sh 
Found IPython processes for xf08id:
===================================
xf08id    31490  22473  7 11:00 pts/22   00:00:00 /opt/conda/bin/python /opt/conda/bin/ipython
xf08id    31509  31460 65 11:00 pts/10   00:00:07 /opt/conda_envs/collection-2019-1.2-iss/bin/python /opt/conda_envs/collection-2019-1.2-iss/bin/ipython --profile=collection --IPCompleter.use_jedi=False

PIDs to kill: 31490 31509
Continue? (y/[N]): 
✘-1 ~/.ipython/profile_collection/startup/scripts [master|…1] 
11:00 $ ./kill_all_ipython_for_xf08id.sh 
Found IPython processes for xf08id:
===================================
xf08id    31490  22473  5 11:00 pts/22   00:00:00 /opt/conda/bin/python /opt/conda/bin/ipython
xf08id    31509  31460 49 11:00 pts/10   00:00:07 /opt/conda_envs/collection-2019-1.2-iss/bin/python /opt/conda_envs/collection-2019-1.2-iss/bin/ipython --profile=collection --IPCompleter.use_jedi=False

PIDs to kill: 31490 31509
Continue? (y/[N]): y
Killing 31490 31509...

Processes after killing:
========================
```
