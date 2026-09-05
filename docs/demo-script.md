# Demonstration Script

A full recorded walkthrough of the deployed infrastructure exists — see [`docs/video/README.md`](video/README.md) for the hosting link. This document is the **companion outline** for that recording: a topic checklist covering what a complete walkthrough should show, useful for jumping to a specific section or for re-recording/extending the video later. It only includes features the project documentation records as actually implemented; it does not include Route 53, HTTPS, or any other planned-but-not-deployed component (see [`docs/architecture.md`](architecture.md#known-documentation-discrepancies)).

> If you add timestamps for the recorded video against each numbered section below, this file becomes a clickable table of contents for it.

## 1. Architecture overview (1–2 min)

Show [`docs/architecture/aws-architecture.png`](architecture/aws-architecture.png) and narrate the layers top to bottom: users → CloudFront → WAF → ALB → Auto Scaling Group (private subnets, 2 AZs) → RDS PostgreSQL (Multi-AZ, isolated subnets), with CloudWatch/SNS/Systems Manager as a separate control plane on the side. Call out explicitly that Route 53/HTTPS are marked "planned, not implemented."

## 2. Application access (1 min)

Open the application's AWS-generated endpoint in a browser over HTTP. Show the Next.js frontend loading, then trigger an action that calls the API (`/api/...`) to show the FastAPI backend responding through the same origin.

## 3. Load balancing (2 min)

In the AWS Console, open the **Target Group** and show both registered EC2 targets in a `healthy` state. Open the **ALB** listener configuration and point out the single HTTP:80 listener forwarding to that Target Group.

## 4. EC2 / compute layer (2 min)

Open the **Launch Template** and show the AMI, instance type (`t3.small`), attached security group (`ec2-sg`), and IAM instance profile (`LuminaEC2SSMRole`). Open **EC2 → Instances** and show both running instances have no public IP address.

## 5. Auto Scaling (2–3 min)

Open the **Auto Scaling Group** and show min/desired/max = 2/2/6 and the target-tracking CPU policy. If demonstrating live: generate CPU load on one instance and show the ASG's Activity History launching a new instance, registering it with the Target Group, and passing health checks before the ALB begins routing to it (see the safe-verification note in [`docs/troubleshooting.md`](troubleshooting.md#verifying-behavior-safely-suggested-not-yet-performed)).

## 6. Database (1–2 min)

Open the **RDS** console and show the instance in the private DB subnet group, engine PostgreSQL, and (if confirmed) the Multi-AZ setting. Do **not** claim Multi-AZ is active unless it is visibly confirmed in the console at demo time — the source documentation does not verify this (see [`docs/architecture.md`](architecture.md#database-layer)).

## 7. Security groups (2 min)

Open `alb-sg`, `ec2-sg`, and `rds-sg` in the console side by side and show the chain: `alb-sg` accepts `0.0.0.0/0:80`; `ec2-sg` accepts port 80 **only** from `alb-sg`; `rds-sg` accepts port 5432 **only** from `ec2-sg`. Point out there is no inbound SSH rule anywhere.

## 8. AWS WAF (2–3 min)

Open the Web ACL `dental-waf` and show the rule list and priority order. Demonstrate the blocking behavior live: request `/admin` and show the `403 Forbidden` response, then open **WAF → Sampled requests** and show the matched rule (`AdminProtection_URIPATH`, action `BLOCK`). Explain the three COUNT-mode rules (Anti-DDoS, rate-based, body-size) and that they currently observe rather than block.

## 9. Systems Manager (2 min)

From **Systems Manager → Managed Nodes**, show an instance with `Ping Status: Online`, then start a **Session Manager** session and run `hostname`, `sudo systemctl status nginx`, and `sudo ss -tulpn` live to demonstrate administrative access with no SSH, no key, and no public IP.

## 10. CloudWatch (2 min)

Open **CloudWatch → Alarms** and show all seven alarms in the `OK` state, with their metrics, statistics, and thresholds. Optionally trigger one safely per the method in [`docs/troubleshooting.md`](troubleshooting.md#verifying-behavior-safely-suggested-not-yet-performed) and show the resulting SNS email.

## 11. Resilience / failover (2 min, optional — requires prior verification)

If RDS Multi-AZ has been confirmed enabled, this is the moment to either show the console setting or (in a non-production context) perform a "Reboot with failover" and narrate the endpoint-based reconnection behavior described in [`docs/scalability-availability.md`](scalability-availability.md#failure-scenario-database-failure). If Multi-AZ has not been verified, skip this step rather than asserting it — do not claim failover works without having shown it.

---

**Total suggested runtime:** ~18–22 minutes for the full sequence, or ~8–10 minutes for a condensed version covering only steps 1, 2, 3, 5, 7, and 8.
