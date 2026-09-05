# Security Architecture

## Defense-in-depth model

The architecture layers independent controls so that no single misconfiguration exposes the application:

| Layer | Control | What it addresses |
|---|---|---|
| 1 | Amazon CloudFront | Controlled edge entry point |
| 2 | AWS WAF | Layer 7 inspection — common exploits, SQL injection, admin-path scanning, abusive request rates |
| 3 | Application Load Balancer | Single public entry point; EC2 instances are never addressed directly |
| 4 | Security groups (`alb-sg` → `ec2-sg` → `rds-sg`) | Tier-to-tier network authorization |
| 5 | Subnet / route-table isolation | No internet route to the compute or database tiers |
| 6 | Application authentication | Identity verification |
| 7 | Application authorization | Role verification (e.g., admin role) |
| 8 | MFA (where supported) | Additional factor for administrative accounts |

Layers 6–8 are application-level controls; the build documentation identifies them as the required primary protection for administrative functionality but does not record their implementation state, so this document makes no claim about them either way.

## Security group chain

```
Internet ──TCP 80──▶ alb-sg ──TCP 80 (source: alb-sg)──▶ ec2-sg ──TCP 5432 (source: ec2-sg)──▶ rds-sg
```

| Security group | Inbound | Outbound |
|---|---|---|
| `alb-sg` | TCP 80 from `0.0.0.0/0` (TCP 443 planned, once TLS is configured) | All traffic to `0.0.0.0/0` |
| `ec2-sg` | TCP 80 from `alb-sg` **only**. No `TCP 80` or `TCP 22` from `0.0.0.0/0`. | All traffic to `0.0.0.0/0` |
| `rds-sg` | TCP 5432 from `ec2-sg` **only**. No `TCP 5432` from `0.0.0.0/0`. | All traffic to `0.0.0.0/0` |

The inbound rule on `ec2-sg` and `rds-sg` authorizes traffic by **security-group membership**, not by IP range. This matters specifically because instance IP addresses under Auto Scaling change continuously: every instance the ASG launches is automatically authorized (it inherits `ec2-sg` from the Launch Template), and nothing outside that group is authorized regardless of its address — there is no CIDR list to maintain as the fleet changes.

### Traffic matrix

| Path | Status |
|---|---|
| Internet → ALB :80 | **ALLOWED** |
| Internet → ALB :443 | Allowed later, once TLS is configured |
| ALB → EC2 :80 | **ALLOWED** |
| Internet → EC2 (any port) | **BLOCKED** |
| Internet → EC2 :22 (SSH) | **BLOCKED** — no inbound SSH rule exists anywhere |
| EC2 → RDS :5432 | **ALLOWED** |
| Internet → RDS :5432 | **BLOCKED** |
| EC2 → Internet | ALLOWED, via NAT Gateway (outbound only) |
| RDS → Internet | **NOT ROUTED** — the DB subnet route tables carry no internet route in either direction |
| ALB → RDS | BLOCKED / not required |

Outbound rules on all three groups permit all traffic — the AWS default, which allows instances to reach Systems Manager, package repositories, and RDS. Egress filtering is not implemented; see [Recommendations](#recommendations) for VPC endpoints as the standard tightening.

## Network isolation as a control independent of security groups

The private database subnets' route tables (`private-db-rt-az1`, `private-db-rt-az2`) contain **only** the VPC-local route — no `0.0.0.0/0` route to a NAT Gateway or Internet Gateway exists. This is deliberate and important: **even if `rds-sg` were later misconfigured** to permit `0.0.0.0/0` on port 5432, there is no network path by which internet traffic could reach the database subnets. Routing and security groups are independent, reinforcing layers here, not two expressions of the same control.

## No direct public access to application instances

EC2 instances hold no public IP address and no inbound rule for ports 80 or 22 from `0.0.0.0/0`. The only path to an instance's port 80 is through `alb-sg`. FastAPI additionally binds to `127.0.0.1:8000` (loopback only), so the API process is unreachable off-host at the operating-system level — a host-level control that reinforces, rather than duplicates, the network-level ones.

## AWS Systems Manager — no inbound SSH

| Property | Value |
|---|---|
| IAM role | `LuminaEC2SSMRole` |
| Trusted entity | AWS service → EC2 |
| Attached policy | `AmazonSSMManagedInstanceCore` (AWS managed — least-privilege for this function) |
| Attachment | EC2 instance profile, referenced in the Launch Template |

Because the instance profile is declared in the Launch Template, **every** instance the ASG launches — including unattended replacements after a failure — becomes manageable through Session Manager automatically, with no manual per-instance configuration. Session Manager requires only **outbound HTTPS (TCP 443)** from the instance; it requires **no inbound connection of any kind**. For private instances, that outbound path is provided by the existing NAT Gateway. The practical result: `ec2-sg` needs no inbound rule beyond port 80 from the ALB — there is no SSH port to attack, no bastion host to patch, and no public IP on any application instance.

Verification performed during the build: SSM Agent status confirmed via `sudo systemctl status amazon-ssm-agent` (`Active: active (running)`); the instance appeared under **Systems Manager → Managed Nodes** with **Ping Status: Online**; an interactive session was opened and validated with `hostname`, `whoami`, `pwd`, `uname -a`, and the application was inspected with `sudo systemctl status nginx` and `sudo ss -tulpn`.

## AWS WAF

The Web ACL (`dental-waf`) combines four AWS managed rule groups with five custom rules, evaluated in priority order.

| Rule | Type | Capacity | Mode | Function |
|---|---|---|---|---|
| `AWS-AWSManagedRulesAntiDDoSRuleSet` | AWS managed | 50 WCU | **COUNT** | Layer 7 anti-DDoS visibility |
| `dental-waf_IPV4_Allow` | Custom IP set | 1 WCU | — | Explicit allow for trusted IPv4 addresses |
| `dental-waf_IPV6_Allow` | Custom IP set | 1 WCU | — | Explicit allow for trusted IPv6 addresses |
| `dental-waf_IPV4_Block` | Custom IP set | 1 WCU | — | Explicit block for unwanted IPv4 addresses |
| `dental-waf_IPV6_Block` | Custom IP set | 1 WCU | — | Explicit block for unwanted IPv6 addresses |
| `GeoRule` | Custom | 1 WCU | — | Restrict traffic by request's geographic origin |
| `GlobalRateBasedRule` | Custom, rate-based | 2 WCU | **COUNT** | Monitors global request rate — scanners, flooding, abuse |
| `BodySizeRestrictionRule` | Custom | 1 WCU | **COUNT** | Flags excessive request payload size |
| `AWS-AWSManagedRulesCommonRuleSet` | AWS managed | 700 WCU | Block | Common web-application attack patterns |
| `AWS-AWSManagedRulesSQLiRuleSet` | AWS managed | 200 WCU | Block | SQL injection detection — relevant since the backend talks to PostgreSQL |
| `AWS-AWSManagedRulesAdminProtectionRuleSet` | AWS managed | 100 WCU | Block | Protects commonly targeted administrative URI paths |

**Actively mitigated (blocking):** SQL injection, common web exploits, administrative path scanning, specific untrusted IPs (to the extent populated), geographic restriction.

**Observed but not blocked (COUNT mode):** Layer 7 DDoS patterns, excessive request rates, oversized request bodies. COUNT mode is a legitimate rollout practice — it lets real traffic be observed before tuning thresholds that could otherwise block legitimate users — but it must not be read as active protection. **The architecture currently records rate-based abuse and oversized payloads; it does not block them.**

### Validation performed

Two pieces of real evidence were captured, rather than assumed:

1. **Admin path blocking.** `GET /admin` returned **HTTP 403 Forbidden**. WAF sampled requests attributed this to rule group `AWS-AWSManagedRulesAdminProtectionRuleSet`, matched rule `AdminProtection_URIPATH`, action `BLOCK`. This confirmed the 403 originated at WAF, not at the ALB, EC2, Nginx, or FastAPI.
2. **Live scanner traffic.** An automated scanner (source `198.235.24.71`, US, Palo Alto Networks Cortex Xpanse user agent) reached the public endpoint at `/` and was `ALLOW`ed, because the URI matched no blocking rule. This confirms the public-facing infrastructure receives real internet traffic and that WAF is actively inspecting it — expected behavior for any internet-facing endpoint, not evidence of a breach.

### Known conflict: Admin Protection blocks the application's own admin panel

`AWSManagedRulesAdminProtectionRuleSet` currently blocks `/admin` — the application's own legitimate admin panel — because that path is exactly what the managed rule exists to protect against. The documented remediation plan (not yet implemented) is a **narrowly scoped exception**, not disabling the rule group:

- Create an IP set `lumina-admin-allowed-ips` containing `/32` entries for authorized administrator devices.
- Position the exception **ahead of** the Common Rule Set and SQLi rules in priority order, but ensure it does **not** use an unrestricted, terminating `ALLOW` — WAF `ALLOW` actions are terminating and would stop subsequent rules from evaluating that request, silently exempting admin traffic from SQLi/Common Rule Set inspection.
- Intended priority order: admin exception → Common Rule Set → SQLi → Admin Protection → remaining rules.
- IP allowlisting is explicitly documented as an **additional** layer, not a replacement for authentication: ISP-assigned addresses are frequently dynamic, so authentication, authorization, and MFA remain the primary controls for the admin panel.

**Current status: planned, not implemented.** The practical consequence today is that the admin panel is unreachable through the WAF-protected path.

## What is not managed by a secrets service

Database credentials (`DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`) are supplied through application configuration captured in the AMI. The build documentation itself identifies **AWS Secrets Manager**, retrieved at runtime via the EC2 IAM role, as the correct production mechanism — but records this as **not implemented**. Practical consequences: credential rotation requires rebuilding the AMI, and anyone who can launch an instance from the AMI can read the stored credentials.

## Transport security

**No HTTPS.** No ACM certificate and no ALB HTTPS listener exist, because no domain was purchased (see [`docs/architecture.md`](architecture.md#known-documentation-discrepancies)). Client-to-ALB traffic is unencrypted HTTP. For an application with an authenticated admin panel, this is the most significant security gap in the current deployment. The full remediation path — domain purchase → Route 53 Hosted Zone → ACM certificate → ALB HTTPS listener → HTTP→HTTPS redirect — is fully specified in [`docs/deployment.md`](deployment.md#completing-the-https-chain-not-yet-executed).

## Network ACLs — unverified

The original diagram's security legend states "NACLs for Subnet Level Control," and NACLs appear in the list of target-architecture components. However, **no NACL rules, names, or subnet associations are documented anywhere** in the project's build material. Whether custom NACLs exist, or the default VPC NACLs (which permit all traffic) remain in place, cannot be determined from the available evidence.

## Recommendations

These are recommendations only — **none of them are currently implemented**:

1. **Close the HTTPS gap** — purchase a domain, provision Route 53 + ACM, add an ALB HTTPS listener, redirect port 80 to 443.
2. **Implement the planned Admin Protection exception** with `lumina-admin-allowed-ips`, positioned so authorized admin traffic still passes through the Common Rule Set and SQLi inspection.
3. **Move database credentials to AWS Secrets Manager**, retrieved at runtime via the existing EC2 IAM role.
4. **Transition the three COUNT-mode WAF rules to BLOCK** once the counters provide enough traffic data to set safe thresholds.
5. **Restrict ALB ingress to CloudFront only** so the origin cannot be reached directly, bypassing WAF (relevant if the Web ACL is associated with CloudFront rather than the ALB — see the diagram discrepancy in [`docs/architecture.md`](architecture.md#known-documentation-discrepancies)).
6. **Add VPC endpoints for Systems Manager** (`ssm`, `ssmmessages`, `ec2messages`) to remove the dependency on NAT Gateway egress for administrative access.
7. **Confirm or document Network ACL configuration.**
