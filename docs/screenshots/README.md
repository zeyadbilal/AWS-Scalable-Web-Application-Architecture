# Screenshots

No screenshots were included in the original project workspace — only the architecture diagram (`docs/architecture/original-target-diagram.png`) and two build-documentation files were provided. Nothing has been fabricated to fill this gap.

If console screenshots are captured later (e.g., while following [`docs/demo-script.md`](../demo-script.md)), organize them here by topic, matching the sections in the documentation:

```
docs/screenshots/
├── networking/     # VPC, subnets, route tables, NAT/Internet Gateways
├── compute/        # Launch Template, Auto Scaling Group, EC2 instances
├── database/       # RDS configuration, Multi-AZ setting
├── security/       # Security groups, WAF Web ACL and sampled requests
└── monitoring/     # CloudWatch alarms, SNS topic/subscription
```

Reference the most important ones from the relevant `docs/*.md` file and from the README — avoid embedding every screenshot in the README itself.
