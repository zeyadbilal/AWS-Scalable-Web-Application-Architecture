# Project Structure

This repository documents an AWS infrastructure project that was built through the AWS Console. **No application source code (Next.js, FastAPI, Nginx configuration, etc.) was present in the original project workspace** — only the architecture diagram, two build-documentation files, and a recorded video walkthrough. This repository therefore contains documentation, the architecture diagram, and evidence of the implementation, organized for public review. If the application source code becomes available later, it belongs under a new top-level `src/` (or `app/`) directory without disturbing the structure below.

```
.
├── README.md                              # Project overview, embedded diagram, quick reference
├── LICENSE
├── .gitignore
└── docs/
    ├── architecture.md                    # Full architecture description (networking, compute, data, CDN, request flow)
    ├── aws-services.md                    # Table of every AWS service used, purpose and configuration
    ├── security.md                        # Defense-in-depth model, security groups, WAF, SSM, IAM, gaps
    ├── monitoring.md                      # CloudWatch alarms, SNS, alerting lifecycle, coverage gaps
    ├── scalability-availability.md        # Auto Scaling, HA mechanisms, failure scenarios, limits
    ├── deployment.md                      # Actual build sequence, prerequisites, verification performed
    ├── troubleshooting.md                 # Operational workflow, alarm response, configuration checks
    ├── project-structure.md               # This file
    ├── demo-script.md                     # Companion outline for the recorded video walkthrough
    ├── architecture/
    │   ├── aws-architecture.png           # Rendered solution diagram (embedded in README)
    │   ├── aws-architecture.svg           # Vector version of the same diagram
    │   ├── generate_diagram.py            # Regenerates both files above using the official AWS
    │   │                                  # Architecture Icons (the `diagrams` Python package)
    │   └── original-target-diagram.png    # The diagram originally produced during the project,
    │                                      # kept for reference — it includes Route 53/HTTPS as
    │                                      # target architecture; see docs/architecture.md for the
    │                                      # documented discrepancies between it and the deployment
    ├── screenshots/
    │   └── README.md                      # Suggested folder layout; documented via video instead (see docs/video/)
    ├── video/
    │   ├── README.md                      # Hosting link/status for the recorded walkthrough
    │   └── aws-project-walkthrough.mp4    # Gitignored (168 MB, exceeds GitHub's 100 MB push limit) —
    │                                      # hosted externally; kept locally for convenience only
    └── source-material/
        ├── project-doc-raw.md             # Original, unedited build notes (primary source of truth)
        └── architecture-report-full.md    # Full evidence-audited architecture report (exhaustive
                                            # version of docs/architecture.md, with ADRs and a
                                            # line-by-line diagram/documentation cross-check)
```

## Why the source material is preserved verbatim

`docs/source-material/` keeps the original build notes and the full audit report unedited. Every summary document elsewhere in `docs/` is derived from these two files — if a fact in `docs/architecture.md` ever seems to need more context, the underlying evidence is one click away rather than lost in an editing pass.

## Documentation, not a working codebase

Because no application code was part of the source workspace, there is no build step, dependency list, or test suite for this repository — it is a documentation and architecture-evidence package. The "Deployment" document describes an AWS Console workflow, not a script to run.
