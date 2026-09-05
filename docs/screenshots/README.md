# Screenshots

No static screenshots are included in this repository. **Instead, the full console workflow — networking, compute, database, security, and monitoring — is documented in a recorded video walkthrough**: see [`docs/video/README.md`](../video/README.md) and the **Video Walkthrough** section of the main [`README.md`](../../README.md) for the link.

If individual screenshots are extracted from that video later (or captured fresh), organize them here by topic, matching the sections in the documentation:

```
docs/screenshots/
├── networking/     # VPC, subnets, route tables, NAT/Internet Gateways
├── compute/        # Launch Template, Auto Scaling Group, EC2 instances
├── database/       # RDS configuration, Multi-AZ setting
├── security/       # Security groups, WAF Web ACL and sampled requests
└── monitoring/     # CloudWatch alarms, SNS topic/subscription
```

Reference the most important ones from the relevant `docs/*.md` file and from the README — avoid embedding every screenshot in the README itself.
