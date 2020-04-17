{% if 'ceph-salt' in grains and grains['ceph-salt']['member'] %}

include:
    - .provision-begin
    - .sshkey
    - .set-admin-host
    - .software
    - .container
    - .apparmor
    - .time
    - .cephtools
    - .provision-end
{% if pillar['ceph-salt'].get('bootstrap_enabled', True) %}
    - .cephbootstrap
    - .wait-for-admin-host
    - .cephorch
    - .ceph-admin
{% endif %}
    - .cleanup

{% else %}

nothing to do in this node:
  test.nop

{% endif %}
