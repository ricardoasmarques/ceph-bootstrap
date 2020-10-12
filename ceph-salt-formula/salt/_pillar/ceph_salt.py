"""
Restrict 'ceph-salt' pillar data access to minions managed by ceph-salt.

This pillar module exists to prevent the security risk of relying on grains targeting.

Example of an insecure top.sls:
```
base:
  ceph-salt:member:
    - match: grain
    - ceph-salt
```

Grains can be set by the minion, so nothing prevents a non-ceph-salt minion from setting
the 'ceph-salt:member' grain and after that, it will have access to ceph-salt pillar which
may contain sensible data. The ceph-salt pillar modules was created to prevent that risk.


----------
How to use
----------

Configure the 'ceph_salt' external pillar in /etc/salt/master:
```
ext_pillar:
  - ceph_salt: ''
```

Restart salt-master:
```
# systemctl restart salt-master
```

Sync pillar modules:
```
# salt-run saltutil.sync_pillar
```

Refresh pillar:
```
# salt '*' saltutil.refresh_pillar
```

Pillar is now visible to minions that are included in ceph-salt config:
```
# salt '*' pillar.get ceph-salt
```

Pillar targeting will also work:
```
# salt -I 'ceph-salt:minions' pillar.get ceph-salt
```
"""

import logging
import os
import yaml

log = logging.getLogger(__name__)


def ext_pillar(minion_id, pillar, *args, **kwargs):
    # If ceph-salt pillar data was already loaded from 'top.sls',
    # we remove it to make sure that it was not loaded by a minion
    # that is not supposed to access it.
    pillar.pop('ceph-salt', None)

    # Read ceph-salt pillar file
    pillar_base_dirs = __opts__.get('pillar_roots', {'base': []})['base']
    if not pillar_base_dirs:
        log.warning("Unable to get pillar roots base dir config")
        return {}
    pillar_base_dir = pillar_base_dirs[0]
    full_path = os.path.join(pillar_base_dir, 'ceph-salt.sls')
    log.info("Reading pillar items from file: %s", full_path)
    if not os.path.exists(full_path):
        log.warning("Pillar file not found: %s", pillar_base_dir)
        return {}
    with open(full_path, 'r') as file:
        data = yaml.full_load(file)
        if data is None:
            data = {}

    # Check if minion is allowed to access ceph-salt pillar data
    if minion_id not in data.get('ceph-salt', {}).get('minions', {}).get('all', []):
        return {}

    return data
