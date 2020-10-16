{% import 'macros.yml' as macros %}

{% if 'cephadm' in grains['ceph-salt']['roles'] %}

{{ macros.begin_stage('Configure sysctl') }}

/etc/sysctl.d/90-ceph.conf:
  file.managed:
    - source:
        - salt://ceph-salt/apply/files/90-ceph.conf.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - makedirs: True
    - backup: minion
    - failhard: True

reload sysctl:
  cmd.run:
    - name: "sysctl --system"

{{ macros.end_stage('Configure sysctl') }}

{% endif %}

sysctl:
  test.nop
