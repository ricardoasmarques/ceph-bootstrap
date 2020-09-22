{% import 'macros.yml' as macros %}

{% if 'ceph-salt' in grains and grains['ceph-salt']['member'] %}

{{ macros.begin_stage("Start 'ceph.target' service") }}

start ceph.target:
  service.running:
    - name: ceph.target
    - failhard: True

{{ macros.end_stage("Start 'ceph.target' service") }}

{% else %}

nothing to do in this node:
  test.nop

{% endif %}
