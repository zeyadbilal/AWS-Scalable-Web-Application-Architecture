"""
Regenerates docs/architecture/aws-architecture.png (+ .svg) using the official
AWS Architecture Icons, via the `diagrams` Python package (https://diagrams.mingrammer.com/).

Reflects the architecture strictly as documented in docs/architecture.md — nothing
here is invented; components labeled "planned, not implemented" are drawn as such.

Usage:
    pip install diagrams
    # Graphviz must also be installed and on PATH (e.g. `winget install Graphviz.Graphviz`)
    python generate_diagram.py
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import (
    CloudFront,
    InternetGateway,
    NATGateway,
    ElbApplicationLoadBalancer,
    Route53,
)
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.security import WAF, CertificateManager
from diagrams.aws.management import Cloudwatch, CloudwatchAlarm, SystemsManager
from diagrams.aws.integration import SNS
from diagrams.aws.general import Users, User

FONT = "Helvetica,Arial,sans-serif"

graph_attr = {
    "fontsize": "24",
    "fontname": FONT,
    "bgcolor": "white",
    "pad": "0.5",
    "nodesep": "0.8",
    "ranksep": "1.0",
    "compound": "true",
    "newrank": "true",
}
node_attr = {"fontname": FONT, "fontsize": "12", "margin": "0.2,0.12"}
edge_attr = {"fontname": FONT, "fontsize": "10"}

c_vpc = {"fontname": FONT, "fontsize": "15", "bgcolor": "#F2F6FF", "pencolor": "#6B4FBB", "style": "dashed", "labeljust": "l"}
c_az = {"fontname": FONT, "fontsize": "13", "bgcolor": "#EAF2FF", "pencolor": "#3B82C4", "style": "dashed", "labeljust": "l"}
c_public = {"fontname": FONT, "fontsize": "11", "bgcolor": "#E9F7EC", "pencolor": "#3C9A5F", "labeljust": "l"}
c_app = {"fontname": FONT, "fontsize": "11", "bgcolor": "#EAF2FF", "pencolor": "#3B82C4", "labeljust": "l"}
c_db = {"fontname": FONT, "fontsize": "11", "bgcolor": "#EDEAFB", "pencolor": "#6B4FBB", "labeljust": "l"}
c_planned = {"fontname": FONT, "fontsize": "11", "bgcolor": "#F2F2F2", "pencolor": "#9E9E9E", "style": "dashed", "fontcolor": "#B00020", "labeljust": "l"}
c_monitor = {"fontname": FONT, "fontsize": "13", "bgcolor": "#FDECEC", "pencolor": "#C0273C", "style": "dashed", "labeljust": "l"}

RED_DASH = {"style": "dashed", "color": "#C0273C"}
GRAY_DOT = {"style": "dotted", "color": "#6B7280"}
PURPLE_DASH = {"style": "dashed", "color": "#6B4FBB"}

with Diagram(
    "Lumina Dental — AWS Solution Architecture (As Implemented)",
    filename="aws-architecture",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    outformat=["png", "svg"],
):

    users = Users("Users / Clients")

    with Cluster("PLANNED — NOT IMPLEMENTED\n(no domain purchased — served over HTTP)", graph_attr=c_planned):
        route53 = Route53("Route 53 (DNS)")
        acm = CertificateManager("ACM (TLS)\nALB :443 listener")
    route53 - Edge(style="invis") - acm

    cf = CloudFront("CloudFront\nEdge cache · origin = ALB")
    waf = WAF("AWS WAF\nWeb ACL: dental-waf")
    igw = InternetGateway("aws-project-igw")
    alb = ElbApplicationLoadBalancer("ALB\ninternet-facing · HTTP :80")

    users >> Edge(label="HTTPS") >> cf
    cf >> Edge(label="Layer 7 inspection", **RED_DASH) >> waf
    cf >> igw >> alb
    # keep the "planned" callout visually near the edge nodes without pulling layout
    igw - Edge(style="invis") - route53

    with Cluster("Amazon VPC · aws-project-vpc · 10.0.0.0/16", graph_attr=c_vpc):

        with Cluster("Availability Zone 1", graph_attr=c_az):
            with Cluster("Public-Subnet-AZ1 · 10.0.1.0/24", graph_attr=c_public):
                nat1 = NATGateway("NAT GW (AZ-1)\n+ dedicated EIP")
            with Cluster("Private-App-Subnet-AZ1 · 10.0.11.0/24\nAuto Scaling Group: dental-asg", graph_attr=c_app):
                ec2_a1 = EC2("EC2 t3.small")
                ec2_a2 = EC2("EC2 t3.small")
            with Cluster("Private-DB-Subnet-AZ1 · 10.0.21.0/24 (isolated)", graph_attr=c_db):
                rds_primary = RDSPostgresqlInstance("RDS PostgreSQL\nPrimary")

            nat1 >> Edge(label="outbound only", **GRAY_DOT, dir="back") >> ec2_a1
            nat1 >> Edge(**GRAY_DOT, dir="back") >> ec2_a2
            ec2_a1 >> Edge(label="TCP 5432") >> rds_primary
            ec2_a2 >> Edge(**{"style": "solid"}) >> rds_primary

        with Cluster("Availability Zone 2", graph_attr=c_az):
            with Cluster("Public-Subnet-AZ2 · 10.0.2.0/24", graph_attr=c_public):
                nat2 = NATGateway("NAT GW (AZ-2)\n+ dedicated EIP")
            with Cluster("Private-App-Subnet-AZ2 · 10.0.12.0/24\nAuto Scaling Group: dental-asg", graph_attr=c_app):
                ec2_b1 = EC2("EC2 t3.small")
                ec2_b2 = EC2("EC2 t3.small")
            with Cluster("Private-DB-Subnet-AZ2 · 10.0.22.0/24 (isolated)", graph_attr=c_db):
                rds_standby = RDSPostgresqlInstance("RDS PostgreSQL\nStandby (Multi-AZ)")

            nat2 >> Edge(label="outbound only", **GRAY_DOT, dir="back") >> ec2_b1
            nat2 >> Edge(**GRAY_DOT, dir="back") >> ec2_b2
            ec2_b1 >> Edge(style="invis") >> rds_standby
            ec2_b2 >> Edge(style="invis") >> rds_standby

        alb >> Edge(label="HTTP :80") >> ec2_a1
        alb >> Edge() >> ec2_a2
        alb >> Edge(label="HTTP :80") >> ec2_b1
        alb >> Edge() >> ec2_b2

        rds_primary >> Edge(label="synchronous replication\nautomatic failover promotes standby", constraint="false", **PURPLE_DASH) >> rds_standby

    with Cluster("Monitoring & Management (control plane)", graph_attr=c_monitor) as monitor:
        admin = User("Administrator\n(AWS Console)")
        ssm = SystemsManager("Systems Manager\nSession Manager\nvia LuminaEC2SSMRole")
        cw = Cloudwatch("CloudWatch\nASG / ALB / TG / RDS metrics")
        alarm = CloudwatchAlarm("CloudWatch Alarms\n7 alarms · 5-min period")
        sns = SNS("SNS Topic\n→ email subscription")

        admin >> ssm
        cw >> alarm >> sns
        ssm - Edge(style="invis") - cw
