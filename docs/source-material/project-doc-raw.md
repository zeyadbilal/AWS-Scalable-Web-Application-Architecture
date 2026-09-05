```
============================================================
LUMINA DENTAL - EC2 + NGINX + APPLICATION + RDS POSTGRESQL
PRE-AMI CONFIGURATION / GOLDEN IMAGE DOCUMENTATION
============================================================
```

```
PROJECT ARCHITECTURE
====================
```

```
The current stage prepares the EC2 instance to become the Golden
AMI used later by the Launch Template and Auto Scaling Group.
```

```
The target AWS architecture is an EC2-based scalable web application
running inside a properly architected VPC with public and private
subnets across multiple Availability Zones. The application uses
EC2 instances for compute, Nginx as the web/reverse-proxy layer,
Next.js as the frontend, FastAPI as the backend/API layer, and
Amazon RDS PostgreSQL as the managed database backend.
```

```
The final architecture is intended to use ALB + ASG for high
availability and scalability, while RDS Multi-AZ provides database
availability and automated failover.
```

```
Current application flow:
```



```
============================================================
1. EC2 INSTANCE
============================================================
```

```
The EC2 instance was prepared as the application server and later
will be used as the source for the Golden AMI.
```

```
The EC2 instance currently contains:
```

```
- Next.js frontend application
- FastAPI backend application
- Python virtual environment for the backend
- Uvicorn application server
```

- `Nginx reverse proxy` 

- `Required application dependencies` 

- `Application configuration/environment variables` 

- `Connectivity configuration to Amazon RDS PostgreSQL` 

```
The EC2 instance was tested successfully before creating the AMI.
```

```
The following services were confirmed to be listening:
```

```
127.0.0.1:8000
```

```
    FastAPI backend running through Uvicorn
```

# `*:3000` 

```
    Next.js frontend
```

- `0.0.0.0:80` 

```
    Nginx
```

```
0.0.0.0:22 / [::]:22
    SSH
```

```
============================================================
2. FASTAPI BACKEND
```

```
============================================================
```

```
The backend is implemented using FastAPI and is running through
Uvicorn.
```

```
The backend is intentionally bound to:
```

# `127.0.0.1:8000` 

```
This means the FastAPI service is not directly exposed to the
Internet.
```

```
A local health check was performed using:
```

```
curl http://127.0.0.1:8000
```

```
The backend successfully returned:
```

```
{"status":"ok","service":"Lumina Dental API"}
```

```
This confirmed that the FastAPI application was running correctly
inside the EC2 instance.
```

```
The backend is therefore accessed internally through Nginx instead
of exposing port 8000 directly to the Internet.
```

```
============================================================
3. NEXT.JS FRONTEND
```

```
============================================================
```

```
The frontend is implemented using Next.js and is running on:
```

# `*:3000` 

```
The Next.js production application was successfully built and
started.
```

```
The frontend is not intended to be directly exposed to the Internet
through port 3000.
```

```
Instead, Nginx receives HTTP requests on port 80 and forwards frontend
requests internally to:
```

```
http://127.0.0.1:3000
```

```
============================================================
4. NGINX ROLE
```

```
============================================================
```

```
Nginx is used as the reverse proxy and the main HTTP entry point
for the application on the EC2 instance.
```

```
Nginx listens on:
```

# `0.0.0.0:80` 

```
The main Nginx configuration is located at:
```

```
/etc/nginx/nginx.conf
```

```
The application-specific configuration is located at:
```

```
/etc/nginx/conf.d/lumina.conf
```

```
The main nginx.conf includes:
```

```
include /etc/nginx/conf.d/*.conf;
```

```
Therefore, lumina.conf is loaded automatically by Nginx.
```

```
============================================================
```

# `5. NGINX ROUTING` 

```
============================================================
```

```
The application-specific Nginx configuration contains two important
locations:
```

```
LOCATION 1:
    /
```

```
This location forwards normal web requests to the Next.js frontend:
```

```
proxy_pass http://127.0.0.1:3000;
```

```
Therefore:
```

```
Browser
   |
   v
EC2 Public IP :80
   |
   v
Nginx
   |
   v
127.0.0.1:3000
   |
   v
Next.js
```

```
LOCATION 2:
    /api/
```

```
This location forwards API requests to the FastAPI backend:
```

```
proxy_pass http://127.0.0.1:8000/;
```

```
Therefore:
```

```
Browser
   |
   v
EC2 Public IP :80
   |
   v
Nginx /api/
   |
   v
127.0.0.1:8000
   |
   v
FastAPI
```

```
The important architectural benefit is that both frontend and
backend are accessed through the same public HTTP endpoint while
the backend remains bound to localhost.
```

```
The external user does not need to access:
```

```
EC2_PUBLIC_IP:3000
```

```
or:
```

```
EC2_PUBLIC_IP:8000
```

```
Instead, the user accesses:
```

```
http://EC2_PUBLIC_IP/
```

```
and Nginx internally decides whether the request belongs to the
frontend or backend API.
```

```
============================================================
6. FRONTEND TO BACKEND COMMUNICATION
============================================================
```

```
The final application communication path is:
```

```
USER BROWSER
    |
    | HTTP request
    v
EC2 PUBLIC IP :80
    |
    v
NGINX
    |
    +--------------------------+
    |                          |
    | /                        | /api/
    v                          v
NEXT.JS :3000              FASTAPI :8000
```

```
                               |
                               v
                         DATABASE CONNECTION
                               |
                               v
                       AMAZON RDS POSTGRESQL
```

```
The frontend communicates with the backend through the Nginx
reverse-proxy path instead of directly exposing the backend port.
```

```
This keeps the application architecture cleaner and prevents the
FastAPI service from being directly reachable from the Internet.
```

```
============================================================
7. AMAZON RDS POSTGRESQL
```

```
============================================================
```

```
The database layer is implemented using Amazon RDS PostgreSQL.
```

```
The application database is moved away from the EC2 instance and
managed by Amazon RDS.
```

```
The EC2 instances do not store the production database locally.
```

```
Instead, FastAPI connects to the RDS PostgreSQL endpoint.
```

```
The logical connection is:
```

```
FastAPI
   |
   | PostgreSQL connection
```

```
   v
RDS PostgreSQL Endpoint
   |
   v
RDS Database
```

```
The backend configuration must contain the RDS connection information,
including the RDS endpoint, PostgreSQL port, database name, username,
and password/credentials.
```

```
The standard PostgreSQL port is:
```

```
5432
```

```
============================================================
8. RDS PRIMARY + STANDBY ARCHITECTURE
```

```
============================================================
```

```
The intended architecture uses one active primary database and a
standby database containing synchronized data for high availability.
```

```
The application does NOT connect separately to two database endpoints.
Instead, the application connects to the RDS service endpoint.
```

```
Conceptually:
```

```
                      v
              RDS DATABASE ENDPOINT
                      |
              +-------+-------+
              |               |
              v               v
          PRIMARY          STANDBY
           DB                DB
              \               /
               \             /
                SYNCHRONIZED
                   DATA
```

```
The standby database is not intended to be directly used by the
application under normal operation.
```

```
If the primary database becomes unavailable, Amazon RDS performs the
appropriate failover mechanism and the application continues using
the RDS endpoint.
```

```
This is why the backend should use the RDS endpoint rather than
hard-coding a specific database instance address.
```

```
============================================================
9. RDS NETWORK CONNECTIVITY
============================================================
```

```
RDS should be placed inside the private database subnet(s).
```

```
The database should not be publicly accessible from the Internet.
```

```
The intended traffic flow is:
```

```
Internet
   |
   v
ALB
   |
   v
EC2 / ASG
   |
   v
RDS PostgreSQL
```

```
The RDS Security Group should allow PostgreSQL traffic on:
```

```
TCP 5432
```

```
from the EC2 application Security Group.
Conceptually:
```

```
EC2-SG
   |
   | TCP 5432
   v
RDS-SG
```

```
The RDS Security Group should NOT allow:
```

```
0.0.0.0/0 : 5432
```

```
This ensures that only the application servers that belong to the
authorized EC2 Security Group can establish database connections.
```

```
============================================================
10. DATABASE CONNECTION FROM EC2
============================================================
```

```
The backend application running inside EC2 establishes the database
connection using the RDS PostgreSQL endpoint.
```

```
The logical configuration is:
```

```
DATABASE_HOST=<RDS_ENDPOINT>
DATABASE_PORT=5432
DATABASE_NAME=<DATABASE_NAME>
DATABASE_USER=<DATABASE_USER>
DATABASE_PASSWORD=<DATABASE_PASSWORD>
```

```
The actual credentials should not be unnecessarily exposed inside
the application source code.
```

```
For the final production architecture, AWS Secrets Manager can be
used to store database credentials, while the EC2 IAM Role allows
the application to retrieve the required secret securely.
```

```
============================================================
11. DATABASE SECURITY MODEL
```

```
============================================================
```

```
The database is private and accessible only from the application
layer.
```

```
The intended security model is:
```

```
Internet
   |
   v
ALB
   |
   v
EC2 Security Group
   |
   | PostgreSQL 5432
   v
RDS Security Group
   |
   v
RDS PostgreSQL
```

```
The database is therefore isolated from direct Internet access.
```

```
The application server is the only layer that needs database
connectivity.
```

```
============================================================
12. EC2 SECURITY GROUP
```

# `============================================================` 

```
The EC2 Security Group should expose only the required services.
Expected public/application access:
```

```
TCP 80
    HTTP access to Nginx
TCP 443
    HTTPS access when SSL/TLS is configured
```

```
TCP 22
    SSH access only when required and preferably restricted to the
    administrator's IP or replaced by AWS Systems Manager Session
    Manager in the final architecture.
```

```
Ports 3000 and 8000 should NOT be publicly exposed.
They are internal application ports:
3000 -> Next.js
8000 -> FastAPI
```

```
============================================================
13. NGINX + APPLICATION PORT MODEL
============================================================
The final local EC2 port model is:
PORT 80
    Nginx
    Public entry point
PORT 3000
    Next.js
    Internal application service
PORT 8000
    FastAPI/Uvicorn
    Internal API service
PORT 5432
    PostgreSQL
    Remote connection from EC2 to RDS
```

```
The complete request path is therefore:
HTTP request
    |
    v
Nginx :80
    |
    +---- "/" ------> Next.js :3000
    |
    +---- "/api/" --> FastAPI :8000
                           |
                           v
                     RDS PostgreSQL :5432
```

```
============================================================
```

```
14. VALIDATION PERFORMED BEFORE AMI
============================================================
```

```
The EC2 application stack was tested before creating the image.
```

```
Backend test:
```

```
curl http://127.0.0.1:8000
```

```
Result:
```

```
{"status":"ok","service":"Lumina Dental API"}
```

```
This confirmed that the backend service is operational.
```

```
The frontend was also confirmed to be accessible through the EC2
public IP.
```

```
The frontend successfully communicated with the backend through the
Nginx reverse proxy.
```

```
The complete application flow was verified:
```

```
Browser
   ->
EC2 Public IP
   ->
Nginx
   ->
Next.js
   ->
/api/
   ->
FastAPI
   ->
RDS PostgreSQL
```

```
============================================================
15. REBOOT TEST
============================================================
```

```
A reboot test was performed before considering the EC2 ready for
the AMI.
```

```
After rebooting the EC2 instance, the required application services
were confirmed to return successfully.
```

```
The important services were:
```

```
Nginx
Next.js
FastAPI/Uvicorn
```

```
The successful reboot test is important because the future AMI will
be used by the Launch Template and Auto Scaling Group.
```

```
New EC2 instances must be able to start the application stack
correctly without depending on manually started terminal processes.
```

```
============================================================
16. GOLDEN AMI PURPOSE
```

```
============================================================
```

```
The current EC2 instance represents the validated application
baseline.
```

```
The AMI created from this instance will serve as the Golden Image
for the application servers.
```

```
The AMI contains the application environment required for the
compute layer, including:
```

- `Operating system configuration` 

```
- Application source/build
```

```
- Next.js frontend
```

```
- FastAPI backend
```

```
- Python virtual environment/dependencies
```

```
- Nginx configuration
```

```
- Required packages
```

- `Application configuration required for startup` 

```
The database itself is NOT part of the AMI.
```

```
The database is an external managed AWS resource:
```

```
Amazon RDS PostgreSQL
```

```
Therefore, every EC2 instance launched from the AMI will run the
same application stack and connect to the same RDS database.
```

```
============================================================
17. GOLDEN AMI + AUTO SCALING CONCEPT
============================================================
```

```
After the AMI is created, it will be used by the Launch Template.
```

```
The Launch Template will define how new EC2 instances are launched.
```

```
The Auto Scaling Group will then use that Launch Template to create
and manage multiple application instances.
```

```
Final compute architecture:
```

```
                    ALB
                     |
             +-------+-------+
             |               |
             v               v
          EC2 #1          EC2 #2
        AMI-based       AMI-based
        application     application
             |               |
             +-------+-------+
                     |
                     v
              RDS PostgreSQL
              Primary/Standby
```

```
This ensures that all EC2 instances use the same validated
application environment.
```

```
============================================================
18. FINAL TARGET ARCHITECTURE
============================================================
```

```
The project target architecture, as defined for the scalable
web application, is:
```

```
                         INTERNET
                     CloudFront
             +--------------+--------------+
             |                             |
             v                             v
          EC2 #1                         EC2 #2
       Auto Scaling                    Auto Scaling
             |                             |
             +--------------+--------------+
                     RDS PostgreSQL
                    Primary/Standby
```

```
Additional AWS services in the target architecture include:
```

```
VPC
Public and Private Subnets
NAT Gateway
Security Groups
NACLs
EC2
Launch Template
Auto Scaling Group
Application Load Balancer
AWS WAF
CloudFront
RDS Multi-AZ
Route 53
Systems Manager
CloudWatch
SNS
```

```
The project architecture is designed to provide scalability,
high availability, security, centralized monitoring, and
fault tolerance.
```

```
============================================================
19. CURRENT STATUS BEFORE AMI
============================================================
```

```
EC2:
    READY
```

```
Next.js:
    RUNNING
```

```
FastAPI/Uvicorn:
    RUNNING
```

```
Nginx:
    RUNNING
```

```
Frontend:
    WORKING
```

```
Backend:
    WORKING
```

- `Frontend <-> Backend: WORKING` 

- `Database connectivity: CONFIGURED/TESTED THROUGH RDS POSTGRESQL` 

- `EC2 reboot: TESTED SUCCESSFULLY` 

- `Application baseline: VALIDATED` 

```
Golden AMI:
    NEXT STEP
```

```
============================================================
```

`20. NEXT STEPS` 

```
============================================================
```

```
The next implementation sequence is:
```

`1. Create the Golden AMI from the validated EC2 instance.` 

`2. Create the Launch Template using the new AMI.` 

`3. Configure the Launch Template with:` 

- `AMI` 

- `Instance type` 

- `IAM Role` 

- `Security Group` 

- `Key pair if required` 

- `User Data if required` 

`4. Create the Auto Scaling Group.` 

`5. Configure desired/minimum/maximum capacity.` 

`6. Configure the Target Group and health checks.` 

`7. Create/configure the Application Load Balancer.` 

`8. Register the ASG instances with the ALB Target Group.` 

`9. Test application access through the ALB instead of the direct EC2 public IP.` 

`10. Continue with CloudFront, WAF, Systems Manager, CloudWatch, SNS, and the remaining components of the target architecture.` 

```
============================================================
IMPORTANT ARCHITECTURAL PRINCIPLE
============================================================
```

```
The EC2 AMI is the application image, not the database image.
```

```
EC2 instances are stateless application servers:
```

```
    Next.js + FastAPI + Nginx
```

```
RDS is the stateful database layer:
```

```
    PostgreSQL Primary + Standby
```

```
Therefore, when Auto Scaling launches a new EC2 instance from the
AMI, the new instance does not create a new database.
```

```
Instead, it connects to the existing RDS PostgreSQL service using
the RDS endpoint.
```

```
This separation between stateless compute and managed stateful
database is the foundation of the scalable architecture.
```

```
============================================================
CURRENT GOLDEN IMAGE FLOW
============================================================
```

```
                    USER
                      |
                      v
                EC2 PUBLIC IP
                      |
                      v
                  NGINX :80
                  /        \
                 /          \
                v            v
          NEXT.JS :3000   FASTAPI :8000
                              |
                              | TCP 5432
                              v
                       RDS POSTGRESQL
                         PRIMARY
                            |
                         Multi-AZ
                            |
                            v
                         STANDBY
```

```
This EC2 configuration has been validated and is ready to be used
as the baseline for the Golden AMI.
============================================================
```

```
================================================================================
================================================================================
==========
```

```
============================================================
AWS PROJECT – NETWORKING & SECURITY DOCUMENTATION
============================================================
```

```
PROJECT:
```

```
Scalable Web Application with ALB and Auto Scaling
```

```
ARCHITECTURE TYPE:
EC2-Based Highly Available Web Application
```

```
============================================================
```

# `1. NETWORKING ARCHITECTURE` 

```
============================================================
```

```
The application infrastructure is deployed inside a dedicated
Amazon VPC designed to provide high availability, scalability,
network isolation, and controlled Internet access across two
Availability Zones.
```

```
VPC:
Name: aws-project-vpc
CIDR: 10.0.0.0/16
```

```
The VPC is divided across two Availability Zones. Each
Availability Zone contains three subnets:
```

# `1. Public Subnet` 

- `Used for the NAT Gateway.` 

- `Provides a path to the Internet through the Internet Gateway.` 

# `2. Private Application Subnet` 

- `Used for EC2 instances running the application.` 

- `EC2 instances are intended to remain private and are not directly accessible from the Internet.` 

- `Outbound Internet access is provided through a NAT Gateway.` 

# `3. Private Database Subnet` 

- `Reserved for Amazon RDS.` 

- `Contains the database tier.` 

- `Has no direct route to the Internet.` 

- `Provides network isolation for the database layer.` 

```
Therefore, the complete subnet structure consists of six subnets:
```

```
AZ-1:
    Public-Subnet-AZ1
        CIDR: 10.0.1.0/24
        Purpose: NAT Gateway
    Private-App-Subnet-AZ1
        CIDR: 10.0.11.0/24
        Purpose: EC2 / Auto Scaling Group
```

```
    Private-DB-Subnet-AZ1
        CIDR: 10.0.21.0/24
        Purpose: RDS
```

```
AZ-2:
    Public-Subnet-AZ2
        CIDR: 10.0.2.0/24
        Purpose: NAT Gateway
```

```
    Private-App-Subnet-AZ2
        CIDR: 10.0.12.0/24
```

```
        Purpose: EC2 / Auto Scaling Group
```

```
    Private-DB-Subnet-AZ2
        CIDR: 10.0.22.0/24
        Purpose: RDS
```

```
============================================================
2. INTERNET GATEWAY
============================================================
```

```
An Internet Gateway named:
```

```
    aws-project-igw
```

```
was created and attached to the VPC.
```

```
The Internet Gateway provides Internet connectivity for the
public subnets.
```

```
A subnet is considered public because its associated route
table contains a default route:
```

```
    0.0.0.0/0 → Internet Gateway
```

```
The Internet Gateway is therefore used by the public subnets
that host the NAT Gateways and, later in the architecture,
the Application Load Balancer.
```

```
============================================================
3. NAT GATEWAYS
```

```
============================================================
```

```
Two NAT Gateways were created to provide highly available
outbound Internet connectivity for the private application
subnets.
```

```
NAT Gateway 1:
    Name: nat-gateway-az1
    Subnet: Public-Subnet-AZ1
    Connectivity: Public
    Elastic IP: Dedicated EIP
NAT Gateway 2:
    Name: nat-gateway-az2
    Subnet: Public-Subnet-AZ2
    Connectivity: Public
    Elastic IP: Dedicated EIP
```

```
Each NAT Gateway is located in a different Availability Zone.
```

```
The application subnet in AZ-1 uses the NAT Gateway in AZ-1,
while the application subnet in AZ-2 uses the NAT Gateway in
AZ-2.
```

```
This avoids making the private application tier dependent on
a NAT Gateway located in another Availability Zone.
```

```
Traffic flow:
```

```
    Private EC2 AZ-1
          |
          v
```

```
    NAT Gateway AZ-1
          |
          v
    Internet Gateway
          |
          v
       Internet
```

```
    Private EC2 AZ-2
          |
          v
    NAT Gateway AZ-2
          |
          v
    Internet Gateway
          |
          v
       Internet
```

```
The NAT Gateways are used for OUTBOUND Internet connectivity
from private application instances.
```

```
They do NOT allow unsolicited inbound Internet connections
to the private EC2 instances.
```

```
============================================================
4. ROUTE TABLE ARCHITECTURE
```

```
============================================================
```

```
Five route tables were designed for the VPC.
```

```
1. public-rt
```

```
2. private-app-rt-az1
```

```
3. private-app-rt-az2
```

```
4. private-db-rt-az1
```

```
5. private-db-rt-az2
```

```
------------------------------------------------------------
4.1 PUBLIC ROUTE TABLE
```

```
------------------------------------------------------------
```

```
Name:
```

```
    public-rt
```

```
Routes:
```

```
    Destination       Target
    --------------------------------
    10.0.0.0/16       local
    0.0.0.0/0         Internet Gateway
Subnet associations:
```

```
    Public-Subnet-AZ1
    Public-Subnet-AZ2
```

```
The public route table allows resources inside the public
subnets to communicate with the Internet through the Internet
Gateway.
```

```
------------------------------------------------------------
4.2 PRIVATE APPLICATION ROUTE TABLE – AZ1
```

```
------------------------------------------------------------
```

```
Name:
```

```
    private-app-rt-az1
```

```
Routes:
```

```
    Destination       Target
    --------------------------------
    10.0.0.0/16       local
    0.0.0.0/0         NAT Gateway AZ-1
```

```
Subnet association:
```

```
    Private-App-Subnet-AZ1
```

```
This allows private EC2 instances in AZ-1 to initiate
outbound Internet connections through NAT Gateway AZ-1.
```

```
------------------------------------------------------------
4.3 PRIVATE APPLICATION ROUTE TABLE – AZ2
```

```
------------------------------------------------------------
```

```
Name:
```

```
    private-app-rt-az2
```

```
Routes:
```

```
    Destination       Target
    --------------------------------
    10.0.0.0/16       local
    0.0.0.0/0         NAT Gateway AZ-2
```

```
Subnet association:
```

```
    Private-App-Subnet-AZ2
```

```
This allows private EC2 instances in AZ-2 to initiate
outbound Internet connections through NAT Gateway AZ-2.
```

```
------------------------------------------------------------
4.4 PRIVATE DATABASE ROUTE TABLE – AZ1
```

```
------------------------------------------------------------
```

```
Name:
```

```
    private-db-rt-az1
```

```
Routes:
```

```
    Destination       Target
    --------------------------------
    10.0.0.0/16       local
```

```
Subnet association:
```

```
    Private-DB-Subnet-AZ1
```

```
There is intentionally no default Internet route:
```

```
    NO 0.0.0.0/0 → NAT Gateway
    NO 0.0.0.0/0 → Internet Gateway
```

```
This keeps the database subnet isolated from direct Internet
access.
```

```
------------------------------------------------------------
4.5 PRIVATE DATABASE ROUTE TABLE – AZ2
------------------------------------------------------------
```

```
Name:
```

```
    private-db-rt-az2
```

```
Routes:
    Destination       Target
    --------------------------------
    10.0.0.0/16       local
```

```
Subnet association:
```

```
    Private-DB-Subnet-AZ2
```

```
There is intentionally no default Internet route.
```

```
The database layer therefore remains isolated from the public
Internet.
```

```
============================================================
5. COMPLETE NETWORK TRAFFIC MODEL
```

```
============================================================
```

```
Public traffic:
```

```
    Internet
       |
       v
    Public Subnet
       |
       v
    Internet Gateway
```

```
Private Application outbound traffic:
```

```
    Private EC2
       |
       v
    Private App Route Table
       |
       v
    NAT Gateway
       |
       v
    Internet Gateway
       |
       v
    Internet
```

```
Private internal application traffic:
```

```
    EC2
       |
       | VPC local routing
       v
    Internal AWS Resources
```

```
Database traffic:
```

```
    EC2
       |
       | TCP 5432
       v
    RDS
```

```
The database is not directly reachable from the Internet.
```

```
============================================================
6. SECURITY ARCHITECTURE
============================================================
```

```
The security model follows a layered approach.
```

```
The main layers are:
```

```
    Internet
       |
       v
    ALB
       |
       v
    EC2
       |
       v
    RDS
```

```
Each layer has a dedicated Security Group.
```

```
Security Groups created:
```

```
    1. alb-sg
    2. ec2-sg
    3. rds-sg
```

```
Security Group references are used instead of allowing
traffic from unrestricted IP ranges whenever possible.
```

```
============================================================
7. ALB SECURITY GROUP
============================================================
```

```
Security Group:
```

```
    Name:
        alb-sg
    Description:
        Security Group for Application Load Balancer
```

```
Purpose:
```

```
    Controls inbound traffic to the Application Load Balancer.
```

```
Inbound rules:
    Protocol: TCP
    Port: 80
    Source: 0.0.0.0/0
```

```
HTTP traffic from the Internet is allowed to reach the ALB.
HTTPS can later be added:
```

```
    Protocol: TCP
    Port: 443
    Source: 0.0.0.0/0
```

```
This will be used when HTTPS and the TLS certificate are
configured.
```

```
Outbound:
```

```
    All traffic
    Destination: 0.0.0.0/0
```

```
The ALB is the public entry point of the application.
```

```
============================================================
8. EC2 SECURITY GROUP
============================================================
```

```
Security Group:
```

```
    Name:
        ec2-sg
    Description:
        Security Group for Application EC2 instances
```

```
Purpose:
```

```
    Controls traffic to the private application instances.
```

```
Inbound:
```

```
    Protocol: TCP
    Port: 80
    Source: alb-sg
```

```
Only the Application Load Balancer is allowed to send HTTP
traffic to the EC2 instances.
```

```
The EC2 instances are NOT directly exposed to the Internet.
```

```
The following rule is intentionally NOT configured:
```

```
    TCP 80 from 0.0.0.0/0
```

```
SSH is also not opened to the Internet.
```

```
The following rule is intentionally NOT configured:
```

```
    TCP 22 from 0.0.0.0/0
```

```
The final architecture will use AWS Systems Manager Session
Manager for secure access to private EC2 instances without
requiring a public IP or Bastion Host.
```

```
Outbound:
```

```
    All traffic
    Destination: 0.0.0.0/0
```

```
Private EC2 instances can therefore initiate outbound
connections through the NAT Gateway.
```

```
============================================================
9. RDS SECURITY GROUP
============================================================
```

```
Security Group:
```

```
    Name:
        rds-sg
    Description:
        Security Group for RDS PostgreSQL
Purpose:
```

```
    Controls access to the database tier.
```

```
Inbound:
```

```
    Protocol: TCP
    Port: 5432
    Source: ec2-sg
Only EC2 instances associated with ec2-sg are allowed to
connect to PostgreSQL.
```

```
The following is intentionally NOT allowed:
```

```
    TCP 5432 from 0.0.0.0/0
Therefore:
    Internet → RDS
        BLOCKED
    EC2 → RDS:5432
        ALLOWED
Outbound:
    All traffic
    Destination: 0.0.0.0/0
```

```
============================================================
10. NAT GATEWAY SECURITY
============================================================
```

```
NAT Gateways do not have Security Groups because NAT Gateway
```

```
is an AWS managed networking service rather than an EC2
instance.
```

```
Its traffic behavior is controlled through:
```

- `Route Tables` 

- `Network ACLs` 

- `Security Groups on the resources using it` 

```
============================================================
11. SECURITY TRAFFIC MATRIX
```

```
============================================================
```

|`Traffic Path                         Status`<br>`------------------------------------------------------------`|
|---|
|`Internet → ALB :80                  ALLOWED`|
|`Internet → ALB :443                 ALLOWED LATER`|
|`ALB → EC2 :80                       ALLOWED`|
|`Internet → EC2                      BLOCKED`|
|`Internet → EC2 :22                  BLOCKED`|
|`EC2 → RDS :5432                      ALLOWED`|
|`Internet → RDS :5432                BLOCKED`|
|`EC2 → Internet                       ALLOWED via NAT`|
|`EC2 AZ-1 → NAT AZ-1                  ALLOWED`|
|`EC2 AZ-2 → NAT AZ-2                  ALLOWED`|
|`RDS → Internet                        NOT ROUTED`|
|`ALB → RDS                             BLOCKED / NOT REQUIRED`|
|`============================================================`<br>`12. APPLICATION TRAFFIC FLOW`<br>`============================================================`|



```
The application is currently structured with:
```

```
    Nginx
       |
       +----> Next.js Frontend :3000
       |
       +----> FastAPI Backend :8000
```

```
In the final architecture, the ALB will communicate with
Nginx on port 80.
```

```
The expected application flow is:
```

```
    User
      |
      v
    ALB :80
      |
```

```
      v
    Nginx :80
      |
      +----> Next.js :3000
      |
      +----> FastAPI :8000
                    |
                    v
              PostgreSQL RDS :5432
```

```
============================================================
13. FINAL SECURITY DESIGN
============================================================
```

```
The final layered security model is:
```

```
                    INTERNET
                        |
                        v
                  Application
                  Load Balancer
                     alb-sg
                        |
                        | TCP 80
                        v
                 Private EC2 Instances
                      ec2-sg
                        |
                        | TCP 5432
                        v
                  RDS PostgreSQL
                      rds-sg
```

```
The Internet can reach only the public entry point
(Application Load Balancer).
```

```
The EC2 application instances remain in private subnets and
accept application traffic only from the ALB.
```

```
The RDS database remains in private database subnets and
accepts PostgreSQL connections only from the application
tier.
Outbound Internet access from private EC2 instances is
provided through NAT Gateways.
```

```
This architecture follows the project's security and
high-availability objectives by using public/private subnet
separation, NAT Gateways, Security Groups, private compute,
and an isolated database tier.
```

```
============================================================
END OF NETWORKING & SECURITY DOCUMENTATION
============================================================
```

```
================================================================================
================================================================================
==============================================================
```

```
============================================================
```

```
ALB + TARGET GROUP + LAUNCH TEMPLATE + AUTO SCALING GROUP
============================================================
```

# `Project Architecture:` 

```
The application is deployed on AWS using an EC2-based scalable architecture. The
main objective of this part is to make the web application highly available and
scalable by placing multiple EC2 instances behind an Application Load Balancer
(ALB) and managing these instances automatically through an Auto Scaling Group
(ASG).
```

```
The architecture is designed across multiple Availability Zones. The ALB acts as
the single entry point for users, while the ASG manages the EC2 instances that
run the application. The EC2 instances are created from a standardized Launch
Template, and the ALB forwards incoming traffic to a Target Group containing the
healthy EC2 instances.
```

```
The overall traffic flow is:
```

```
User
  |
  v
Application Load Balancer (ALB)
  |
  v
Target Group
  |
  +------> EC2 Instance 1
  |
  +------> EC2 Instance 2
  |
  +------> EC2 Instance N
```

```
The Auto Scaling Group is responsible for creating, terminating, and maintaining
the required number of EC2 instances behind the Target Group.
```

```
============================================================
```

`1. LAUNCH TEMPLATE` 

```
============================================================
```

```
A Launch Template was created to provide a standardized configuration for every
EC2 instance launched by the Auto Scaling Group.
```

```
Instead of manually launching each EC2 instance and configuring it separately,
the Launch Template stores the required EC2 configuration. Whenever the ASG
needs a new instance, it launches the instance using this template.
```

```
The Launch Template is based on the AMI that was prepared from the configured
application EC2 instance. The AMI contains the application environment that was
already configured, including the frontend, backend, Nginx configuration,
required dependencies, and the required connection configuration to the RDS
database.
```

```
Using the AMI inside the Launch Template ensures that every instance created by
the ASG starts with the same application environment and configuration.
```

```
The Launch Template configuration includes:
```

- `AMI: The custom application AMI created from the configured EC2 instance.` 

- `Instance Type: t3.small.` 

- `Key Pair: The configured EC2 key pair where applicable.` 

- `Security Group: The EC2/application Security Group created for the application instances.` 

- `IAM Instance Profile: The IAM role used by the EC2 instances, including the` 

```
permissions required for AWS Systems Manager (SSM).
```

```
- Network configuration: Instances are launched in the subnets selected by the
Auto Scaling Group.
```

```
- Storage: The AMI-based/root EBS configuration is used for the instances.
- Application configuration: The instance starts with the same application
environment captured in the AMI.
```

```
The Launch Template is therefore the source of truth for the configuration of
all EC2 instances managed by the ASG.
```

```
This provides configuration consistency and makes horizontal scaling possible
because a newly launched instance is automatically created with the same
application setup as the existing instances.
```

```
============================================================
```

# `2. TARGET GROUP` 

```
============================================================
```

```
A Target Group was created for the Application Load Balancer.
```

```
The Target Group represents the collection of backend EC2 instances that are
eligible to receive traffic from the ALB.
```

```
The Target Group is configured with:
```

- `Target type: Instances.` 

```
- Protocol: HTTP.
```

- `Application port: 80.` 

- `Health checks: Enabled.` 

- `Health check protocol: HTTP.` 

- `Health check path: The application's available HTTP endpoint/path.` 

- `Traffic is forwarded only to healthy targets.` 

```
The Target Group is directly associated with the Auto Scaling Group.
```

```
When the ASG launches a new EC2 instance, that instance is automatically
registered with the Target Group.
```

```
When the ASG terminates an EC2 instance, that instance is automatically removed
from the Target Group.
```

```
This means that the Target Group always represents the current set of EC2
instances managed by the ASG.
```

```
The health check mechanism is important because the ALB must not send user
traffic to an unhealthy EC2 instance.
```

```
The ALB periodically sends health-check requests to the configured health-check
path. If an instance responds successfully according to the configured health-
check criteria, the instance is considered healthy and can receive traffic.
```

```
If the health check fails, the instance is marked unhealthy and the ALB stops
forwarding new traffic to it.
```

```
This provides automatic fault isolation at the load-balancing layer.
```

```
============================================================
```

# `3. APPLICATION LOAD BALANCER (ALB)` 

```
============================================================
```

```
An Application Load Balancer was created as the public entry point of the
application.
```

```
The ALB operates at Layer 7 and is responsible for receiving HTTP application
traffic and distributing it across the healthy EC2 instances registered in the
Target Group.
```

```
Instead of exposing the individual EC2 instances directly to users, users
communicate with the ALB.
```

```
The traffic flow becomes:
```

```
Client
  |
  | HTTP
  v
ALB
  |
  | Forward
  v
Target Group
  |
  +------> Healthy EC2 Instance
  |
  +------> Healthy EC2 Instance
```

```
The ALB was configured to use the application Target Group as its forwarding
destination.
```

```
The ALB is deployed across the selected Availability Zones to provide high
availability.
```

```
The ALB Security Group allows incoming application traffic from the required
source and allows outbound traffic toward the EC2/application Security Group.
```

```
The EC2 Security Group is designed so that application instances accept
application traffic from the ALB rather than relying on direct public access to
the application.
```

```
This creates a security boundary between the public-facing load balancer and the
backend compute instances.
```

```
The ALB continuously uses the Target Group health-check status to determine
which EC2 instances are available to receive traffic.
```

```
If multiple EC2 instances are healthy, the ALB distributes incoming requests
between them.
```

```
If one instance becomes unhealthy, the ALB removes it from active traffic
distribution while the remaining healthy instances continue serving users.
```

```
============================================================
4. ALB LISTENER
============================================================
```

```
An HTTP listener was configured on the Application Load Balancer.
```

```
The listener receives incoming requests on the configured HTTP port and forwards
them to the application Target Group.
```

```
The logical rule is:
```

```
HTTP Request
     |
     v
```

```
ALB Listener
     |
     v
```

```
Forward to Target Group
     |
     v
Healthy EC2 Instances
```

```
The listener therefore separates the public entry point from the backend
application instances.
```

```
The architecture was initially implemented using HTTP.
```

```
HTTPS/TLS can later be added by creating an ACM certificate for the
application's domain and adding an HTTPS listener on port 443. The HTTPS
listener would terminate TLS at the ALB and then forward the request to the
backend Target Group.
```

```
In the current implementation, the ALB is primarily responsible for HTTP traffic
distribution.
```

```
============================================================
5. AUTO SCALING GROUP (ASG)
```

```
============================================================
```

```
An Auto Scaling Group was created to automatically manage the EC2 instances
running the application.
```

```
The ASG uses the previously created Launch Template as the instance
configuration source.
```

```
The ASG was configured with:
```

```
- Minimum capacity: 2 instances.
```

- `Desired capacity: 2 instances.` 

```
- Maximum capacity: 6 instances.
```

```
- Launch Template: The custom application Launch Template.
```

```
- Availability Zones: Multiple Availability Zones.
```

- `Target Group: The application Target Group.` 

```
The minimum capacity of 2 ensures that the application normally maintains at
least two EC2 instances.
```

```
The desired capacity of 2 represents the normal number of running instances at
the beginning of the deployment.
```

```
The maximum capacity of 6 defines the upper limit to which the application can
scale automatically.
```

```
Therefore:
```

```
MIN = 2
DESIRED = 2
MAX = 6
```

```
The ASG maintains the desired number of healthy EC2 instances and automatically
replaces instances when required.
```

```
For example, if the desired capacity is 2 and one EC2 instance fails or becomes
unhealthy and is terminated, the ASG can automatically launch a replacement
instance from the Launch Template to return the group toward the desired
capacity.
```

```
This provides self-healing behavior at the compute layer.
```

```
============================================================
6. MULTI-AZ ASG DESIGN
```

```
============================================================
```

```
The Auto Scaling Group is associated with subnets distributed across multiple
Availability Zones.
```

```
The purpose of using multiple Availability Zones is to avoid depending on a
single physical AWS infrastructure location.
```

```
For example:
```

```
Availability Zone A
    |
    +---- EC2 Instance 1
    |
    +---- EC2 Instance 2
```

```
Availability Zone B
    |
    +---- EC2 Instance 3
    |
    +---- EC2 Instance 4
```

```
The actual number of instances depends on the current ASG capacity.
```

```
If one Availability Zone experiences a failure, the ASG can maintain or recreate
instances in the remaining available Availability Zones, while the ALB continues
directing traffic toward healthy targets.
```

```
============================================================
7. AUTO SCALING POLICY
```

```
============================================================
```

```
A Target Tracking scaling policy was configured for the Auto Scaling Group.
```

```
The scaling policy uses CPU utilization as the primary scaling metric.
```

```
The basic concept is:
```

```
Target CPU Utilization
        |
        v
Auto Scaling Group
        |
        +---- Scale Out when demand increases
        |
        +---- Scale In when demand decreases
```

```
When the average CPU utilization of the instances increases above the target
behavior, the ASG can launch additional EC2 instances.
```

```
When the workload decreases and CPU utilization remains below the target, the
ASG can gradually reduce the number of instances, while respecting the minimum
capacity.
```

```
The ASG therefore dynamically adjusts compute capacity according to application
demand.
```

```
The configured capacity boundaries remain:
```

```
Minimum = 2
Desired = 2
Maximum = 6
```

```
This prevents the application from scaling below the required baseline or beyond
the defined maximum capacity.
```

```
============================================================
8. RELATIONSHIP BETWEEN ALB, TARGET GROUP AND ASG
============================================================
```

```
The three components have different responsibilities and work together as one
scalable system.
```

```
The ALB is responsible for receiving and distributing application traffic.
```

```
The Target Group is responsible for representing the EC2 instances that can
receive traffic and for performing health checks.
```

```
The ASG is responsible for creating and managing the EC2 instances.
```

```
The Launch Template defines how each EC2 instance should be created.
```

```
Therefore, the complete relationship is:
```

```
Launch Template
       |
       v
Auto Scaling Group
       |
       +----> EC2 Instance 1
       |
       +----> EC2 Instance 2
       |
       +----> EC2 Instance N
                 |
                 v
            Target Group
                 ^
                 |
                 |
                ALB
                 ^
                 |
               Users
```

```
When the ASG launches an instance:
```

`1. ASG uses the Launch Template.` 

`2. A new EC2 instance is created from the configured AMI.` 

`3. The instance starts the application environment.` 

`4. The instance is automatically registered in the Target Group.` 

`5. The Target Group performs a health check.` 

`6. If the instance becomes healthy, the ALB can forward traffic to it.` 

```
When the ASG scales out:
```

`1. Additional EC2 instances are launched.` 

`2. New instances are automatically registered with the Target Group.` 

`3. Health checks verify the new instances.` 

`4. Healthy instances become available to the ALB.` 

`5. The ALB starts distributing traffic across the larger number of healthy instances.` 

```
When the ASG scales in:
```

`1. The ASG selects an instance for termination according to its termination logic.` 

`2. The instance is removed from service.` 

`3. The instance is deregistered from the Target Group.` 

`4. The ALB stops sending traffic to the terminating instance.` 

`5. The remaining healthy instances continue serving users.` 

```
============================================================
```

# `9. HIGH AVAILABILITY` 

```
============================================================
```

```
The ALB + ASG architecture provides high availability at the application compute
layer.
```

```
The ALB is distributed across multiple Availability Zones, while the ASG
maintains multiple EC2 instances across the configured Availability Zones.
```

```
This eliminates the dependency on a single EC2 instance.
```

```
Instead of:
```

```
User
 |
 v
Single EC2
 |
 v
Application
```

```
The architecture becomes:
```

```
                    +---- EC2 Instance 1
                    |
User --> ALB --> Target Group
                    |
                    +---- EC2 Instance 2
                    |
                    +---- EC2 Instance N
```

```
If one EC2 instance fails, the ALB detects the unhealthy target through health
checks and stops sending new requests to it.
```

```
The ASG can then launch a replacement instance using the Launch Template.
```

```
This creates a combination of:
```

```
Load balancing
+
Health checking
+
Automatic replacement
+
Automatic scaling
+
Multi-AZ deployment
```

```
which significantly improves application availability and resilience.
```

```
============================================================
10. SCALABILITY
```

```
============================================================
```

```
The architecture supports horizontal scaling.
```

```
Horizontal scaling means increasing or decreasing the number of EC2 instances
instead of increasing the resources of a single EC2 instance.
```

```
The ASG provides this capability.
```

```
Under normal load:
```

```
2 EC2 instances
        |
        v
ALB
        |
        v
Users
```

```
Under increased load:
```

```
2 --> 3 --> 4 --> 5 --> 6 instances
```

```
The ALB automatically distributes incoming requests across the healthy
instances.
```

```
When demand decreases, the ASG can scale the number of instances back down while
maintaining the configured minimum of 2 instances.
```

```
This allows compute capacity to follow application demand without manually
launching or terminating EC2 instances.
```

```
============================================================
11. SECURITY RELATIONSHIP
```

```
============================================================
```

```
The ALB and EC2 instances use separate Security Groups.
```

```
The ALB Security Group is responsible for allowing incoming traffic to the load
balancer.
```

```
The EC2 Security Group is responsible for protecting the backend application
instances.
```

```
The intended traffic relationship is:
```

```
Internet
   |
   v
ALB Security Group
   |
   v
ALB
   |
   v
EC2 Security Group
   |
   v
Application
```

```
The EC2 instances should accept application traffic from the ALB rather than
exposing the backend application directly to arbitrary sources.
```

```
This creates a layered security architecture where the ALB is the controlled
public entry point and the EC2 instances operate behind it.
```

```
============================================================
12. FINAL ARCHITECTURE FLOW
```

```
============================================================
```

```
The final ALB + ASG architecture can be summarized as:
```

```
                            |
                            v
                    Application Load
                       Balancer
                          (ALB)
                            |
                            v
                      ALB Listener
                            |
                            v
                       Target Group
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
           EC2 #1        EC2 #2        EC2 #N
              |             |             |
              +-------------+-------------+
                            |
                            v
                     Application
                  Frontend + Backend
                            |
                            v
                          RDS
```

```
                         ^
                         |
                   Auto Scaling
                       Group
                         |
                         v
                  Launch Template
                         |
                         v
                    Custom AMI
```

```
The ALB provides traffic distribution, the Target Group provides target
registration and health checks, the ASG provides automatic instance management
and scaling, and the Launch Template provides a consistent configuration for
every EC2 instance.
```

```
The final capacity configuration is:
```

```
Minimum Capacity  = 2
Desired Capacity   = 2
Maximum Capacity   = 6
```

```
This design provides a scalable and highly available EC2-based application
architecture and forms the compute/load-balancing foundation of the overall AWS
```

```
project.
```

```
============================================================
END OF ALB + TARGET GROUP + ASG DOCUMENTATION
```

```
============================================================
```

```
================================================================================
================================================================================
=======================================================================
```

```
============================================================
AWS ROUTE 53 — DNS & DOMAIN MANAGEMENT
```

```
============================================================
```

```
1. PURPOSE OF ROUTE 53
```

```
=======================
```

```
Amazon Route 53 is AWS's managed DNS (Domain Name System) service. Its main role
in this project would have been to provide a human-readable domain name for the
application instead of accessing the application through the ALB DNS name or a
public IP address.
```

```
The planned architecture uses Route 53 as the DNS layer in front of the
Application Load Balancer (ALB).
```

```
The expected traffic flow would be:
```

```
User
  |
  | HTTPS request
  v
Route 53
  |
  | DNS resolution
  v
Application Load Balancer (ALB)
  |
  v
AWS WAF
  |
  v
Target Group
  |
  v
EC2 Instances managed by Auto Scaling Group
  |
  v
RDS Multi-AZ Database
```

```
Route 53 itself does not forward the HTTP/HTTPS traffic to the application. Its
```

```
primary responsibility is DNS resolution: converting the domain name requested
by the user into the AWS resource endpoint that should receive the traffic.
```

```
2. ROUTE 53 IN THE PLANNED PROJECT ARCHITECTURE
===============================================
```

```
The original architecture included Route 53 with an Alias Record pointing to the
Application Load Balancer.
```

```
The planned configuration was:
```

```
Domain Name
    |
    v
Route 53 Hosted Zone
    |
    v
```

```
A / AAAA Alias Record
```

```
    |
    v
Application Load Balancer
    |
    v
WAF
    |
    v
EC2 Auto Scaling Group
```

```
The Route 53 record would point directly to the ALB using an AWS Alias Record.
For example, after purchasing a domain such as:
```

```
example.com
```

```
we would create a Route 53 Hosted Zone for:
```

```
example.com
```

```
and then create a DNS record similar to:
```

```
Record Type:
A
```

```
Record Name:
example.com
```

```
Alias:
Yes
Alias Target:
Application Load Balancer
```

```
The Alias Record is preferable to using a normal CNAME for the root domain
because Route 53 Alias Records can directly point the domain to AWS resources
such as an Application Load Balancer.
```

# `3. HOSTED ZONE` 

```
===============
```

```
A Hosted Zone is the DNS container that holds the DNS records for a domain.
```

```
For example:
```

```
Domain:
example.com
```

```
Hosted Zone:
example.com
```

```
Inside the Hosted Zone, we could create records such as:
```

```
A Record:
example.com
        -> ALB
```

```
A Record / Alias:
www.example.com
        -> ALB
```

```
The Hosted Zone would therefore become the DNS control plane for the
application's domain.
```

# `4. DOMAIN REGISTRATION` 

```
======================
```

```
To use Route 53 with a real production domain, we first need to own a domain
name.
```

```
The normal implementation would be:
```

`1. Purchase a domain.` 

`2. Create or use the corresponding Route 53 Hosted Zone.` 

`3. Configure the domain's DNS delegation / nameservers.` 

`4. Create an Alias Record pointing the domain to the ALB.` 

`5. Configure HTTPS using AWS Certificate Manager (ACM).` 

`6. Configure the ALB HTTPS listener.` 

`7. Redirect HTTP traffic to HTTPS.` 

```
For example:
```

```
User enters:
```

```
https://example.com
```

```
DNS resolution would occur through Route 53:
```

```
example.com
     |
     v
Route 53
     |
     v
ALB DNS endpoint
     |
     v
ALB HTTPS Listener :443
     |
     v
WAF / Target Group
     |
     v
EC2 instances
```

```
5. ROUTE 53 + ALB
```

# `==================` 

```
The ALB already has an AWS-generated DNS name similar to:
```

```
xxxxxxxx.eu-north-1.elb.amazonaws.com
```

```
However, this is not suitable as the application's public identity.
```

```
Route 53 would allow us to use a custom domain such as:
```

```
example.com
```

```
while the actual traffic would still be handled by the ALB.
```

```
The Route 53 Alias Record would map:
```

```
example.com
        |
        v
Application Load Balancer
```

```
Therefore, users would not need to know the ALB's generated DNS name.
```

# `6. HEALTH CHECKS` 

```
================
```

```
Route 53 also supports DNS health checks.
```

```
In a more advanced architecture, Route 53 Health Checks can monitor the
availability of endpoints and can be used with DNS routing policies.
```

```
For example, Route 53 could monitor an endpoint and determine whether it is
healthy.
```

```
However, in this project the main high-availability mechanism is provided by:
```

```
ALB
+
Target Group Health Checks
```

```
+
Auto Scaling Group
+
Multi-AZ EC2 Deployment
```

```
The ALB continuously checks the health of EC2 instances through the Target Group
Health Check and stops routing traffic to unhealthy instances.
```

```
Therefore, Route 53 Health Checks were part of the planned architecture
capability, but they were not required to provide the primary application
failover mechanism in this implementation.
```

# `7. HTTPS IMPLEMENTATION THAT WOULD HAVE BEEN USED` 

```
==================================================
```

```
The project was designed to use HTTPS for secure communication between the
client and the application.
```

```
However, HTTPS using a trusted public certificate requires a real domain name.
```

```
The normal AWS implementation would therefore be:
```

```
Step 1:
```

```
Purchase a domain.
```

```
Step 2:
```

```
Create/configure the Route 53 Hosted Zone.
```

```
Step 3:
```

```
Create an AWS Certificate Manager (ACM) public certificate for:
```

```
example.com
```

```
and optionally:
```

```
*.example.com
```

```
Step 4:
Validate the ACM certificate using DNS validation.
```

```
If Route 53 is managing the DNS zone, ACM can automatically create the required
DNS validation record.
```

```
Step 5:
```

```
Attach the validated ACM certificate to the ALB HTTPS Listener on:
```

```
TCP 443
```

```
Step 6:
Configure the ALB HTTP Listener on:
```

```
TCP 80
```

```
to redirect HTTP requests to HTTPS.
```

```
The final traffic flow would therefore be:
```

```
HTTP
```

```
http://example.com
       |
       v
Route 53
       |
       v
ALB :80
       |
       v
301/Redirect
       |
       v
```

```
HTTPS
https://example.com
       |
       v
ALB :443
       |
       v
ACM Certificate
       |
       v
WAF
       |
       v
Target Group
       |
       v
EC2 Instances
```

```
8. AWS CERTIFICATE MANAGER (ACM)
================================
```

```
AWS Certificate Manager would be responsible for providing the SSL/TLS
certificate used by the ALB.
```

```
The certificate would establish encrypted communication between the user's
browser and the ALB.
```

```
The ALB would terminate TLS at the HTTPS listener.
```

```
Therefore:
```

```
Client
   |
   | HTTPS / TLS
   v
ALB :443
   |
   | TLS termination
   v
HTTP/HTTPS forwarding to backend
   |
   v
EC2
```

```
The certificate would be attached to the ALB rather than individually installing
certificates on every EC2 instance.
```

```
This is especially important because the project uses an Auto Scaling Group. New
EC2 instances can be created or terminated dynamically, while the HTTPS
certificate remains centralized at the ALB layer.
```

```
9. HTTP TO HTTPS REDIRECTION
============================
```

```
After configuring the HTTPS listener, the ALB would normally have two listeners:
```

```
Listener 1:
HTTP :80
```

```
Action:
Redirect to HTTPS :443
Listener 2:
HTTPS :443
Action:
Forward traffic to the Target Group
```

```
Therefore:
http://example.com
        |
        v
ALB :80
        |
        v
Redirect
        |
        v
```

```
https://example.com
        |
        v
ALB :443
        |
        v
Target Group
        |
        v
EC2
```

```
10. WHY ROUTE 53 WAS NOT IMPLEMENTED IN THIS PROJECT
=====================================================
```

```
Route 53 was included in the original planned AWS architecture, but it was NOT
implemented in the current project deployment.
```

```
The reason is that the current AWS account/project setup does not support the
required domain-based configuration in the way needed for the final production
implementation.
```

```
Because we did not proceed with purchasing a real domain, we also did not
complete the complete production DNS + public HTTPS workflow.
```

```
Therefore, the following Route 53 components were planned but not actually
deployed:
```

```
- Domain purchase
```

```
- Route 53 Hosted Zone
```

```
- Custom domain DNS records
```

```
- Alias Record pointing to the ALB
```

```
- DNS validation for ACM
```

```
- Public ACM certificate for the custom domain
```

```
- ALB HTTPS listener using the custom certificate
```

```
- HTTP-to-HTTPS redirection through the final custom domain
```

```
This means Route 53 is documented as part of the intended production
architecture, but it is explicitly marked as NOT IMPLEMENTED in the current
project.
```

# `11. CURRENT PROJECT STATE` 

```
=========================
```

```
The project was successfully implemented using the AWS infrastructure that could
be deployed under the current account limitations.
```

```
The implemented architecture includes the major infrastructure components such
as:
```

```
VPC
Public/Private Subnets
Route Tables
NAT Gateway
Security Groups
EC2
Launch Template
Auto Scaling Group
Application Load Balancer
Target Group
AWS WAF
CloudFront
RDS
```

```
Systems Manager
CloudWatch
SNS
```

```
Route 53 was intentionally left out of the actual deployment because a real
domain was not purchased.
```

```
The application can therefore be accessed through the available AWS endpoint
instead of a custom domain.
```

```
The absence of Route 53 does not prevent the core ALB + Auto Scaling
architecture from working. Route 53 would mainly provide the DNS/domain layer
required for a clean production-facing domain name.
```

# `12. WHAT WOULD BE DONE AFTER PURCHASING THE DOMAIN` 

```
===================================================
```

```
Once a domain is purchased, the remaining production DNS/HTTPS configuration
would be:
```

`1. Register/purchase the domain.` 

`2. Create the Route 53 Hosted Zone.` 

`3. Configure the domain's DNS delegation to Route 53 if the domain is registered through another registrar.` 

`4. Create an Alias A Record:` 

```
example.com
      |
```

```
      v
Application Load Balancer
```

`5. Create an ACM public certificate for:` 

```
example.com
```

`6. Validate the certificate using DNS validation.` 

`7. Attach the ACM certificate to the ALB HTTPS Listener:` 

```
HTTPS :443
```

`8. Configure the ALB HTTP Listener:` 

```
HTTP :80
```

```
to redirect to:
```

```
HTTPS :443
```

`9. Test:` 

```
http://example.com
```

```
and verify that it redirects to:
```

```
https://example.com
```

`10. Verify that the HTTPS certificate is valid and trusted by the browser.` 

`11. Verify that the complete production traffic path is:` 

```
User
  |
  | HTTPS
  v
Route 53
  |
  | DNS Resolution
  v
ALB :443
  |
  v
AWS WAF
  |
  v
Target Group
  |
  v
EC2 Auto Scaling Group
  |
  v
RDS Multi-AZ
```

```
13. FINAL STATUS
================
```

```
Route 53 Status:
```

```
NOT IMPLEMENTED IN THE CURRENT PROJECT.
```

```
Reason:
```

```
The project was stopped before purchasing and configuring a real domain because
the current AWS account limitations did not allow us to complete the intended
domain-based production setup.
```

```
Planned future implementation:
```

```
Domain Purchase
      |
      v
Route 53 Hosted Zone
      |
      v
Alias A Record
      |
      v
ALB
      |
      v
ACM Certificate
      |
      v
HTTPS :443
      |
      v
WAF
      |
      v
ASG / EC2
      |
      v
RDS
```

```
If the account supported the required domain workflow and the project continued
to the domain-purchase stage, we would purchase the domain, configure Route 53,
issue an ACM certificate, attach it to the ALB, configure HTTPS on port 443, and
redirect all HTTP traffic from port 80 to HTTPS.
```

```
Therefore, Route 53 remains a planned component of the production architecture
and is fully compatible with the implemented ALB, WAF, Auto Scaling, CloudFront,
and RDS architecture, but it was intentionally NOT applied in the current
version of the project because the project was stopped before purchasing the
domain.
```

```
============================================================
```

```
END OF ROUTE 53 DOCUMENTATION
```

```
============================================================
```

```
================================================================================
================================================================================
====
```

```
====================================================================
SYSTEMS MANAGER (SSM) + IAM ROLE + ASG + CLOUDFRONT CACHE
```

```
====================================================================
```

```
====================================================================
```

# `1. IAM ROLE FOR EC2 / AUTO SCALING GROUP` 

```
====================================================================
```

```
An IAM Role was created for the EC2 instances to allow them to
communicate securely with AWS Systems Manager (SSM).
```

```
Role:
```

```
    LuminaEC2SSMRole
```

```
Trusted Entity:
    AWS Service → EC2
```

```
Main IAM Policy Attached:
    AmazonSSMManagedInstanceCore
```

```
Purpose:
    The role allows EC2 instances to register with AWS Systems
    Manager and use Session Manager without requiring SSH-based
    administrative access.
```

```
The role is attached to the EC2 instances through the EC2
Instance Profile.
```

```
Because the application instances are managed by an Auto Scaling
Group, the IAM role is configured in the Launch Template so that
every new EC2 instance launched automatically by the ASG receives
the same IAM permissions.
```

```
Architecture:
```

```
    Auto Scaling Group
            |
```

```
            v
      Launch Template
            |
            v
       EC2 Instance
            |
            v
    IAM Instance Profile
            |
            v
    LuminaEC2SSMRole
            |
            v
 AmazonSSMManagedInstanceCore
```

```
This means that when the ASG launches a replacement or additional
EC2 instance, the new instance automatically receives the SSM IAM
role and can register with Systems Manager without manual IAM
configuration.
```

```
====================================================================
2. SYSTEMS MANAGER (SSM)
====================================================================
```

```
AWS Systems Manager was configured to provide secure management
access to the EC2 instances through Session Manager.
```

```
The main component used is:
```

```
    Systems Manager Session Manager
```

```
Purpose:
    Provide shell access to EC2 instances directly from the AWS
    Console without depending on SSH, public IP addresses, or a
    Bastion Host.
The EC2 instance uses the SSM Agent to communicate with AWS
Systems Manager.
SSM communication architecture:
```

```
    AWS Management Console
            |
            v
    AWS Systems Manager
            |
            v
      Session Manager
            |
            v
        SSM Agent
            |
            v
       EC2 Instance
```

```
The SSM Agent was verified on the EC2 instance using:
```

```
    sudo systemctl status amazon-ssm-agent
```

```
The agent was expected to be:
```

```
    Active: active (running)
```

```
The agent can also be enabled at boot using:
```

```
    sudo systemctl enable amazon-ssm-agent
```

```
The EC2 instance was then checked from:
```

```
    AWS Console
```

```
        →
    Systems Manager
        →
    Managed Nodes
```

```
The EC2 instance should appear with:
```

```
    Ping Status: Online
```

```
After the instance became available in Systems Manager, Session
Manager was used to start an interactive shell session directly
from the AWS Console.
```

```
Session Manager testing commands included:
```

```
    hostname
    whoami
    pwd
    uname -a
```

```
The application environment was also verified from the Session
Manager shell using commands such as:
```

```
    sudo systemctl status nginx
    sudo ss -tulpn
```

```
This confirms that the administrator can access and inspect the
application EC2 instance without using SSH.
```

```
====================================================================
3. SSM NETWORK REQUIREMENTS
====================================================================
```

```
SSM requires outbound connectivity from the EC2 instance to the
AWS Systems Manager services.
```

```
The EC2 instance does NOT require an inbound SSH connection for
Session Manager.
```

```
The required communication is outbound HTTPS traffic over:
```

```
    TCP 443
```

```
For EC2 instances located in a Private Subnet, outbound access to
AWS Systems Manager can be provided through the existing NAT
Gateway.
```

```
Architecture:
```

```
    Private EC2
         |
         v
    Private Route Table
         |
    0.0.0.0/0
         |
         v
    NAT Gateway
         |
         v
    AWS Services / Systems Manager
```

```
The EC2 Security Group therefore does not require a dedicated
inbound TCP/22 rule for SSM.
```

```
The important requirement is that outbound HTTPS traffic is
allowed.
```

```
====================================================================
4. SESSION MANAGER SECURITY MODEL
====================================================================
```

```
Session Manager separates application traffic from administrative
management traffic.
```

```
Application traffic:
```

```
    User
      |
      v
    CloudFront
      |
      v
    WAF
      |
      v
    ALB
      |
      v
    EC2
      |
      v
    RDS
```

```
Management traffic:
    Administrator
          |
          v
    AWS Management Console
          |
          v
    Systems Manager
          |
          v
    Session Manager
          |
          v
```

```
        EC2
```

```
SSM is therefore not part of the public application request path.
```

```
It is used only for secure administrative access and management
of the EC2 instances.
```

```
====================================================================
5. AUTO SCALING GROUP + SSM INTEGRATION
====================================================================
```

```
The EC2 instances are managed by an Auto Scaling Group.
```

```
The Launch Template contains the configuration required for new
instances, including the IAM Instance Profile associated with:
```

```
    LuminaEC2SSMRole
```

```
Therefore, the ASG automatically applies the SSM configuration to
every EC2 instance it launches.
```

```
Example lifecycle:
```

```
    ASG detects required capacity
            |
            v
    Launch Template
            |
            v
    New EC2 Instance
            |
            v
    IAM Instance Profile
            |
            v
    LuminaEC2SSMRole
            |
            v
    SSM Agent
            |
            v
    Systems Manager
            |
            v
    Managed Node: Online
```

```
This provides consistent management access across all instances
in the Auto Scaling Group.
```

```
If an EC2 instance fails and the ASG launches a replacement
instance, the replacement receives the same Launch Template
configuration and therefore automatically becomes manageable
through SSM.
```

```
====================================================================
6. CLOUDFRONT
```

```
====================================================================
```

```
Amazon CloudFront was configured as the content delivery layer in
front of the Application Load Balancer.
```

```
The purpose of CloudFront is to provide a global edge delivery
layer and cache appropriate static content closer to users.
```

```
Architecture:
```

```
    User
      |
      v
    CloudFront
      |
      v
    WAF
      |
      v
    Application Load Balancer
      |
      v
    Target Group
      |
      v
    EC2 Instances
      |
      v
    RDS
```

```
The Application Load Balancer is configured as the CloudFront
Origin.
```

```
CloudFront does NOT connect directly to the EC2 instances.
```

```
Instead:
```

```
    CloudFront
        |
        v
       ALB
        |
        v
    Target Group
        |
        v
       EC2
```

```
====================================================================
7. CLOUDFRONT CACHE
```

```
====================================================================
```

```
CloudFront caching is used primarily for static content.
```

```
The basic concept is:
```

```
    User requests static resource
              |
              v
        CloudFront Edge
              |
        ┌─────┴─────┐
        |           |
      HIT          MISS
        |           |
        v           v
```

```
   Return from     Origin
      Cache          |
                     v
                    ALB
                     |
                     v
                    EC2
                     |
                     v
               Application
```

```
CACHE HIT:
    If the requested object already exists in the CloudFront edge
    cache and is still valid, CloudFront returns the object
    directly without sending the request to the ALB.
```

```
CACHE MISS:
```

```
    If the object is not cached or the cached object has expired,
    CloudFront forwards the request to the configured origin,
    which is the ALB.
```

```
After receiving the object from the origin, CloudFront can cache
the response according to the configured cache policy and TTL.
```

```
====================================================================
8. CLOUDFRONT CACHE POLICY
====================================================================
```

```
CloudFront cache behavior must be designed according to the type
of application content.
```

```
Static assets are suitable for caching, such as:
```

```
    JavaScript files
    CSS files
    Images
    Fonts
    Other static resources
```

```
Dynamic application/API requests should generally not be cached
like static assets because their responses may depend on the
current user, session, database state, or request parameters.
```

```
Therefore, the architecture separates the concept of:
```

```
    Static Content
        →
    CloudFront Cache
```

```
from:
```

```
    Dynamic/API Requests
```

```
        →
    Forward to ALB
        →
    EC2
        →
    Application / RDS
```

```
This prevents stale dynamic application data from being served
from an inappropriate cache.
```

```
====================================================================
```

# `9. CLOUDFRONT BENEFITS IN THE PROJECT` 

```
====================================================================
```

```
CloudFront provides the following architectural benefits:
```

`1. Content Delivery:` 

- `Static resources can be served from CloudFront edge locations closer to users.` 

`2. Reduced Origin Load:` 

- `Cached static content does not need to reach the ALB and EC2 instances for every request.` 

`3. Reduced Latency:` 

- `Frequently requested static resources can be delivered from an edge location instead of the application region.` 

`4. Scalability:` 

```
       CloudFront reduces the amount of repeated static-content
       traffic reaching the EC2/ALB layer.
```

`5. Integration with the Existing Architecture: CloudFront sits in front of the existing WAF and ALB architecture without changing the application-to-RDS connection.` 

```
====================================================================
10. FINAL ARCHITECTURE AFTER THESE CONFIGURATIONS
```

```
====================================================================
```

```
                         USERS
                           |
                           v
                    +--------------+
                    |  CloudFront  |
                    | Cache / Edge |
                    +------+-------+
                           |
                           v
                    +--------------+
                    |     WAF      |
                    +------+-------+
                           |
                           v
                    +--------------+
                    |     ALB      |
                    +------+-------+
                           |
                  +--------+--------+
                  |                 |
                  v                 v
             +---------+       +---------+
             |  EC2-1  |       |  EC2-2  |
             |   ASG   |       |   ASG   |
             +----+----+       +----+----+
                  |                 |
                  +--------+--------+
                           |
```

```
                           v
                    +--------------+
                    |     RDS      |
                    |  PostgreSQL  |
                    +--------------+
```

# `Administrative Management:` 

```
                    ADMINISTRATOR
                           |
                           v
                    AWS CONSOLE
                           |
                           v
                  SYSTEMS MANAGER
                           |
                           v
                  SESSION MANAGER
                           |
                           v
                  +----------------+
                  | EC2 Instances  |
                  |      ASG       |
                  +----------------+
```

```
IAM Relationship:
```

```
                    Launch Template
                           |
                           v
                    EC2 Instance
                           |
                           v
                  Instance Profile
                           |
                           v
                  LuminaEC2SSMRole
                           |
                           v
              AmazonSSMManagedInstanceCore
```

```
====================================================================
11. OVERALL RESULT
```

```
====================================================================
```

```
The infrastructure now combines:
```

```
    Auto Scaling Group
```

```
        →
    Automatically manages EC2 capacity.
    Launch Template
        →
    Provides a consistent configuration for every new EC2
    instance.
```

```
    IAM Role + AmazonSSMManagedInstanceCore
```

```
        →
    Gives EC2 instances the required permissions for Systems
    Manager.
```

```
    Systems Manager / Session Manager
```

```
        →
    Provides secure administrative access without depending on
    SSH or a Bastion Host.
```

```
    CloudFront
```

```
        →
```

```
    Provides the edge delivery and caching layer.
```

```
    CloudFront Cache
```

```
        →
    Reduces repeated requests reaching the ALB and EC2 layer for
    cacheable static content.
```

```
    ALB
```

```
        →
    Distributes application traffic across healthy EC2 instances.
```

```
    ASG
```

```
        →
    Maintains the required number of application instances and
    replaces failed instances.
```

```
    RDS
```

```
        →
```

```
    Provides the persistent PostgreSQL database backend.
```

```
The resulting architecture provides scalability, centralized
instance management, secure administrative access, and improved
content delivery while preserving the existing ALB → EC2 → RDS
application flow.
```

```
====================================================================
```

```
================================================================================
================================================================================
======
```

```
# ==============================
```

```
# CLOUDWATCH + SNS MONITORING
```

```
# ==============================
```

```
## 1. SNS — Simple Notification Service
```

```
# ==============================
```

```
Amazon SNS was configured as the notification and alerting service for the AWS
infrastructure.
```

```
An SNS Topic was created to receive notifications generated by CloudWatch
Alarms.
```

```
SNS Configuration:
```

```
Service:
```

```
Amazon SNS
```

```
Notification Protocol:
Email
```

```
Purpose:
```

```
CloudWatch Alarms publish alarm-state notifications to the SNS Topic, and SNS
forwards these notifications to the configured email endpoint.
```

```
Monitoring Flow:
```

```
CloudWatch Metrics
|
v
CloudWatch Alarms
|
v
SNS Topic
|
v
Email Notification
```

```
This provides centralized notification whenever an important infrastructure,
load balancer, target group, or database condition reaches the configured alarm
threshold.
```

```
# ==============================
```

- `# 2. CloudWatch` 

```
# ==============================
```

```
Amazon CloudWatch was configured to monitor the main components of the
application architecture:
```

- `Auto Scaling Group (ASG)` 

- `Application Load Balancer (ALB)` 

- `ALB Target Group` 

- `Amazon RDS` 

```
CloudWatch collects metrics from these AWS services and evaluates them against
predefined thresholds using CloudWatch Alarms.
```

```
The configured alarms are connected to the SNS notification system so that
important events can generate email notifications.
```

```
# ==============================
```

```
# 3. ASG Monitoring
```

```
# ==============================
```

```
The Auto Scaling Group was monitored using the GroupInServiceInstances metric.
```

```
Metric:
GroupInServiceInstances
```

```
Statistic:
Minimum
```

```
Period:
5 minutes
```

```
Condition:
```

```
Less than 2
```

```
Alarm Purpose:
```

```
This alarm monitors the number of EC2 instances currently running in the
InService state inside the Auto Scaling Group.
```

```
Because the alarm is based on the Auto Scaling Group metric rather than an
individual EC2 instance, it remains applicable even when the ASG terminates an
instance and launches a replacement instance.
```

```
Expected Architecture:
```

```
dental-asg
|
+---- EC2 Instance 1 -> InService
|
+---- EC2 Instance 2 -> InService
|
+---- GroupInServiceInstances = 2
```

```
If the number of InService instances drops below 2 for the configured evaluation
period, the CloudWatch Alarm can transition to ALARM and send a notification
through SNS.
```

```
# ==============================
```

```
# 4. ALB Monitoring
```

```
# ==============================
```

```
The Application Load Balancer was monitored using the HTTPCode_ELB_4XX_Count
metric.
```

```
Metric:
HTTPCode_ELB_4XX_Count
```

```
Statistic:
Sum
```

```
Period:
5 minutes
```

```
Condition:
Greater than 5
```

```
Alarm Purpose:
This alarm monitors the number of HTTP 4XX responses generated by the
Application Load Balancer.
```

```
The Sum statistic counts the total number of 4XX responses during the five-
minute monitoring period.
```

```
If the number of ALB-generated 4XX responses exceeds the configured threshold,
the CloudWatch Alarm can trigger an SNS notification.
```

```
# ==============================
```

```
# 5. Target Group Monitoring
```

```
# ==============================
```

```
The ALB Target Group was monitored using two important metrics:
```

```
## 5.1 Healthy Host Monitoring
```

```
Metric:
HealthyHostCount
```

```
Statistic:
Minimum
```

```
Period:
5 minutes
```

```
Condition:
Less than 2
```

```
Alarm Purpose:
This alarm monitors the number of healthy targets available in the ALB Target
Group.
```

```
The Target Group represents the EC2 instances that receive traffic from the ALB.
```

```
The alarm is configured to detect a situation where the number of healthy
targets falls below 2.
```

```
Example:
```

```
Target Group
|
+---- EC2 Instance 1 -> Healthy
|
+---- EC2 Instance 2 -> Healthy
HealthyHostCount = 2
```

```
If one or more targets become unhealthy:
```

```
Target Group
|
+---- EC2 Instance 1 -> Healthy
|
+---- EC2 Instance 2 -> Unhealthy
HealthyHostCount = 1
```

```
The CloudWatch Alarm can then transition to ALARM and send an SNS notification.
```

```
## 5.2 Target 4XX Monitoring
```

```
Metric:
HTTPCode_Target_4XX_Count
```

```
Statistic:
Sum
```

```
Period:
5 minutes
```

```
Condition:
Greater than 5
Alarm Purpose:
This alarm monitors HTTP 4XX responses generated by the targets behind the ALB.
```

```
The metric helps monitor client-side HTTP errors returned by the backend
targets.
```

```
The Sum statistic counts the total number of target-generated 4XX responses
during the five-minute period.
```

```
# ==============================
```

```
# 6. RDS Monitoring
```

```
# ==============================
```

```
Amazon RDS was monitored using three main CloudWatch metrics:
```

# `* CPUUtilization` 

```
* DatabaseConnections
```

```
* FreeStorageSpace
```

```
## 6.1 RDS CPU Monitoring
```

```
Metric:
CPUUtilization
```

```
Statistic:
Average
```

```
Period:
5 minutes
```

```
Condition:
Greater than 80%
```

```
Alarm Purpose:
```

```
This alarm monitors the average CPU utilization of the RDS database instance.
```

```
If the average CPU utilization exceeds 80% during the configured monitoring
period, the CloudWatch Alarm can trigger an SNS notification.
```

```
This helps identify situations where the database is experiencing high
computational load.
```

```
## 6.2 RDS Database Connections Monitoring
```

```
Metric:
DatabaseConnections
```

```
Statistic:
Average
```

```
Period:
5 minutes
```

```
Condition:
Greater than 80
```

```
Alarm Purpose:
```

```
This alarm monitors the average number of active database connections.
```

```
If the average number of database connections exceeds 80 during the configured
monitoring period, the CloudWatch Alarm can trigger an SNS notification.
```

```
This helps identify unusually high database connection usage.
```

```
## 6.3 RDS Free Storage Monitoring
```

```
Metric:
FreeStorageSpace
```

```
Statistic:
Minimum
```

```
Period:
5 minutes
```

```
Condition:
Less than 2147483648 Bytes
```

```
Equivalent:
2 GB
```

```
Alarm Purpose:
```

```
This alarm monitors the amount of free storage available on the RDS instance.
```

```
The alarm uses the Minimum statistic because the objective is to detect when
available storage reaches a critically low value.
```

```
Threshold:
```

```
# 2147483648 Bytes
```

```
2 GB
```

```
If the available free storage falls below 2 GB, the CloudWatch Alarm can trigger
an SNS notification.
```

```
This helps detect potential storage exhaustion before it affects the database
operation.
```

```
# ==============================
```

# `# 7. COMPLETE MONITORING ARCHITECTURE` 

```
# ==============================
```

```
```
```

```
                CloudWatch
                    |
    +---------------+----------------+
    |               |                |
   ASG              ALB              RDS
    |               |                |
    |               |                +-- CPUUtilization
    |               +-- ELB 4XX      +-- DatabaseConnections
    |               |                +-- FreeStorageSpace
    |               |
    |               +-- Target Group
    |                       |
    +-- InService           +-- HealthyHostCount
        Instances           +-- Target 4XX
                                |
                                v
                          CloudWatch Alarm
                                |
                                v
                               SNS
                                |
                                v
                          Email Notification
```

```
```
```

```
# ==============================
```

```
# 8. MONITORING SUMMARY
```

```
# ==============================
```

```
The final CloudWatch monitoring configuration provides visibility across the
main infrastructure layers of the application.
```

```
ASG:
GroupInServiceInstances
Condition: < 2
```

```
ALB:
HTTPCode_ELB_4XX_Count
Condition: > 5 in 5 minutes
```

```
Target Group:
HealthyHostCount
Condition: < 2
```

```
Target Group:
HTTPCode_Target_4XX_Count
Condition: > 5 in 5 minutes
```

```
RDS:
CPUUtilization
Condition: > 80%
```

```
RDS:
DatabaseConnections
Condition: > 80
```

```
RDS:
FreeStorageSpace
Condition: < 2 GB
```

```
All configured CloudWatch Alarms use the SNS notification mechanism to provide
email-based alerting when the corresponding monitoring conditions are met.
```

```
The resulting monitoring architecture provides centralized observability and
alerting for the Auto Scaling layer, Load Balancer layer, application targets,
and database layer.
```

```
================================================================================
================================================================================
=
```

```
============================================================
AWS WAF – Lumina Dental Application
============================================================
```

# `1. Overview` 

```
------------------------------------------------------------
```

```
AWS WAF (Web Application Firewall) was implemented as a
Layer 7 security layer in front of the Lumina Dental
application.
```

```
Its primary purpose is to inspect incoming HTTP/HTTPS
requests and protect the application against common web
attacks, malicious traffic, excessive request rates,
untrusted IP addresses, geographic restrictions, SQL
injection attempts, and unauthorized access to common
administrative paths.
```

```
The WAF is positioned before the Application Load Balancer
(ALB), allowing malicious or unwanted requests to be
filtered before reaching the application infrastructure.
```

```
Traffic flow:
```

```
Internet
   |
   v
AWS WAF
   |
   v
Application Load Balancer (ALB)
   |
   v
Auto Scaling Group
   |
   +---- EC2 Instance 1
   |
   +---- EC2 Instance 2
   |
   v
Lumina Dental Application
   |
   v
RDS PostgreSQL
```

```
============================================================
2. WAF Essential Protection
============================================================
```

```
The WAF configuration includes the essential security
protections recommended for the selected application
category and application focus.
```

```
Enabled protections:
```

```
- Layer 7 Anti-DDoS
- IP Allowlist
- IP Blocklist
- Geographic Restriction
- Global Rate Limit
- Body Size Restriction
- AWS Core Rule Set
- SQL Injection Protection
- Admin Protection
```

```
These protections provide multiple security layers instead
of relying on a single WAF rule.
```

```
The estimated WAF cost shown by AWS is approximately:
```

```
$42–$43 per 10 million requests/month
```

```
Actual AWS billing may vary depending on request volume,
WAF configuration, managed rule usage, and other AWS pricing
factors.
```

```
============================================================
3. Configured WAF Rules
```

```
============================================================
```

```
The following rules are currently configured in the Web ACL.
```

```
Rules are evaluated according to their configured priority.
```

```
------------------------------------------------------------
```

```
3.1 AWS Managed Anti-DDoS Rule Set
```

```
------------------------------------------------------------
```

```
Rule:
```

```
AWS-AWSManagedRulesAntiDDoSRuleSet
```

```
Capacity:
```

```
50 WCU
```

```
Mode:
```

```
COUNT
```

```
Purpose:
```

```
Provides Layer 7 anti-DDoS protection and visibility into
potentially abusive traffic patterns.
```

```
The rule is currently running in COUNT mode, meaning matching
requests are monitored and counted rather than being directly
blocked by this rule.
```

```
------------------------------------------------------------
3.2 IPv4 Allowlist
```

```
------------------------------------------------------------
```

```
Rule:
```

```
dental-waf_IPV4_Allow
```

```
Capacity:
```

```
1 WCU
```

```
Purpose:
```

```
Provides the ability to explicitly allow trusted IPv4
addresses when required.
```

```
------------------------------------------------------------
```

# `3.3 IPv6 Allowlist` 

```
------------------------------------------------------------
```

```
Rule:
```

```
dental-waf_IPV6_Allow
```

```
Capacity:
```

```
1 WCU
```

```
Purpose:
```

```
Provides the ability to explicitly allow trusted IPv6
addresses when required.
```

```
------------------------------------------------------------
3.4 IPv4 Blocklist
```

```
------------------------------------------------------------
```

```
Rule:
```

```
dental-waf_IPV4_Block
```

```
Capacity:
```

```
1 WCU
```

```
Purpose:
```

```
Provides the ability to explicitly block known or unwanted
IPv4 addresses.
```

```
------------------------------------------------------------
3.5 IPv6 Blocklist
```

```
------------------------------------------------------------
```

```
Rule:
```

```
dental-waf_IPV6_Block
```

```
Capacity:
```

```
1 WCU
```

```
Purpose:
```

```
Provides the ability to explicitly block known or unwanted
IPv6 addresses.
```

```
------------------------------------------------------------
3.6 Geographic Restriction
```

```
------------------------------------------------------------
```

```
Rule:
```

```
GeoRule
```

```
Capacity:
```

```
1 WCU
```

```
Purpose:
```

```
Restricts traffic based on the geographic origin of the
request.
```

```
This provides an additional security layer by allowing or
blocking traffic according to configured countries or
geographic regions.
```

```
------------------------------------------------------------
```

```
3.7 Global Rate-Based Rule
```

```
------------------------------------------------------------
```

# `Rule:` 

```
GlobalRateBasedRule
```

```
Capacity:
```

```
2 WCU
```

```
Mode:
```

```
COUNT
```

```
Purpose:
```

```
Monitors the global request rate and identifies potentially
excessive request activity.
```

```
The rule currently operates in COUNT mode, allowing traffic
patterns to be observed before enforcing an aggressive block
policy.
```

```
This can be used to identify:
```

```
- Automated scanners
```

- `Request flooding` 

- `Abnormally high request rates` 

- `Potential application-layer abuse` 

```
------------------------------------------------------------
3.8 Body Size Restriction
```

```
------------------------------------------------------------
```

```
Rule:
```

```
BodySizeRestrictionRule
```

```
Capacity:
```

```
1 WCU
```

```
Mode:
```

```
COUNT
```

```
Purpose:
```

```
Monitors request body size and identifies requests with
potentially excessive payload sizes.
```

```
The rule currently operates in COUNT mode so that its
behavior can be observed without immediately blocking
traffic.
```

```
------------------------------------------------------------
3.9 AWS Managed Common Rule Set
```

```
------------------------------------------------------------
```

```
Rule:
```

```
AWS-AWSManagedRulesCommonRuleSet
```

```
Capacity:
```

```
700 WCU
```

```
Purpose:
```

```
Provides protection against common web application attacks
and malicious request patterns.
```

```
This is one of the primary AWS Managed Rule Groups used to
protect the application against common Layer 7 attack
techniques.
```

```
------------------------------------------------------------
3.10 AWS Managed SQL Injection Protection
```

```
------------------------------------------------------------
```

```
Rule:
```

# `AWS-AWSManagedRulesSQLiRuleSet` 

```
Capacity:
```

```
200 WCU
```

```
Purpose:
```

```
Provides protection against SQL injection attempts.
```

```
This is particularly important for the Lumina Dental
application because the application communicates with a
PostgreSQL database.
```

```
The rule helps identify malicious SQL injection patterns
before requests reach the backend application.
```

```
------------------------------------------------------------
3.11 AWS Managed Admin Protection
```

```
------------------------------------------------------------
```

```
Rule:
```

```
AWS-AWSManagedRulesAdminProtectionRuleSet
```

```
Capacity:
```

```
100 WCU
```

```
Purpose:
```

```
Protects common administrative interfaces and paths that
are frequently targeted by automated scanners and attackers.
```

```
This rule was specifically observed during testing of the
Lumina Dental Admin Panel.
```

```
============================================================
4. Admin Panel Protection Test
```

```
============================================================
```

```
During testing, accessing:
```

```
/admin
```

```
returned:
```

```
HTTP 403 Forbidden
```

```
The request was inspected using AWS WAF sampled requests.
```

```
The request was identified as:
```

```
Rule Group:
AWS-AWSManagedRulesAdminProtectionRuleSet
```

```
Matched Rule:
```

```
AdminProtection_URIPATH
```

```
Action:
```

```
BLOCK
```

```
URI:
```

```
/admin
```

```
This confirmed that the 403 response was generated by AWS
WAF and not by the Application Load Balancer, EC2 instance,
Nginx, or FastAPI application.
```

```
Request flow:
```

```
Client
   |
   | GET /admin
   v
AWS WAF
   |
   | AdminProtection_URIPATH
   |
   v
BLOCK
   |
   v
HTTP 403 Forbidden
```

```
============================================================
5. Internet Scanner Detection
```

```
============================================================
```

```
During WAF testing, an automated Internet scanner was detected
accessing the public application endpoint.
```

```
Example:
```

```
Source IP:
198.235.24.71
```

```
Country:
United States
```

```
URI:
```

```
/
```

```
User-Agent:
```

```
Hello from Palo Alto Networks...
Cortex-Xpanse...
```

```
Action:
```

```
ALLOW
```

```
The request was an automated scanning request targeting the
public-facing ALB.
```

```
This behavior is expected for Internet-facing infrastructure.
Public IP addresses and public endpoints can be discovered
by automated Internet scanners without the infrastructure
owner explicitly sharing the endpoint.
```

```
The request was allowed because the URI was:
```

```
/
```

```
and it did not match a WAF rule configured to block it.
```

```
This demonstrates that the public-facing ALB is receiving
real Internet traffic and that AWS WAF is actively inspecting
that traffic.
```

```
============================================================
6. Admin Access Control Design
```

```
============================================================
```

```
The objective is not to expose the /admin endpoint to every
Internet user.
```

```
At the same time, legitimate administrators must be able to
access the Admin Panel.
```

```
The security model therefore separates:
```

`1. WAF protection` 

`2. Network-level access control` 

`3. Application authentication` 

`4. Application authorization` 

```
The WAF should not be used as the only authentication
mechanism for the Admin Panel.
```

```
The application must continue to verify that the authenticated
user has the required administrative role.
```

```
============================================================
7. Admin IP Allowlist – Planned Configuration
============================================================
```

```
An IP Set will be created for trusted administrative devices.
```

```
IP Set name:
```

```
lumina-admin-allowed-ips
```

```
The IP Set will contain the public IPv4 addresses of
authorized administrative devices.
```

```
Example:
```

```
Admin PC:
X.X.X.X/32
```

```
Admin Laptop:
Y.Y.Y.Y/32
```

```
The /32 prefix represents a single IPv4 address.
```

```
This provides an additional restriction so that administrative
traffic can be limited to known networks or devices.
```

```
IMPORTANT:
```

```
Public IP addresses assigned by ISPs may be dynamic.
```

```
Therefore, an administrator's public IP may change over time.
```

```
For this reason, IP allowlisting should be treated as an
additional security layer and not as the primary Admin
authentication mechanism.
```

```
The primary protection should remain:
```

```
Authentication
```

```
+
Authorization
+
MFA when applicable
```

```
============================================================
8. AdminProtection Exception
```

```
============================================================
```

```
The AWS Managed Admin Protection Rule currently blocks the
legitimate Lumina Dental Admin Panel because /admin is a
common administrative URI.
```

```
Therefore, the planned configuration is to create a controlled
exception for legitimate administrative access rather than
disabling the entire Admin Protection Rule Group.
```

```
The goal is:
```

```
Authorized Admin Request
        |
        v
      AWS WAF
        |
        v
AdminProtection Exception
        |
        v
Continue WAF Inspection
        |
        v
       ALB
        |
        v
       EC2
        |
        v
Admin Application
```

```
Unauthorized /admin Request
```

```
        |
        v
      AWS WAF
        |
        v
     BLOCK
        |
        v
      HTTP 403
```

- `============================================================ 9. WAF Rule Priority` 

```
============================================================
```

```
Rules are evaluated according to their configured priority.
```

```
The Admin access exception must be carefully positioned so
that legitimate administrative requests are handled correctly
without unintentionally bypassing the rest of the WAF security
controls.
```

```
The intended logical order is:
```

`1. Admin Access / AdminProtection Exception` 

`2. AWS Managed Common Rule Set` 

`3. AWS Managed SQLi Rule Set` 

`4. AWS Managed Admin Protection Rule Set` 

`5. Other security and monitoring rules` 

```
The exact AWS WAF rule configuration must ensure that allowing
authorized Admin traffic does not unintentionally bypass the
remaining security protections.
```

```
A broad ALLOW rule for:
```

```
URI = /admin
```

```
must NOT be used by itself because it could allow any Internet
client to access the Admin endpoint.
```

```
Likewise, an unrestricted ALLOW action may be terminating and
can prevent subsequent WAF rules from evaluating that request.
```

```
The preferred approach is a narrowly scoped exception that
only affects the AdminProtection behavior while preserving
the remaining WAF protections.
```

```
============================================================
10. Defense-in-Depth Security Model
============================================================
```

```
The final security architecture follows a Defense-in-Depth
approach.
```

```
Layer 1 – CloudFront
Provides edge delivery and an additional controlled entry
point for the application.
```

```
Layer 2 – AWS WAF
Inspects Layer 7 traffic and protects against common web
attacks, SQL injection, abusive traffic, suspicious requests,
and administrative path scanning.
```

```
Layer 3 – Application Load Balancer
Provides the centralized public entry point and distributes
traffic across the EC2 instances.
```

```
Layer 4 – Security Groups
EC2 Security Groups should allow application traffic from the
ALB Security Group rather than allowing unrestricted Internet
access to the EC2 instances.
```

```
Layer 5 – Application Authentication
Verifies the identity of the user.
```

```
Layer 6 – Application Authorization
Verifies that the authenticated user has the required Admin
role.
```

```
Layer 7 – MFA
Provides an additional authentication factor for administrative
accounts when supported.
```

```
============================================================
11. Final Architecture
============================================================
```

```
                         Internet
                       CloudFront
                          AWS WAF
              +-------------+-------------+
              |                           |
       Unauthorized /               Legitimate /
       Malicious Traffic            Authorized Traffic
              |                           |
              v                           v
            BLOCK                        ALB
```

```
              |              EC2 #1                EC2 #2
```

```
For the Admin Panel:
Authorized Admin
       |
       v
CloudFront
       |
       v
AWS WAF
       |
       +--> AdminProtection Exception
       |
       +--> Other WAF Protections
       |
       v
      ALB
       |
       v
      EC2
       |
       v
Authentication
       |
       v
Authorization
       |
       v
   Admin Panel
```

```
============================================================
12. Monitoring and Validation
============================================================
```

```
AWS WAF Sampled Requests were used to validate the behavior
of the Web ACL.
```

```
The following behaviors were successfully verified:
```

`1. /admin requests can be blocked by AWSManagedRulesAdminProtectionRuleSet.` 

`2. The AdminProtection_URIPATH rule correctly identifies common administrative paths.` 

`3. HTTP 403 responses can be traced back to the WAF.` 

`4. Internet scanners can reach the public-facing endpoint, confirming that the infrastructure is exposed to real Internet traffic.` 

`5. WAF rules inspect incoming requests before they reach the application infrastructure.` 

`6. COUNT-mode rules can be used to observe traffic patterns before changing them to enforcement/blocking behavior.` 

```
============================================================
13. Current Implementation Status
```

```
============================================================
```

# `COMPLETED:` 

- `[✓] AWS WAF Web ACL created/configured.` 

- `[✓] WAF integrated with the application architecture. [✓] Layer 7 security protections enabled. [✓] AWS Managed Common Rule Set configured. [✓] AWS Managed SQL Injection Rule Set configured.` 

- `[✓] AWS Managed Admin Protection Rule Set configured.` 

- `[✓] IPv4 Allowlist capability configured.` 

- `[✓] IPv6 Allowlist capability configured.` 

- `[✓] IPv4 Blocklist capability configured.` 

- `[✓] IPv6 Blocklist capability configured.` 

- `[✓] Geographic restriction configured.` 

- `[✓] Global rate-based monitoring configured.` 

- `[✓] Body size restriction monitoring configured. [✓] Anti-DDoS rule set enabled in COUNT mode. [✓] /admin blocking behavior tested.` 

- `[✓] 403 response successfully traced to AdminProtection_URIPATH.` 

- `[✓] Automated Internet scanner traffic detected and analyzed.` 

# `PLANNED:` 

- `[ ] Create the lumina-admin-allowed-ips IP Set.` 

- `[ ] Add authorized administrative Public IP addresses.` 

- `[ ] Configure a controlled AdminProtection exception.` 

- `[ ] Review and finalize WAF rule priorities.` 

- `[ ] Test authorized Admin access.` 

- `[ ] Test unauthorized Admin access.` 

- `[ ] Confirm that the remaining WAF protections continue to inspect authorized Admin requests.` 

- `[ ] Verify application-level Authentication and Authorization.` 

- `[ ] Enable/verify MFA for administrative accounts where applicable.` 

```
============================================================
14. Final Security Objective
============================================================
```

```
The final WAF implementation is designed to provide a
multi-layered security boundary between the public Internet
and the Lumina Dental application.
```

```
The intended security model is:
```

```
Internet
   |
   v
CloudFront
   |
   v
AWS WAF
   |
   +--> Malicious Traffic --------> BLOCK
   |
   +--> Unauthorized Admin -------> BLOCK
   |
   +--> SQL Injection ------------> BLOCK
   |
   +--> Common Web Attacks -------> BLOCK
   |
   +--> Excessive Traffic --------> MONITOR / BLOCK
   |
   +--> Legitimate Traffic -------> ALB
                                      |
                                      v
                                     EC2
                                      |
                                      v
                                  Application
                                      |
                                      v
                                Authentication
                                      |
                                      v
                                Authorization
                                      |
                                      v
                                  RDS
```

```
This architecture ensures that AWS WAF provides the first
application-layer security boundary while application-level
authentication and authorization remain responsible for
controlling access to protected functionality such as the
Admin Panel.
```

```
============================================================
```

