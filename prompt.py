import typing as t
import openai
import json

from utils import log_data


# TODO: convert table to example output
def get_pss_prompt_with_table(spec: str) -> str:
    return f'''
Please detect potential security issues with Kubernetes pod security standard definition in below:

```
<table>
	<caption style="display:none">Baseline policy specification</caption>
	<tbody>
		<tr>
			<th>Control</th>
			<th>Policy</th>
		</tr>
		<tr>
			<td style="white-space: nowrap">HostProcess</td>
			<td>
				<p>Windows pods offer the ability to run <a href="/docs/tasks/configure-pod-container/create-hostprocess-pod">HostProcess containers</a> which enables privileged access to the Windows node. Privileged access to the host is disallowed in the baseline policy. {{< feature-state for_k8s_version="v1.23" state="beta" >}}</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.windowsOptions.hostProcess</code></li>
					<li><code>spec.containers[*].securityContext.windowsOptions.hostProcess</code></li>
					<li><code>spec.initContainers[*].securityContext.windowsOptions.hostProcess</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.windowsOptions.hostProcess</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>false</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">Host Namespaces</td>
			<td>
				<p>Sharing the host namespaces must be disallowed.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.hostNetwork</code></li>
					<li><code>spec.hostPID</code></li>
					<li><code>spec.hostIPC</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>false</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">Privileged Containers</td>
			<td>
				<p>Privileged Pods disable most security mechanisms and must be disallowed.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.containers[*].securityContext.privileged</code></li>
					<li><code>spec.initContainers[*].securityContext.privileged</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.privileged</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>false</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">Capabilities</td>
			<td>
				<p>Adding additional capabilities beyond those listed below must be disallowed.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.containers[*].securityContext.capabilities.add</code></li>
					<li><code>spec.initContainers[*].securityContext.capabilities.add</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.capabilities.add</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>AUDIT_WRITE</code></li>
					<li><code>CHOWN</code></li>
					<li><code>DAC_OVERRIDE</code></li>
					<li><code>FOWNER</code></li>
					<li><code>FSETID</code></li>
					<li><code>KILL</code></li>
					<li><code>MKNOD</code></li>
					<li><code>NET_BIND_SERVICE</code></li>
					<li><code>SETFCAP</code></li>
					<li><code>SETGID</code></li>
					<li><code>SETPCAP</code></li>
					<li><code>SETUID</code></li>
					<li><code>SYS_CHROOT</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">HostPath Volumes</td>
			<td>
				<p>HostPath volumes must be forbidden.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.volumes[*].hostPath</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">Host Ports</td>
			<td>
				<p>HostPorts should be disallowed entirely (recommended) or restricted to a known list</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.containers[*].ports[*].hostPort</code></li>
					<li><code>spec.initContainers[*].ports[*].hostPort</code></li>
					<li><code>spec.ephemeralContainers[*].ports[*].hostPort</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li>Known list (not supported by the built-in <a href="/docs/concepts/security/pod-security-admission/">Pod Security Admission controller</a>)</li>
					<li><code>0</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">AppArmor</td>
			<td>
				<p>On supported hosts, the <code>runtime/default</code> AppArmor profile is applied by default. The baseline policy should prevent overriding or disabling the default AppArmor profile, or restrict overrides to an allowed set of profiles.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>metadata.annotations["container.apparmor.security.beta.kubernetes.io/*"]</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>runtime/default</code></li>
					<li><code>localhost/*</code></li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap">SELinux</td>
			<td>
				<p>Setting the SELinux type is restricted, and setting a custom SELinux user or role option is forbidden.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.seLinuxOptions.type</code></li>
					<li><code>spec.containers[*].securityContext.seLinuxOptions.type</code></li>
					<li><code>spec.initContainers[*].securityContext.seLinuxOptions.type</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.seLinuxOptions.type</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/""</li>
					<li><code>container_t</code></li>
					<li><code>container_init_t</code></li>
					<li><code>container_kvm_t</code></li>
				</ul>
				<hr />
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.seLinuxOptions.user</code></li>
					<li><code>spec.containers[*].securityContext.seLinuxOptions.user</code></li>
					<li><code>spec.initContainers[*].securityContext.seLinuxOptions.user</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.seLinuxOptions.user</code></li>
					<li><code>spec.securityContext.seLinuxOptions.role</code></li>
					<li><code>spec.containers[*].securityContext.seLinuxOptions.role</code></li>
					<li><code>spec.initContainers[*].securityContext.seLinuxOptions.role</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.seLinuxOptions.role</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/""</li>
				</ul>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap"><code>/proc</code> Mount Type</td>
			<td>
				<p>The default <code>/proc</code> masks are set up to reduce attack surface, and should be required.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.containers[*].securityContext.procMount</code></li>
					<li><code>spec.initContainers[*].securityContext.procMount</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.procMount</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>Default</code></li>
				</ul>
			</td>
		</tr>
		<tr>
  			<td>Seccomp</td>
  			<td>
  				<p>Seccomp profile must not be explicitly set to <code>Unconfined</code>.</p>
  				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.seccompProfile.type</code></li>
					<li><code>spec.containers[*].securityContext.seccompProfile.type</code></li>
					<li><code>spec.initContainers[*].securityContext.seccompProfile.type</code></li>
					<li><code>spec.ephemeralContainers[*].securityContext.seccompProfile.type</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>RuntimeDefault</code></li>
					<li><code>Localhost</code></li>
				</ul>
  			</td>
  		</tr>
		<tr>
			<td style="white-space: nowrap">Sysctls</td>
			<td>
				<p>Sysctls can disable security mechanisms or affect all containers on a host, and should be disallowed except for an allowed "safe" subset. A sysctl is considered safe if it is namespaced in the container or the Pod, and it is isolated from other Pods or processes on the same Node.</p>
				<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.sysctls[*].name</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
					<li>Undefined/nil</li>
					<li><code>kernel.shm_rmid_forced</code></li>
					<li><code>net.ipv4.ip_local_port_range</code></li>
					<li><code>net.ipv4.ip_unprivileged_port_start</code></li>
					<li><code>net.ipv4.tcp_syncookies</code></li>
					<li><code>net.ipv4.ping_group_range</code></li>
				</ul>
			</td>
		</tr>
	</tbody>
</table>
```

Please output the result as a JSON file. Your output should be a valid JSON.
Don't explain your output.
Your JSON output should be a list of object. Each object should have 3 fields, "Rule", "Message", and "Location".
The "Location" field describes the source code location, while the "Message" field describes the security issue.
If there is no security issue, please output empty JSON.
If the input is invalid, return an empty JSON.


----------------

input:
```
apiVersion: apps/v1
kind: Deployment
metadata:
name: nginx-deployment
spec:
selector:
    app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        securityContext:
          privileged: true
```
output:
[
{{
    "Rule": "Privileged Containers",
    "Location": "spec.template.spec.containers[0].securityContext.privileged",
    "Message": "Privileged Pods disable most security mechanisms and must be disallowed."
}}
]

----------------

input:
```
apiVersion: apps/v1
kind: Deployment
metadata:
name: nginx-deployment
spec:
  selector:
    app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        securityContext:
          privileged: false
---
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: my-container2
    image: nginx
    securityContext:
      privileged: false
```
output:
[]

----------------

input:
```
{spec}
```
output:'''


def get_pss_prompt_without_table(spec: str) -> str:
    return f'''
Please detect potential security issues with Kubernetes pod security standard.
Please output the result as a JSON file. Your output should be a valid JSON.
Don't explain your output.
Your JSON output should be a list of object. Each object should have 3 fields, "Rule", "Message", and "Location".
The "Location" field describes the source code location, while the "Message" field describes the security issue.
If there is no security issue, please output empty JSON.
If the input is invalid, return an empty JSON.

----------------

input:
```
apiVersion: apps/v1
kind: Deployment
metadata:
name: nginx-deployment
spec:
selector:
    app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        securityContext:
          privileged: true
```
output:
[
{{
    "Rule": "Privileged Containers",
    "Location": "spec.template.spec.containers[0].securityContext.privileged",
    "Message": "Privileged Pods disable most security mechanisms and must be disallowed."
}}
]

----------------

input:
```
apiVersion: apps/v1
kind: Deployment
metadata:
name: nginx-deployment
spec:
  selector:
    app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        securityContext:
          privileged: false
---
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: my-container2
    image: nginx
    securityContext:
      privileged: false
```
output:
[]

----------------

input:
```
{spec}
```
output:'''


def get_pss_openai_messages(spec: str) -> t.List[t.Dict[str, str]]:
    return [
        {
            'role': 'system',
            'content': ('You are a helpful assistant that helps developers '
                        'detect potential security issues in their Kubernetes '
                        'YAML files using pod security standard.'),
        },
        {
            'role': 'user',
            'content': get_pss_prompt_without_table(spec),
        },
    ]


def get_pss_results_from_openai(api_key: str, model: str, spec: str) -> str:
    messages = get_pss_openai_messages(spec)
    print('here!!')
    log_data('openai prompt', messages[1]['content'])

    response = openai.ChatCompletion.create(
        api_key=api_key,
        model=model,
        messages=messages,
        temperature=0.0,
    )

    response_content = response['choices'][0]['message']['content']
    log_data('openai response', response_content)

    try:
        issue_dicts = json.loads(response_content)
        if len(issue_dicts) < 1:
            return '😊 no security issue detected!'

        result_table = '| Rule | Message | Location |\n|--|--|--|\n'
        for issue_dict in issue_dicts:
            rule_name = issue_dict.get('Rule')
            message = issue_dict.get('Message')
            location = json.dumps(issue_dict.get('Location'))
            result_table += f'| {rule_name} | {message} | {location} |\n'
        return result_table

    except Exception as e:
        log_data('openai response decode error', e)

        # return the full response for now
        err_details = f'failed to parse OpenAI response from JSON\n\n```\n{response_content}\n```'
        raise Exception(err_details)