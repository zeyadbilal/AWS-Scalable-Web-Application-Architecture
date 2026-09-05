# AWS Services Used

This table lists every AWS service the project documentation records as **deployed**. Services that were designed but not deployed are listed separately at the bottom, clearly marked, so the distinction between "built" and "planned" is never ambiguous.

| AWS Service | Purpose | Implementation |
|---|---|---|
| **Amazon VPC** | Network isolation boundary | `aws-project-vpc`, `10.0.0.0/16`, 6 subnets across 2 AZs, 5 route tables |
| **Internet Gateway** | Internet connectivity for public subnets | `aws-project-igw`, attached to the VPC; `0.0.0.0/0` route in `public-rt` |
| **NAT Gateway** | Outbound-only internet access for private subnets | `nat-gateway-az1`, `nat-gateway-az2` — one per AZ, each with a dedicated Elastic IP, zone-local routing |
| **Amazon EC2** | Application compute | `t3.small` instances launched from a custom Golden AMI, in the private application subnets |
| **EC2 Launch Template** | Standardized instance definition | Custom AMI, `t3.small`, `ec2-sg`, IAM instance profile for `LuminaEC2SSMRole` |
| **EC2 Auto Scaling Group** | Capacity management and self-healing | `dental-asg`; min 2 / desired 2 / max 6; multi-AZ; target-tracking scaling policy on CPU utilisation |
| **Application Load Balancer** | Layer 7 public entry point | Internet-facing, deployed across both AZs, HTTP :80 listener, `alb-sg` |
| **ALB Target Group** | Target registration and health evaluation | Type: instance, HTTP:80, health checks enabled, bound to the ASG |
| **Amazon RDS (PostgreSQL)** | Managed relational database | Private, isolated DB subnets, TCP 5432, `rds-sg`, Multi-AZ primary/standby as documented |
| **Amazon CloudFront** | Edge delivery and static-asset caching | Distribution with the ALB as origin |
| **AWS WAF** | Layer 7 request inspection | Web ACL `dental-waf` — 4 AWS managed rule groups + 5 custom rules; 3 rules in COUNT mode |
| **AWS Systems Manager** | Secure administrative access | Session Manager via the SSM Agent and `LuminaEC2SSMRole` |
| **AWS IAM** | Instance permissions | Role `LuminaEC2SSMRole` with the `AmazonSSMManagedInstanceCore` managed policy, attached through the Launch Template's instance profile |
| **Amazon CloudWatch** | Metrics and alarms | 7 alarms across the ASG, ALB, Target Group and RDS; 5-minute evaluation periods |
| **Amazon SNS** | Notification delivery | Topic with an email subscription; every alarm publishes to it |
| **Security Groups** | Instance-level stateful firewall | `alb-sg`, `ec2-sg`, `rds-sg` — chained by security-group reference, not CIDR |
| **Amazon EBS** | Instance root storage | AMI-based root volume, attached to every EC2 instance |

## Planned but not implemented

These appear in the project's target architecture and in the original diagram but are explicitly recorded as **not deployed**:

| Service | Planned role | Why it was not deployed |
|---|---|---|
| **Amazon Route 53** | DNS — a Hosted Zone with an Alias A record pointing at the ALB | No domain was purchased |
| **AWS Certificate Manager (ACM)** | TLS certificate for an ALB HTTPS listener on :443 | Depends on Route 53 / a purchased domain for DNS validation |
| **AWS Secrets Manager** | Runtime retrieval of database credentials via the EC2 IAM role | Not implemented — credentials are currently supplied through configuration baked into the AMI |

See [`docs/deployment.md`](deployment.md) for the exact sequence that would complete the Route 53/ACM/HTTPS chain, and [`docs/security.md`](security.md) for why the Secrets Manager gap matters.
