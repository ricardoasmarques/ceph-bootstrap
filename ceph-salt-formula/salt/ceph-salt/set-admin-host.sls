{% import 'macros.yml' as macros %}

{{ macros.begin_stage('Find admin host') }}
set admin host:
  ceph_orch.set_admin_host:
    - failhard: True
{{ macros.end_stage('Find admin host') }}
