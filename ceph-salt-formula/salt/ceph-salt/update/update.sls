{% import 'macros.yml' as macros %}

{{ macros.begin_stage('Update all packages') }}

install required packages:
  pkg.installed:
    - pkgs:
      - lsof
    - failhard: True

update packages:
  module.run:
    - name: pkg.upgrade
    - failhard: True

{{ macros.end_stage('Update all packages') }}

{% if pillar['ceph-salt']['updates']['reboot'] %}

{{ macros.begin_stage('Find an admin host') }}
wait for admin host:
  ceph_orch.wait_for_admin_host:
    - failhard: True
{{ macros.end_stage('Find an admin host') }}

reboot:
   ceph_orch.orchestrated_reboot_if_needed:
     - failhard: True

{% else %}

skip reboot:
  test.nop

{% endif %}
