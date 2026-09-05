# Operational Workflow & Troubleshooting

## Accessing an instance

Administrative access is exclusively through **Systems Manager Session Manager**:

```
AWS Console → Systems Manager → Managed Nodes → select the instance → Start session
```

No SSH client, key, public IP, or bastion host is involved. Instances appear as managed nodes automatically because the Launch Template attaches `LuminaEC2SSMRole`.

**If an instance does not appear under Managed Nodes**, check, in order:
1. Is the SSM Agent running? `sudo systemctl status amazon-ssm-agent` (expect `Active: active (running)`).
2. Does the instance have the correct IAM instance profile attached (`LuminaEC2SSMRole`)?
3. Is outbound HTTPS on port 443 reachable through the NAT Gateway (check the private route table and the NAT Gateway's health)?

## Checking application health from within a session

```bash
sudo systemctl status nginx        # reverse proxy running?
sudo ss -tulpn                     # are 80, 3000 and 8000 listening as expected?
curl http://127.0.0.1:8000         # backend responding? expect {"status":"ok",...}
curl -I http://127.0.0.1:3000      # frontend responding?
```

At the infrastructure level, the **ALB Target Group** console page shows each registered instance's health state and the specific reason for any failure — the fastest way to distinguish "the instance is down" from "the instance is up but failing its health check."

## Responding to each configured alarm

See [`docs/monitoring.md`](monitoring.md#first-response-per-alarm) for the full table of alarms and first-response actions.

## Handling an unhealthy instance

The ALB removes an unhealthy target from rotation automatically, so the first operational question is not "how do I stop traffic" but "why did it fail." Use Session Manager to check whether Nginx is running, whether Next.js/FastAPI are listening, and whether the instance can reach RDS on port 5432. If the fault isn't quickly diagnosable, terminating the instance is a valid response — the ASG launches a clean replacement from the Golden AMI, which is the intended behavior of a disposable compute tier. Diagnosis matters most when the fault is likely to recur on the replacement.

## Handling scaling events

Scaling activity is visible in the ASG's **Activity History**, which records every launch/termination and its reason. Expected scale-out sequence: launch → Target Group registration → health checks → traffic. An instance stuck unhealthy after launch usually indicates the AMI or application configuration has drifted from what the health check expects.

## Configuration values worth confirming

These settings are not recorded in the project's build documentation, and each one changes the system's actual failure behavior described in [`docs/scalability-availability.md`](scalability-availability.md):

| Setting | Why it matters | Where to check |
|---|---|---|
| RDS Multi-AZ enabled? | Determines whether database failure is automatic failover or a full outage | RDS console → instance configuration |
| RDS backup retention | Determines whether data loss/corruption is recoverable at all | RDS console → Maintenance & backups |
| ASG health check type (`EC2` vs `ELB`) | With `EC2` only, an instance with a dead Nginx is removed from ALB rotation but **never replaced** | Auto Scaling Group console → Advanced configuration |
| Target Group health-check path | Determines whether "healthy" means the full stack (API + DB) or just Nginx | Target Group console → Health checks |
| Network ACL configuration | Determines whether a second layer of subnet-level filtering exists at all | VPC console → Network ACLs |

## Logging — the biggest blind spot

No centralized logging is configured: no CloudWatch Logs agent on instances, no ALB access logs, no WAF logging destination, no RDS log export. Application and Nginx logs live **only** on the instance that produced them, and a scaling event can terminate that instance — taking its logs with it. **Investigating a fault requires reaching the instance before it is replaced.** If you are actively debugging a failing instance that the ASG might terminate, consider temporarily suspending the ASG's `ReplaceUnhealthy` process for that instance so it stays available for inspection, and enable CloudWatch Logs / ALB access logging as a permanent fix (see [`docs/monitoring.md`](monitoring.md#recommendations)).

## Verifying behavior safely (suggested, not yet performed)

| What to verify | Suggested method | Risk |
|---|---|---|
| Auto Scaling scale-out | Generate CPU load on an instance (e.g., `stress-ng`) or manually raise desired capacity, then watch Activity History and the Target Group | Low — reduce desired capacity afterward |
| RDS Multi-AZ failover | Use the RDS console's "Reboot with failover" action on a **non-production** instance | Causes a brief connection interruption by design — do not run against live traffic without a maintenance window |
| CloudWatch alarm firing | Temporarily lower a threshold (e.g., `HealthyHostCount < 3`) to force an ALARM state, confirm the SNS email arrives, then restore the threshold | Low, but will generate a real notification |
| WAF admin exception | Once implemented, test both an allowed request from an admin IP and a blocked request from an arbitrary IP | Low |
| CloudFront cache behavior | Request the same static asset twice and inspect the `X-Cache` response header (`Hit from cloudfront` / `Miss from cloudfront`) | None |
