# -*- encoding: utf-8 -*-
import json

from salt.exceptions import SaltInvocationError

def configured():
    ret = __salt__['cmd.run_all']("sh -c 'type ceph'")
    if ret['retcode'] != 0:
        return False
    if not __salt__['file.file_exists']("/etc/ceph/ceph.conf"):
        return False
    if not __salt__['file.file_exists']("/etc/ceph/ceph.client.admin.keyring"):
        return False
    ret = __salt__['cmd.run_all']("ceph orch status")
    if ret['retcode'] != 0:
        return False
    return True

def host_ls():
    ret = __salt__['cmd.run']("ceph orch host ls --format=json")
    return json.loads(ret)

def remote_host_ls():
    """
    Similar to 'host_ls' but will run on 'ceph-salt:execution:admin_host' grain.
    If 'ceph-salt:execution:admin_host' grain is not set, then an empty list will be returned.
    """
    host = __salt__['grains.get']('ceph-salt:execution:admin_host')
    if not host:
        return []
    ret = __salt__['cmd.run_all']("ssh -o StrictHostKeyChecking=no "
                                  "-i /tmp/ceph-salt-ssh-id_rsa root@{} "
                                  "'salt-call ceph_orch.host_ls2 "
                                  "--out=json --out-indent=-1'".format(host))
    if ret['retcode'] != 0:
        raise SaltInvocationError("Failed to run 'ceph_orch.host_ls' on host '{}'.".format(host))
    return json.loads(ret['stdout'])['local']
