import contextlib

from ..exceptions import ValidationException
from ..salt_utils import SaltClient


class UnableToSyncAll(ValidationException):
    def __init__(self):
        super(UnableToSyncAll, self).__init__(
            "Sync failed, please run: "
            "\"salt -I 'ceph-salt:minions' saltutil.sync_all\" manually and fix "
            "the problems reported")


class UnableToSyncModules(ValidationException):
    def __init__(self):
        super(UnableToSyncModules, self).__init__(
            "Sync failed, please run: "
            "\"salt -I 'ceph-salt:minions' saltutil.sync_modules\" manually and fix "
            "the problems reported")


def pillar_refresh():
    with contextlib.redirect_stdout(None):
        SaltClient.local_cmd('*', 'saltutil.pillar_refresh', tgt_type="compound")


def sync_all():
    with contextlib.redirect_stdout(None):
        result = SaltClient.local_cmd('ceph-salt:minions', 'saltutil.sync_all', tgt_type='pillar')
    for minion, value in result.items():
        if not value:
            raise UnableToSyncAll()


def sync_modules():
    with contextlib.redirect_stdout(None):
        result = SaltClient.local_cmd('ceph-salt:minions', 'saltutil.sync_modules', tgt_type='pillar')
    for value in result:
        if not value:
            raise UnableToSyncModules()
