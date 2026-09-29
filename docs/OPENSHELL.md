# OpenShell integration boundary

The Python runtime policy is an executable specification for expected actions. It does not implement Landlock, seccomp, a network proxy, credential isolation, or OpenShell. No OpenShell configuration has been deployed or validated by this project.

## Documentation checked

NVIDIA's current policy reference describes static filesystem/Landlock/process controls and dynamically changeable network controls. Pin a release before creating deployment configuration because schemas and effective defaults can change.

- [Policy schema](https://docs.nvidia.com/openshell/latest/reference/policy-schema)
- [Default policy and baseline paths](https://docs.nvidia.com/openshell/latest/how-it-works/policies/default-policy)
- [Security best practices](https://docs.nvidia.com/openshell/latest/security/best-practices.html)
- [Sandbox logging](https://docs.nvidia.com/openshell/observability/logging)

Do not assume that omitting a policy selects a restrictive default. Inspect the effective policy, including provider/image contributions and baseline paths. This matters particularly for `/etc`, `/proc`, and `/tmp`, which the source document proposes probing.

## Integration checklist

1. Provision an explicitly selected Brev Linux instance and record the kernel and GPU versions. GPU experiments need local model inference; deterministic harness runs do not.
2. Pin OpenShell and validate required enforcement controls at startup. Treat missing enforcement as a failed experiment, not a passing run.
3. Mount only synthetic fixtures and decoy credentials into the sandbox. Use controlled receiver endpoints; never send sensitive material to an unrelated real service.
4. Separate the agent process from the policy controller. The agent must not have credentials or write access to expand its own policy.
5. Allow only the customer-scoped fixture paths and exact necessary bank API methods/routes. Application authorization must validate customer identifiers in query/body data as well as route access.
6. Replace virtual operations with actual file reads, process launches and HTTP requests inside the sandbox. Observe the real result independently from the expected policy decision. Never call the local Guard to pre-block a probe intended to measure OpenShell enforcement.
7. Export original OCSF events separately from FinGuard's application JSONL. Correlate action IDs and timestamps; do not label FinGuard events as OCSF.
8. Record effective policy snapshots, denial events, controlled sink receipts, task outcomes, inference latency and GPU utilization. Populate currently-null metrics only from measured data.

The unrestricted comparison must still run within an isolated synthetic lab. A human-review hold is not authorization to expand the underlying OpenShell policy.
