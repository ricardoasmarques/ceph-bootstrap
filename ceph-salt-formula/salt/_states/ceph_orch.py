# -*- encoding: utf-8 -*-
import json
import logging
import time


logger = logging.getLogger(__name__)


def wait_for_admin_host(name, timeout=1800):
    ret = {'name': name, 'changes': {}, 'comment': '', 'result': False}
    starttime = time.time()
    timelimit = starttime + timeout
    configured_admin_host = None
    while not configured_admin_host:
        is_timedout = time.time() > timelimit
        if is_timedout:
            ret['comment'] = 'Timeout value reached.'
            return ret
        time.sleep(15)
        admin_hosts = __pillar__['ceph-salt']['minions']['admin']
        for admin_host in admin_hosts:
            failed = __salt__['ceph_salt.get_remote_grain'](admin_host, 'ceph-salt:execution:failed')
            if failed:
                ret['comment'] = 'One or more admin minions failed.'
                return ret
            provisioned = __salt__['ceph_salt.get_remote_grain'](admin_host,
                                                                'ceph-salt:execution:provisioned')
            if provisioned:
                ssh_user = __pillar__['ceph-salt']['ssh']['user']
                sudo = 'sudo ' if ssh_user != 'root' else ''
                status_ret = __salt__['cmd.run_all']("ssh -o StrictHostKeyChecking=no "
                                                     "-i /tmp/ceph-salt-ssh-id_rsa {}@{} "
                                                     "'if [[ -f /etc/ceph/ceph.conf "
                                                     "&& -f /etc/ceph/ceph.client.admin.keyring ]]; "
                                                     "then timeout 60 {}ceph orch status --format=json; "
                                                     "else (exit 1); fi'".format(
                                                         ssh_user,
                                                         admin_host,
                                                         sudo))
                if status_ret['retcode'] == 0:
                    status = json.loads(status_ret['stdout'])
                    if status.get('available'):
                        configured_admin_host = admin_host
                        break

    __salt__['grains.set']('ceph-salt:execution:admin_host', configured_admin_host)
    ret['result'] = True
    return ret


def add_host(name, host):
    ret = {'name': name, 'changes': {}, 'comment': '', 'result': False}
    admin_host = __salt__['grains.get']('ceph-salt:execution:admin_host')
    ssh_user = __pillar__['ceph-salt']['ssh']['user']
    sudo = 'sudo ' if ssh_user != 'root' else ''
    cmd_ret = __salt__['cmd.run_all']("ssh -o StrictHostKeyChecking=no "
                                      "-i /tmp/ceph-salt-ssh-id_rsa {}@{} "
                                      "'{}ceph orch host add {}'".format(ssh_user, admin_host,
                                                                       sudo, host))
    if cmd_ret['retcode'] == 0:
        ret['result'] = True
    return ret


def copy_ceph_conf_and_keyring(name):
    ret = {'name': name, 'changes': {}, 'comment': '', 'result': False}
    admin_host = __salt__['grains.get']('ceph-salt:execution:admin_host')
    ssh_user = __pillar__['ceph-salt']['ssh']['user']
    sudo = 'sudo ' if ssh_user != 'root' else ''
    cmd_ret = __salt__['cmd.run_all']("{0}rsync --rsync-path='{0}rsync' "
                                      "-e 'ssh -o StrictHostKeyChecking=no "
                                      "-i /tmp/ceph-salt-ssh-id_rsa' "
                                      "{1}@{2}:/etc/ceph/{{ceph.conf,ceph.client.admin.keyring}} "
                                      "/etc/ceph/".format(sudo, ssh_user, admin_host))
    if cmd_ret['retcode'] == 0:
        ret['result'] = True
    return ret


def orchestrated_reboot_if_needed(name, timeout=36000):
    ret = {'name': name, 'changes': {}, 'comment': '', 'result': False}
    if __grains__.get('os_family') == 'Suse':
        needs_reboot = __salt__['cmd.run_all']('zypper ps')['retcode'] > 0
    else:
        ret['comment'] = 'Unsupported distribution: Unable to check if reboot is needed'
        return ret
    if needs_reboot:
        id = __grains__['id']
        minions = __pillar__['ceph-salt']['execution']['minions']
        if id not in minions:
            ret['comment'] = 'Unexpected minion. Unable to run orchestrated reboot on minion {}'.format(id)
            return ret
        is_master = __salt__['service.status']('salt-master')
        if is_master:
            ret['comment'] = 'Salt master must be rebooted manually'
            return ret

        def _get_ancestor_minion():
            for i in range(len(minions)):
                if i < (len(minions)-1) and minions[i+1] == id:
                    return minions[i]
            return None

        # Wait until ancestor minion is updated
        starttime = time.time()
        timelimit = starttime + timeout
        ancestor_minion = _get_ancestor_minion()
        if ancestor_minion:
            __salt__['event.send']('ceph-salt/stage/begin',
                                   data={'desc': "Wait for '{}'".format(ancestor_minion)})
            ancestor_minion_ready = False
            while not ancestor_minion_ready:
                is_timedout = time.time() > timelimit
                if is_timedout:
                    ret['comment'] = 'Timeout value reached.'
                    return ret
                grain_value = __salt__['ceph_salt.get_remote_grain'](ancestor_minion, 'ceph-salt:execution:failed')
                if grain_value:
                    ret['comment'] = 'Minion {} failed.'.format(ancestor_minion)
                    return ret
                grain = 'ceph-salt:execution:updated'
                grain_value = __salt__['ceph_salt.get_remote_grain'](ancestor_minion, grain)
                if grain_value:
                    ancestor_minion_ready = True
                if not ancestor_minion_ready:
                    logger.info("Waiting for grain '%s' on '%s'", grain, ancestor_minion)
                    time.sleep(15)
            __salt__['event.send']('ceph-salt/stage/end',
                                   data={'desc': "Wait for '{}'".format(ancestor_minion)})

        # Wait until minion is ready to be rebooted
        host = __grains__['host']
        __salt__['event.send']('ceph-salt/stage/begin',
                                   data={'desc': "Wait for 'ceph orch host ok-to-stop {}'".format(host)})
        ok_to_stop = False
        while not ok_to_stop:
            is_timedout = time.time() > timelimit
            if is_timedout:
                ret['comment'] = 'Timeout value reached.'
                return ret
            admin_host = __salt__['grains.get']('ceph-salt:execution:admin_host')
            ssh_user = __pillar__['ceph-salt']['ssh']['user']
            sudo = 'sudo ' if ssh_user != 'root' else ''
            cmd_ret = __salt__['cmd.run_all']("ssh -o StrictHostKeyChecking=no "
                                              "-i /tmp/ceph-salt-ssh-id_rsa {}@{} "
                                              "'{}ceph orch host ok-to-stop {}'".format(ssh_user, admin_host,
                                                                                        sudo, host))
            ok_to_stop = cmd_ret['retcode'] == 0
            if not ok_to_stop:
                logger.info("Waiting for 'ceph_orch.host_ok_to_stop'")
                time.sleep(15)
        __salt__['event.send']('ceph-salt/stage/end',
                                   data={'desc': "Wait for 'ceph orch host ok-to-stop {}'".format(host)})

        # Reboot
        __salt__['event.send']('ceph-salt/minion_reboot', data={'desc': 'Rebooting...'})
        time.sleep(5)
        __salt__['system.reboot']()
    ret['result'] = True
    return ret
