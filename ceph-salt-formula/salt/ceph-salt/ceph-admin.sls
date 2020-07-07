{% import 'macros.yml' as macros %}

{% if 'admin' in grains['ceph-salt']['roles'] %}

{{ macros.begin_stage('Ensure keyring is present') }}
copy keyring from an admin node:
  ceph_orch.copy_keyring:
    - failhard: True
{{ macros.end_stage('Ensure keyring is present') }}

{{ macros.begin_stage('Ensure cephadm MGR module is configured') }}

configure cephadm mgr module:
  cmd.run:
    - name: |
        ceph config-key set mgr/cephadm/manage_etc_ceph_ceph_conf true
        ceph config-key set mgr/cephadm/ssh_identity_key -i /tmp/ceph-salt-ssh-id_rsa
        ceph config-key set mgr/cephadm/ssh_identity_pub -i /tmp/ceph-salt-ssh-id_rsa.pub
    - failhard: True

{{ macros.end_stage('Ensure cephadm MGR module is configured') }}

{% endif %}
