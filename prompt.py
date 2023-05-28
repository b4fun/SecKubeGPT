import typing as t
import openai
import json
from utils import log_data
import dataclasses as dc


@dc.dataclass
class SpecResult:
    has_issues: bool
    raw_response: str
    formatted_response: str


def get_pss_prompt_with_table(spec: str) -> str:
    return f"""
Please detect potential security issues with Kubernetes pod security standard definition in below:

---
Rule Name: HostProcess
Description: Windows pods offer the ability to run HostProcess containers which enables privileged access to the Windows node. Privileged access to the host is disallowed in the baseline policy.
Restricted Fields:
spec.securityContext.windowsOptions.hostProcess
spec.containers[*].securityContext.windowsOptions.hostProcess
spec.initContainers[*].securityContext.windowsOptions.hostProcess
spec.ephemeralContainers[*].securityContext.windowsOptions.hostProcess
Allowed Values: Undefined/nil/false
---
Rule Name: Host Namespaces
Description: Sharing the host namespaces must be disallowed.
Restricted Fields:
spec.hostNetwork
spec.hostPID
spec.hostIPC
Allowed Values: Undefined/nil/false
---
Rule Name: Privileged Containers
Description: Privileged Pods disable most security mechanisms and must be disallowed.
Restricted Fields:
spec.containers[*].securityContext.privileged
spec.initContainers[*].securityContext.privileged
spec.ephemeralContainers[*].securityContext.privileged
Allowed Values: Undefined/nil/false
---
Rule Name: Capabilities
Description: Adding additional capabilities beyond those listed below must be disallowed.
Restricted Fields:
spec.containers[*].securityContext.capabilities.add
spec.initContainers[*].securityContext.capabilities.add
spec.ephemeralContainers[*].securityContext.capabilities.add
Allowed Values: Undefined/nil / AUDIT_WRITE / CHOWN / DAC_OVERRIDE / FOWNER / FSETID / KILL / MKNOD / NET_BIND_SERVICE / SETFCAP / SETGID / SETPCAP / SETUID / SYS_CHROOT
---
Rule Name: HostPath Volumes
Description: HostPath volumes must be forbidden.
Restricted Fields:
spec.volumes[*].hostPath
Allowed Values: Undefined/nil
---
Rule Name: Host Ports
Description: HostPorts should be disallowed entirely (recommended) or restricted to a known list.
Restricted Fields:
spec.containers[].ports[].hostPort
spec.initContainers[].ports[].hostPort
spec.ephemeralContainers[].ports[].hostPort
Allowed Values: Undefined/nil / Known list (not supported by the built-in Pod Security Admission controller) / 0
---
Rule Name: AppArmor
Description: On supported hosts, the runtime/default AppArmor profile is applied by default. The baseline policy should prevent overriding or disabling the default AppArmor profile, or restrict overrides to an allowed set of profiles.
Restricted Fields:
metadata.annotations["container.apparmor.security.beta.kubernetes.io/*"]
Allowed Values: Undefined/nil / runtime/default / localhost/*
---
Rule Name: SELinux
Description: Setting the SELinux type is restricted, and setting a custom SELinux user or role option is forbidden.
Restricted Fields:
spec.securityContext.seLinuxOptions.type
spec.containers[*].securityContext.seLinuxOptions.type
spec.initContainers[*].securityContext.seLinuxOptions.type
spec.ephemeralContainers[*].securityContext.seLinuxOptions.type
spec.securityContext.seLinuxOptions.user
spec.containers[*].securityContext.seLinuxOptions.user
spec.initContainers[*].securityContext.seLinuxOptions.user
spec.ephemeralContainers[*].securityContext.seLinuxOptions.user
spec.securityContext.seLinuxOptions.role
spec.containers[*].securityContext.seLinuxOptions.role
spec.initContainers[*].securityContext.seLinuxOptions.role
spec.ephemeralContainers[*].securityContext.seLinuxOptions.role
Allowed Values: Undefined/"" / container_t / container_init_t / container_kvm_t for type field and Undefined/"" for user and role fields.
---
Rule Name: Proc Mount Type
Description: The default /proc masks are set up to reduce attack surface, and should not be overridden.
Restricted Fields:
spec.securityContext.procMount
spec.containers[*].securityContext.procMount
spec.initContainers[*].securityContext.procMount
spec.ephemeralContainers[*].securityContext.procMount
Allowed Values: Undefined/nil / Default
---
Rule Name: Seccomp
Description: Seccomp profile must not be explicitly set to Unconfined.
Restricted Fields:
spec.securityContext.seccompProfile.type
spec.containers[*].securityContext.seccompProfile.type
spec.initContainers[*].securityContext.seccompProfile.type
spec.ephemeralContainers[*].securityContext.seccompProfile.type
Allowed Values: Undefined/nil / RuntimeDefault / Localhost
---
Rule Name: Sysctls
Description: Sysctls can disable security mechanisms or affect all containers on a host, and should be disallowed except for an allowed "safe" subset. A sysctl is considered safe if it is namespaced in the container or the Pod, and it is isolated from other Pods or processes on the same Node.
Restricted Fields:
spec.securityContext.sysctls[*].name
Allowed Values: Undefined/nil / kernel.shm_rmid_forced / net.ipv4.ip_local_port_range / net.ipv4.ip_unprivileged_port_start / net.ipv4.tcp_syncookies / net.ipv4.ping_group_range 
---

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
output:"""


def get_pss_openai_messages(spec: str) -> t.List[t.Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that helps developers "
                "detect potential security issues in their Kubernetes "
                "YAML files using pod security standard."
            ),
        },
        {
            "role": "user",
            "content": get_pss_prompt_with_table(spec),
        },
    ]


def get_pss_results_from_openai(api_key: str, model: str, spec: str) -> SpecResult:
    messages = get_pss_openai_messages(spec)
    log_data("openai prompt", messages[1]["content"])

    response = openai.ChatCompletion.create(
        api_key=api_key,
        model=model,
        messages=messages,
        temperature=0.0,
    )

    response_content = response["choices"][0]["message"]["content"]
    log_data("openai response", response_content)

    try:
        issue_dicts = json.loads(response_content)
        if len(issue_dicts) < 1:
            return SpecResult(
                has_issues=False,
                raw_response=response_content,
                formatted_response="😊 no security issue detected!",
            )

        result_table = "| Rule | Message | Location |\n|--|--|--|\n"
        for issue_dict in issue_dicts:
            rule_name = issue_dict.get("Rule")
            message = issue_dict.get("Message")
            location = json.dumps(issue_dict.get("Location"))
            result_table += f"| {rule_name} | {message} | {location} |\n"

        return SpecResult(
            has_issues=True,
            raw_response=response_content,
            formatted_response=result_table,
        )
    except Exception as e:
        log_data("openai response decode error", e)

        # return the full response for now
        err_details = (
            f"failed to parse OpenAI response from JSON\n\n```\n{response_content}\n```"
        )
        raise Exception(err_details)
