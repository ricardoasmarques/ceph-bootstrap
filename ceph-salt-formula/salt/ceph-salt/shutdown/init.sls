{% import 'macros.yml' as macros %}

{% if 'ceph-salt' in grains and grains['ceph-salt']['member'] %}

{{ macros.begin_stage("Stop 'ceph.target' service") }}

stop ceph.target:
  service.dead:
    - name: ceph.target
    - failhard: True

{{ macros.end_stage("Stop 'ceph.target' service") }}

{% else %}

nothing to do in this node:
  test.nop

{% endif %}
