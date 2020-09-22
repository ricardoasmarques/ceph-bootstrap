{% import 'macros.yml' as macros %}

{% if 'ceph-salt' in grains and grains['ceph-salt']['member'] %}

check fsid:
   ceph_salt.check_fsid:
     - formula: ceph-salt.shutdown
     - failhard: True

stop cluster:
   ceph_orch.stop_cluster:
     - failhard: True

{% else %}

nothing to do in this node:
  test.nop

{% endif %}
