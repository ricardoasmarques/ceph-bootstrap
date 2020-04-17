reset provisioned:
  grains.present:
    - name: ceph-salt:execution:provisioned
    - value: False

reset failure:
  grains.present:
    - name: ceph-salt:execution:failed
    - value: False

set admin host:
  ceph_orch.set_admin_host:
    - failhard: True