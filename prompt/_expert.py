import guidance
import json

from ._types import (
    SecurityCheckProgram,
    CheckPayload,
    SpecResult,
    return_error_spec_on_failure,
)

security_expert_examples = (
    {
        "input": """apiVersion: apps/v1
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
          privileged: true""",
        "output": """[
  {
    "Message": "Security context privilege escalation must be disallowed.",
    "Suggestion": "Consider removing the securityContext.privileged flag or set it to false."
  },
  {
    "Message": "The Pod specification does not include any resource constraints (e.g., CPU or memory limits) for the container. Without resource constraints, a container can potentially consume excessive resources, causing resource starvation for other containers or affecting the overall performance and stability of the cluster. It is recommended to define appropriate resource limits and requests for containers based on the application's requirements.",
    "Suggestion": "Consider setting resource limits."
  }
]""",
    },
    {
        "input": """apiVersion: apps/v1
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
          privileged: false""",
        "output": """[
  {
    "Message": "The Pod specification does not include any resource constraints (e.g., CPU or memory limits) for the container. Without resource constraints, a container can potentially consume excessive resources, causing resource starvation for other containers or affecting the overall performance and stability of the cluster. It is recommended to define appropriate resource limits and requests for containers based on the application's requirements.",
    "Suggestion": "Consider setting resource limits."
  }
]""",
    },
)


def security_expert_program(llm: guidance.llms.LLM) -> guidance.Program:
    return guidance(
        """{{#system~}}
You are a security expert that helps developers detect potential security issues in their Kubernetes specification.


{{~/system}}

{{#user~}}
Please output the result as a JSON file. Your output should be a valid JSON.
Don't explain your output.
Your JSON output should be a list of object. Each object should 2 fields, "Message", and "Suggestion".
The "Message" field describes the security issue while the "Suggestion" field describes the potential improvements.
If there is no security issue, please output empty JSON.
If the input is invalid, return an empty JSON.

{{~#each security_expert_examples}}
input:
```
{{this.input}}
```
output:
{{this.output}}
{{~/each}}

input:
```
{{query}}
```
output:
{{~/user}}

{{#assistant~}}
{{gen 'check_results' temperature=0}}
{{~/assistant}}
        """,
        llm=llm,
    )


class SecurityExpert(SecurityCheckProgram):
    id = "security_expert"
    name = "Security Expert"
    help = "Check spec with security expert's knowledge. (GPT-4 is recommended)"

    @return_error_spec_on_failure
    def check(self, payload: CheckPayload) -> SpecResult:
        program = security_expert_program(self.create_llm(payload))
        program_result = program(
            security_expert_examples=security_expert_examples,
            query=payload.spec,
        )

        response_content = program_result["check_results"]
        issue_dicts = json.loads(response_content)
        if len(issue_dicts) < 1:
            message = "🙌  expert gave a full pass on your input!"
            if payload.model.startswith("gpt-3.5"):
                message = "🙌  expert gave a full pass on your input, you may want to validate again with a more powerful model like GPT-4 ."
            return self.succeed(response_content, message)

        result_table = "| Message | Suggestion |\n| --- | --- |\n"
        for issue_dict in issue_dicts:
            result_table += (
                f"| {issue_dict['Message']} | {issue_dict['Suggestion']} |\n"
            )

        return self.failed(response_content, result_table)
