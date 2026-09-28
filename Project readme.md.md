# DevOps Django AWS Project

A complete DevOps practical project deploying a Dockerized Django application on AWS with PostgreSQL RDS, Nginx, Application Load Balancer, Auto Scaling Group, CloudWatch monitoring, ECR, IAM, Secrets Manager and automated EC2 provisioning using Launch Template User Data.

---

# 1. Project Summary

This project demonstrates a production-style AWS architecture:

```text
                         INTERNET
                            |
                            v
                 +---------------------+
                 |   Application       |
                 |   Load Balancer     |
                 |   Port 80           |
                 +----------+----------+
                            |
                     Target Group
                         Port 80
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          EC2  ASG     EC2  ASG     EC2  ASG
           Nginx          Nginx          Nginx
             |              |              |
             v              v              v
          Docker         Docker         Docker
          Django         Django         Django
             |              |              |
             +--------------+--------------+
                            |
                            v
                 +---------------------+
                 | PostgreSQL RDS      |
                 | Private Subnets     |
                 | Port 5432           |
                 +---------------------+
```

The application is:

```text
Django
   |
Gunicorn
   |
Docker
   |
Nginx
   |
ALB
   |
Internet
```

The database is separated from the application tier:

```text
EC2 Django ---> PostgreSQL RDS
```

The Auto Scaling Group automatically creates new EC2 instances from the Launch Template.

The new EC2 instance automatically:

1. Installs Docker.
2. Installs Nginx.
3. Installs AWS CLI.
4. Logs into ECR.
5. Pulls the Django image.
6. Reads the database credentials from Secrets Manager.
7. Creates the Django environment file.
8. Connects to RDS.
9. Runs Django migrations.
10. Starts the Django container.
11. Configures Nginx.
12. Starts Nginx.
13. Becomes healthy in the Target Group.

No manual configuration is required on the new EC2 instance.

---

# 2. AWS Architecture

## Region

This project uses:

```text
us-east-1
```

Change the region if required, but use the same region consistently for all AWS resources.

---

# 3. Resources Used

The final project contains:

```text
VPC
├── Public Subnet A
├── Public Subnet B
├── Private Subnet A
└── Private Subnet B

Internet Gateway

NAT Gateway
(optional depending on final architecture)

Security Groups
├── alb-sg
├── ec2-sg
└── rds-sg

Application Load Balancer
└── Target Group

Auto Scaling Group
└── Launch Template

EC2
├── Nginx
└── Docker
    └── Django

Amazon ECR
└── devops-django-app

Amazon RDS
└── PostgreSQL

AWS Secrets Manager
└── devops-django/rds

IAM
└── DevOpsDjangoEC2ECRRole

CloudWatch
└── Target Tracking alarms
```

---

# 4. Prerequisites

## Local Windows machine

Install:

```text
Git
Python
Docker Desktop
AWS CLI
VS Code
```

Check:

```powershell
python --version
docker --version
git --version
aws --version
```

Example:

```text
Python 3.x
Docker 29.x
Git 2.x
AWS CLI 2.x
```

---

# 5. Configure AWS CLI

Run:

```powershell
aws configure
```

Enter:

```text
AWS Access Key ID:
AWS Secret Access Key:
Default region name:
Default output format:
```

Use:

```text
us-east-1
json
```

Verify:

```powershell
aws sts get-caller-identity
```

Example:

```json
{
    "UserId": "XXXXXXXXXXXX",
    "Account": "YOUR_ACCOUNT_ID",
    "Arn": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_USER"
}
```

Do not put AWS access keys, secret keys or passwords into GitHub.

---

# 6. Create Project Directory

PowerShell:

```powershell
cd "E:\DevOps\Aws Practice"
```

Create the project:

```powershell
mkdir DevOps-Django-AWS-Project
```

Enter:

```powershell
cd DevOps-Django-AWS-Project
```

Create the application directory:

```powershell
mkdir app
```

Enter:

```powershell
cd app
```

Open VS Code:

```powershell
code .
```

---

# 7. Create Python Virtual Environment

Inside the `app` directory:

```powershell
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\venv\Scripts\Activate.ps1
```

Verify:

```powershell
python --version
pip --version
```

---

# 8. Install Django

Install:

```powershell
pip install django
```

Install Gunicorn:

```powershell
pip install gunicorn
```

Install PostgreSQL driver:

```powershell
pip install "psycopg[binary]"
```

Check:

```powershell
pip list
```

---

# 9. Create Django Project

Run:

```powershell
django-admin startproject config .
```

Create application:

```powershell
python manage.py startapp core
```

Run migrations:

```powershell
python manage.py migrate
```

Create administrator:

```powershell
python manage.py createsuperuser
```

Run Django:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Stop Django:

```text
CTRL + C
```

---

# 10. Configure Django Application

Edit:

```text
core/views.py
```

Use:

```python
from django.http import JsonResponse
import socket

def home(request):
    return JsonResponse({
        "application": "DevOps Django AWS Project",
        "status": "running",
        "server": socket.gethostname(),
        "message": "Django application is working"
    })

def health(request):
    return JsonResponse({
        "status": "healthy",
        "server": socket.gethostname()
    })
```

The hostname is useful when testing the Load Balancer because different EC2 instances can return different hostnames.

---

# 11. Configure URLs

Edit:

```text
config/urls.py
```

Use:

```python
from django.contrib import admin
from django.urls import path
from core.views import home, health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home),
    path("health/", health),
]
```

Test:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Health:

```text
http://127.0.0.1:8000/health/
```

Expected:

```json
{
    "status": "healthy",
    "server": "..."
}
```

---

# 12. Configure PostgreSQL in Django

Edit:

```text
config/settings.py
```

Add:

```python
import os
```

Use:

```python
ALLOWED_HOSTS = ["*"]
```

For this lab, the database configuration is:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "devopsdb"),
        "USER": os.getenv("DB_USER", "django_admin"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv(
            "DB_HOST",
            "YOUR_RDS_ENDPOINT"
        ),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
```

Replace:

```text
YOUR_RDS_ENDPOINT
```

with the RDS endpoint.

Do not put the actual RDS password into `settings.py`.

---

# 13. Create requirements.txt

Run:

```powershell
pip freeze > requirements.txt
```

For a clean project, `requirements.txt` should contain at least:

```text
Django==5.2.17
gunicorn
psycopg[binary]
```

Check:

```powershell
type requirements.txt
```

---

# 14. Create Dockerfile

Create:

```text
Dockerfile
```

Content:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

---

# 15. Create .dockerignore

Create:

```text
.dockerignore
```

Content:

```text
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.gitignore
.env
db.sqlite3
```

Never copy:

```text
venv
.env
AWS credentials
database passwords
```

into the Docker image.

---

# 16. Build Docker Image

Check Docker:

```powershell
docker version
```

Build:

```powershell
docker build --no-cache -t devops-django-app:1.0 .
```

Check:

```powershell
docker images
```

---

# 17. Run Django Container Locally

Run:

```powershell
docker run -d `
  --name devops-django `
  -p 8000:8000 `
  devops-django-app:1.0
```

Check:

```powershell
docker ps
```

Check logs:

```powershell
docker logs devops-django
```

Test:

```powershell
curl http://localhost:8000/health/
```

Expected:

```json
{
    "status": "healthy"
}
```

Stop:

```powershell
docker stop devops-django
```

Remove:

```powershell
docker rm devops-django
```

---

# 18. Create Amazon ECR Repository

Create repository:

```powershell
aws ecr create-repository `
  --repository-name devops-django-app `
  --region us-east-1
```

List repositories:

```powershell
aws ecr describe-repositories `
  --region us-east-1
```

Get AWS account ID:

```powershell
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
```

Check:

```powershell
echo $ACCOUNT_ID
```

Set variables:

```powershell
$REGION="us-east-1"
$REPOSITORY="devops-django-app"
```

Create ECR URI:

```powershell
$ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY"
```

Check:

```powershell
echo $ECR_URI
```

---

# 19. Login to ECR

Run:

```powershell
aws ecr get-login-password --region us-east-1 |
docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"
```

Expected:

```text
Login Succeeded
```

---

# 20. Build Final Application Image

Build:

```powershell
docker build --no-cache -t devops-django-app:2.1 .
```

Tag:

```powershell
docker tag `
  devops-django-app:2.1 `
  "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1"
```

Check:

```powershell
docker images
```

Push:

```powershell
docker push `
  "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1"
```

Verify:

```powershell
aws ecr list-images `
  --repository-name devops-django-app `
  --region us-east-1
```

---

# 21. AWS VPC Architecture

Create:

VPC:

```text
10.0.0.0/16
```

Public subnet A:

```text
10.0.1.0/24
```

Public subnet B:

```text
10.0.2.0/24
```

Private subnet A:

```text
10.0.11.0/24
```

Private subnet B:

```text
10.0.12.0/24
```

Recommended layout:

```text
VPC
10.0.0.0/16
|
+-- Public-A
|   10.0.1.0/24
|
+-- Public-B
|   10.0.2.0/24
|
+-- Private-A
|   10.0.11.0/24
|
+-- Private-B
    10.0.12.0/24
```

---

# 22. Create VPC Through AWS Console

Open:

```text
AWS Console
→ VPC
→ Your VPCs
→ Create VPC
```

Select:

```text
Resources to create:
VPC only
```

Name:

```text
devops-django-vpc
```

IPv4 CIDR:

```text
10.0.0.0/16
```

Create.

---

# 23. Create Subnets

Create four subnets.

## Public-A

```text
Name: devops-public-a
CIDR: 10.0.1.0/24
```

## Public-B

```text
Name: devops-public-b
CIDR: 10.0.2.0/24
```

## Private-A

```text
Name: devops-private-a
CIDR: 10.0.11.0/24
```

## Private-B

```text
Name: devops-private-b
CIDR: 10.0.12.0/24
```

Make sure all four belong to:

```text
devops-django-vpc
```

Use different Availability Zones for the two public subnets and two private subnets.

---

# 24. Internet Gateway

Go to:

```text
VPC
→ Internet Gateways
→ Create internet gateway
```

Name:

```text
devops-django-igw
```

Attach it to:

```text
devops-django-vpc
```

---

# 25. Public Route Table

Create:

```text
devops-public-rt
```

Add route:

```text
Destination: 0.0.0.0/0
Target: Internet Gateway
```

Associate:

```text
Public-A
Public-B
```

---

# 26. NAT Gateway

If private resources require outbound Internet access:

Create NAT Gateway in:

```text
Public-A
```

Allocate an Elastic IP.

Then create:

```text
devops-private-rt
```

Route:

```text
0.0.0.0/0
→ NAT Gateway
```

Associate:

```text
Private-A
Private-B
```

For this project, the application EC2 instances are placed in public subnets, while RDS remains private.

---

# 27. Security Groups

Create three security groups.

```text
alb-sg
ec2-sg
rds-sg
```

---

# 28. ALB Security Group

Name:

```text
alb-sg
```

Inbound:

```text
HTTP
TCP
80
Source: 0.0.0.0/0
```

Optional:

```text
HTTPS
TCP
443
Source: 0.0.0.0/0
```

The HTTPS rule alone does NOT create an HTTPS listener.

For this lab, the ALB uses:

```text
HTTP :80
```

Outbound:

```text
All traffic
0.0.0.0/0
```

---

# 29. EC2 Security Group

Name:

```text
ec2-sg
```

Inbound:

```text
HTTP
TCP
80
Source: alb-sg
```

SSH:

```text
SSH
TCP
22
Source: YOUR_PUBLIC_IP/32
```

Do NOT allow:

```text
HTTP 80 from 0.0.0.0/0
```

The ALB should be the public entry point.

Outbound:

```text
All traffic
0.0.0.0/0
```

---

# 30. RDS Security Group

Name:

```text
rds-sg
```

Inbound:

```text
PostgreSQL
TCP
5432
Source: ec2-sg
```

Do NOT allow:

```text
5432 from 0.0.0.0/0
```

Outbound:

```text
All traffic
```

---

# 31. Create RDS Subnet Group

AWS Console:

```text
RDS
→ Subnet groups
→ Create DB subnet group
```

Name:

```text
devops-django-db-subnet
```

VPC:

```text
devops-django-vpc
```

Subnets:

```text
Private-A
Private-B
```

---

# 32. Create PostgreSQL RDS

Go to:

```text
RDS
→ Databases
→ Create database
```

Engine:

```text
PostgreSQL
```

Database name:

```text
devops-django-db
```

Initial database:

```text
devopsdb
```

Username:

```text
django_admin
```

Password:

```text
YOUR_STRONG_PASSWORD
```

Connectivity:

```text
VPC:
devops-django-vpc

DB subnet group:
devops-django-db-subnet

Public access:
No

Security group:
rds-sg

Port:
5432
```

Create database.

Wait until:

```text
Status: Available
```

---

# 33. Important RDS Check

Copy the RDS endpoint.

It will look similar to:

```text
devops-django-db.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com
```

Do not commit the endpoint if you want the repository to remain environment-neutral.

---

# 34. Test RDS From EC2

SSH into an EC2 instance.

Install PostgreSQL client:

```bash
sudo apt update
sudo apt install -y postgresql-client
```

Test DNS:

```bash
getent hosts YOUR_RDS_ENDPOINT
```

Test port:

```bash
nc -zv YOUR_RDS_ENDPOINT 5432
```

Expected:

```text
Connection to YOUR_RDS_ENDPOINT 5432 port [tcp/postgresql] succeeded!
```

This only proves TCP connectivity.

It does not prove database authentication.

---

# 35. Connect to PostgreSQL

Run:

```bash
psql \
  -h YOUR_RDS_ENDPOINT \
  -U django_admin \
  -d devopsdb
```

Enter the RDS password.

Inside PostgreSQL:

```text
\l
```

Expected database:

```text
devopsdb
```

Exit:

```text
\q
```

---

# 36. Create AWS Secrets Manager Secret

Go to:

```text
AWS Console
→ Secrets Manager
→ Store a new secret
```

Secret type:

```text
Other type of secret
```

Create key/value values:

```text
DB_NAME=devopsdb
DB_USER=django_admin
DB_PASSWORD=YOUR_RDS_PASSWORD
DB_HOST=YOUR_RDS_ENDPOINT
DB_PORT=5432
```

Secret name:

```text
devops-django/rds
```

Save the secret.

Never commit this secret to GitHub.

---

# 37. IAM Role for EC2

Create IAM role:

```text
DevOpsDjangoEC2ECRRole
```

Trusted entity:

```text
EC2
```

Attach:

```text
AmazonEC2ContainerRegistryReadOnly
```

Add an inline policy for Secrets Manager:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadDjangoDatabaseSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:devops-django/rds-*"
    }
  ]
}
```

Replace:

```text
YOUR_ACCOUNT_ID
```

with your AWS account ID.

---

# 38. Create EC2 Instance

Create Ubuntu:

```text
Ubuntu 24.04 LTS
```

Instance type:

```text
t3.micro
```

Subnet:

```text
Public-A
```

Auto-assign public IPv4:

```text
Enable
```

Security group:

```text
ec2-sg
```

IAM instance profile:

```text
DevOpsDjangoEC2ECRRole
```

SSH into the instance.

---

# 39. Install Docker on EC2

Run:

```bash
sudo apt update
```

Install:

```bash
sudo apt install -y docker.io
```

Enable:

```bash
sudo systemctl enable docker
```

Start:

```bash
sudo systemctl start docker
```

Check:

```bash
sudo systemctl status docker
```

Check version:

```bash
docker --version
```

---

# 40. Install AWS CLI

```bash
sudo apt install -y awscli
```

Check:

```bash
aws --version
```

Verify IAM role:

```bash
aws sts get-caller-identity
```

The returned ARN should contain:

```text
DevOpsDjangoEC2ECRRole
```

---

# 41. Test Secrets Manager From EC2

Run:

```bash
aws secretsmanager get-secret-value \
  --secret-id devops-django/rds \
  --region us-east-1
```

If successful, the EC2 role can read the secret.

Do not paste the secret value into GitHub or documentation.

---

# 42. Login to ECR From EC2

```bash
aws ecr get-login-password \
  --region us-east-1 \
  | sudo docker login \
      --username AWS \
      --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

Expected:

```text
Login Succeeded
```

---

# 43. Pull Django Image

```bash
sudo docker pull \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1
```

Check:

```bash
sudo docker images
```

---

# 44. Create Django Environment File

Create:

```bash
sudo nano /home/ubuntu/django.env
```

Content:

```text
DB_NAME=devopsdb
DB_USER=django_admin
DB_PASSWORD=YOUR_RDS_PASSWORD
DB_HOST=YOUR_RDS_ENDPOINT
DB_PORT=5432
```

Protect it:

```bash
sudo chmod 600 /home/ubuntu/django.env
```

Change ownership:

```bash
sudo chown ubuntu:ubuntu /home/ubuntu/django.env
```

---

# 45. Run Django Database Migration

Run:

```bash
sudo docker run --rm \
  --env-file /home/ubuntu/django.env \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1 \
  python manage.py migrate
```

Expected:

```text
Applying ... OK
```

---

# 46. Start Django Container

Run:

```bash
sudo docker run -d \
  --name django-app \
  --restart unless-stopped \
  --env-file /home/ubuntu/django.env \
  -p 8000:8000 \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1
```

Check:

```bash
sudo docker ps
```

Expected:

```text
0.0.0.0:8000->8000/tcp
```

---

# 47. Test Django

Run:

```bash
curl -i http://localhost:8000/
```

Health:

```bash
curl -i http://localhost:8000/health/
```

Expected:

```text
HTTP/1.1 200 OK
```

and:

```json
{
    "status": "healthy"
}
```

---

# 48. Install Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

Enable:

```bash
sudo systemctl enable nginx
```

Start:

```bash
sudo systemctl start nginx
```

Check:

```bash
sudo systemctl status nginx
```

---

# 49. Configure Nginx

Remove default site:

```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

Create:

```bash
sudo nano /etc/nginx/sites-available/django
```

Use:

```nginx
server {

    listen 80;
    listen [::]:80;

    server_name _;

    location / {

        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -sf \
  /etc/nginx/sites-available/django \
  /etc/nginx/sites-enabled/django
```

Test:

```bash
sudo nginx -t
```

Expected:

```text
syntax is ok
test is successful
```

Restart:

```bash
sudo systemctl restart nginx
```

---

# 50. Test Nginx → Django

Run:

```bash
curl -i http://localhost/
```

Health:

```bash
curl -i http://localhost/health/
```

Traffic flow:

```text
Browser
   |
   v
Nginx :80
   |
   v
Django :8000
```

---

# 51. Create Target Group

AWS Console:

```text
EC2
→ Target Groups
→ Create target group
```

Target type:

```text
Instances
```

Name:

```text
devops-django-tg
```

Protocol:

```text
HTTP
```

Port:

```text
80
```

VPC:

```text
devops-django-vpc
```

Health check protocol:

```text
HTTP
```

Health check path:

```text
/health/
```

Port:

```text
Traffic port
```

Success codes:

```text
200
```

Recommended:

```text
Healthy threshold: 2
Unhealthy threshold: 2
Timeout: 5 seconds
Interval: 30 seconds
```

Register the initial EC2 instances.

---

# 52. Test Target Group

Each EC2 must answer:

```bash
curl -i http://localhost/health/
```

Expected:

```text
HTTP/1.1 200 OK
```

In AWS:

```text
EC2
→ Target Groups
→ devops-django-tg
→ Targets
```

Wait for:

```text
healthy
```

---

# 53. Create Application Load Balancer

AWS Console:

```text
EC2
→ Load Balancers
→ Create Load Balancer
```

Select:

```text
Application Load Balancer
```

Name:

```text
devops-django-alb
```

Scheme:

```text
Internet-facing
```

IP address type:

```text
IPv4
```

VPC:

```text
devops-django-vpc
```

Subnets:

```text
Public-A
Public-B
```

Security group:

```text
alb-sg
```

Listener:

```text
HTTP
Port 80
```

Default action:

```text
Forward to
devops-django-tg
```

Create the ALB.

---

# 54. Test ALB

Copy the ALB DNS name.

Example:

```text
devops-django-alb-xxxxxxxx.us-east-1.elb.amazonaws.com
```

Browser:

```text
http://YOUR_ALB_DNS/
```

Health:

```text
http://YOUR_ALB_DNS/health/
```

PowerShell:

```powershell
curl http://YOUR_ALB_DNS/health/
```

Expected:

```json
{
    "status": "healthy",
    "server": "..."
}
```

---

# 55. Why ALB Uses Port 80

The traffic path is:

```text
Internet
   |
   | HTTP :80
   v
ALB
   |
   | HTTP :80
   v
Nginx
   |
   | HTTP :8000
   v
Django
```

The ALB does not directly connect to Django port 8000.

The Target Group uses:

```text
Port 80
```

because Nginx listens on port 80.

Nginx then forwards to:

```text
127.0.0.1:8000
```

---

# 56. Create Launch Template

AWS Console:

```text
EC2
→ Launch Templates
→ Create launch template
```

Name:

```text
devops-django-launch-template
```

AMI:

```text
Ubuntu 24.04 LTS
```

Instance type:

```text
t3.micro
```

Key pair:

```text
YOUR_KEY_PAIR
```

Security group:

```text
ec2-sg
```

IAM instance profile:

```text
DevOpsDjangoEC2ECRRole
```

Do not hard-code a subnet if the ASG will select multiple subnets.

---

# 57. Launch Template User Data

The most important part of the project is User Data.

The purpose is:

```text
New EC2
   |
   +-- install Docker
   +-- install Nginx
   +-- install AWS CLI
   +-- authenticate ECR
   +-- pull application image
   +-- read Secrets Manager
   +-- create django.env
   +-- connect to RDS
   +-- migrate database
   +-- start Django
   +-- configure Nginx
   +-- start Nginx
   +-- pass health check
```

Use the following User Data.

IMPORTANT:

Replace:

```text
YOUR_ACCOUNT_ID
```

with your AWS account ID.

```bash
#!/bin/bash

set -euo pipefail

LOG_FILE="/var/log/devops-django-user-data.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "===== USER DATA STARTED ====="

export DEBIAN_FRONTEND=noninteractive

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"
ECR_REPOSITORY="devops-django-app"
IMAGE_TAG="2.1"

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

SECRET_NAME="devops-django/rds"

echo "===== SYSTEM UPDATE ====="

apt-get update -y

echo "===== INSTALL PACKAGES ====="

apt-get install -y \
    docker.io \
    nginx \
    postgresql-client \
    netcat-openbsd \
    awscli \
    jq \
    curl

echo "===== START DOCKER ====="

systemctl enable docker
systemctl start docker

echo "===== START NGINX ====="

systemctl enable nginx
systemctl start nginx

echo "===== ECR LOGIN ====="

aws ecr get-login-password \
    --region "$AWS_REGION" \
    | docker login \
        --username AWS \
        --password-stdin "$ECR_REGISTRY"

echo "===== PULL APPLICATION IMAGE ====="

docker pull "$IMAGE"

echo "===== READ DATABASE SECRET ====="

SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$AWS_REGION" \
    --query SecretString \
    --output text)

DB_NAME=$(echo "$SECRET_JSON" | jq -r '.DB_NAME')
DB_USER=$(echo "$SECRET_JSON" | jq -r '.DB_USER')
DB_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.DB_PASSWORD')
DB_HOST=$(echo "$SECRET_JSON" | jq -r '.DB_HOST')
DB_PORT=$(echo "$SECRET_JSON" | jq -r '.DB_PORT')

echo "===== CREATE DATABASE ENVIRONMENT ====="

cat > /home/ubuntu/django.env <<EOF
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
EOF

chmod 600 /home/ubuntu/django.env
chown ubuntu:ubuntu /home/ubuntu/django.env

echo "===== WAIT FOR RDS ====="

RDS_READY=false

for i in {1..30}
do
    if nc -z "$DB_HOST" "$DB_PORT"
    then
        echo "RDS is reachable."
        RDS_READY=true
        break
    fi

    echo "Waiting for RDS... attempt $i/30"
    sleep 10
done

if [ "$RDS_READY" != "true" ]
then
    echo "RDS did not become reachable."
    exit 1
fi

echo "===== DATABASE MIGRATION ====="

docker run --rm \
    --env-file /home/ubuntu/django.env \
    "$IMAGE" \
    python manage.py migrate --noinput

echo "===== REMOVE OLD CONTAINER ====="

docker rm -f django-app 2>/dev/null || true

echo "===== START DJANGO ====="

docker run -d \
    --name django-app \
    --restart unless-stopped \
    --env-file /home/ubuntu/django.env \
    -p 8000:8000 \
    "$IMAGE"

echo "===== WAIT FOR DJANGO ====="

DJANGO_READY=false

for i in {1..30}
do

    if curl -fsS http://127.0.0.1:8000/health/
    then
        echo
        echo "Django is healthy."
        DJANGO_READY=true
        break
    fi

    echo "Waiting for Django... attempt $i/30"
    sleep 5
done

if [ "$DJANGO_READY" != "true" ]
then
    echo "Django failed health check."
    docker logs django-app || true
    exit 1
fi

echo "===== CONFIGURE NGINX ====="

rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/django <<'EOF'
server {

    listen 80;
    listen [::]:80;

    server_name _;

    location / {

        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

    }
}
EOF

ln -sf \
    /etc/nginx/sites-available/django \
    /etc/nginx/sites-enabled/django

echo "===== TEST NGINX ====="

nginx -t

echo "===== RESTART NGINX ====="

systemctl enable nginx
systemctl restart nginx

echo "===== FINAL HEALTH CHECK ====="

NGINX_READY=false

for i in {1..30}
do

    if curl -fsS http://127.0.0.1/health/
    then
        echo
        echo "Nginx -> Django health check successful."
        NGINX_READY=true
        break
    fi

    echo "Waiting for Nginx... attempt $i/30"
    sleep 5
done

if [ "$NGINX_READY" != "true" ]
then
    echo "Nginx health check failed."
    systemctl status nginx --no-pager || true
    exit 1
fi

echo "===== DOCKER STATUS ====="

docker ps

echo "===== NGINX STATUS ====="

systemctl --no-pager status nginx || true

echo "===== USER DATA COMPLETED ====="
```

---

# 58. Important User Data Security Note

Do not use:

```bash
set -x
```

when handling database passwords.

It can expose commands and secret-related values in logs.

Use:

```bash
set -euo pipefail
```

instead.

Never print:

```text
DB_PASSWORD
AWS SecretString
AWS access keys
```

to public logs or GitHub.

---

# 59. Create Auto Scaling Group

AWS Console:

```text
EC2
→ Auto Scaling Groups
→ Create Auto Scaling group
```

Name:

```text
devops-django-asg
```

Launch template:

```text
devops-django-launch-template
```

Use the latest version.

VPC:

```text
devops-django-vpc
```

Subnets:

```text
Public-A
Public-B
```

Desired capacity:

```text
2
```

Minimum:

```text
2
```

Maximum:

```text
4
```

Attach existing load balancer:

```text
devops-django-tg
```

Health check:

```text
EC2
ELB
```

Recommended health check grace period:

```text
300 seconds
```

---

# 60. Auto Scaling Policy

Create:

```text
Target tracking scaling policy
```

Metric:

```text
Average CPU utilization
```

Example target:

```text
50%
```

This means:

```text
CPU > target
    |
    v
ASG may launch instances

CPU < target for sufficient time
    |
    v
ASG may terminate excess instances
```

Do not expect scaling to happen instantly.

CloudWatch needs enough data points and the ASG has cooldown/warm-up behavior.

---

# 61. Verify Auto Scaling Group

Check:

```text
EC2
→ Auto Scaling Groups
→ devops-django-asg
→ Activity
```

Instances should become:

```text
InService
```

Target Group should show:

```text
healthy
```

---

# 62. Verify Automatically Created EC2

SSH into a newly created instance if it has a reachable address.

Check:

```bash
sudo docker ps
```

Expected:

```text
django-app
```

Check image:

```bash
sudo docker images
```

Check environment file:

```bash
sudo ls -l /home/ubuntu/django.env
```

Expected permissions similar to:

```text
-rw------- ubuntu ubuntu
```

Check Nginx:

```bash
sudo systemctl status nginx
```

Check Docker:

```bash
sudo systemctl status docker
```

Check User Data log:

```bash
sudo cat /var/log/devops-django-user-data.log
```

---

# 63. User Data Debugging Commands

If a new instance does not become healthy:

```bash
sudo cat /var/log/cloud-init-output.log
```

Also:

```bash
sudo cat /var/log/devops-django-user-data.log
```

Check Docker:

```bash
sudo systemctl status docker
```

Check container:

```bash
sudo docker ps -a
```

Check logs:

```bash
sudo docker logs django-app
```

Check Nginx:

```bash
sudo nginx -t
sudo systemctl status nginx
```

Check Django:

```bash
curl -i http://127.0.0.1:8000/health/
```

Check Nginx:

```bash
curl -i http://127.0.0.1/health/
```

Check RDS:

```bash
nc -zv YOUR_RDS_ENDPOINT 5432
```

Check Secrets Manager:

```bash
aws secretsmanager get-secret-value \
  --secret-id devops-django/rds \
  --region us-east-1
```

Check ECR:

```bash
aws ecr describe-repositories \
  --repository-names devops-django-app \
  --region us-east-1
```

---

# 64. CloudWatch

AWS Console:

```text
CloudWatch
→ Alarms
```

The ASG target tracking policy creates alarms automatically.

You may see alarms similar to:

```text
TargetTracking-devops-django-asg-AlarmHigh-...
TargetTracking-devops-django-asg-AlarmLow-...
```

The high alarm is related to scaling out.

The low alarm is related to scaling in.

---

# 65. Test Load Balancer

First obtain the ALB DNS:

```text
EC2
→ Load Balancers
→ devops-django-alb
```

Copy DNS name.

Test:

```bash
curl http://YOUR_ALB_DNS/
```

Health:

```bash
curl http://YOUR_ALB_DNS/health/
```

Run repeatedly (PowerShell):

```powershell
while ($true) {
    curl http://YOUR_ALB_DNS/
}
```

Stop:

```text
CTRL + C
```

---

# 66. Linux Load Test Script

Create:

```bash
nano load-test.sh
```

Content:

```bash
#!/bin/bash

ALB_URL="http://YOUR_ALB_DNS"

echo "======================================"
echo " HIGH LOAD TEST"
echo "======================================"

echo "Target: $ALB_URL"
echo "Press CTRL+C to stop"
echo

while true
do

    echo "Starting high-load batch..."

    for i in {1..500}
    do

        (
            while true
            do

                curl -s \
                    -o /dev/null \
                    --max-time 10 \
                    "$ALB_URL/"

            done

        ) &

    done

    echo "Started 500 concurrent workers."

    echo "Current workers: $(jobs -rp | wc -l)"

    wait

done
```

Make executable:

```bash
chmod +x load-test.sh
```

Run:

```bash
./load-test.sh
```

Stop:

```text
CTRL + C
```

---

# 67. Monitor CPU

AWS Console:

```text
CloudWatch
→ Metrics
→ EC2
→ Per-Instance Metrics
```

Watch:

```text
CPUUtilization
```

Also monitor:

```text
EC2
→ Auto Scaling Groups
→ devops-django-asg
→ Activity
```

---

# 68. Demonstrate Scale-Out

Initial state:

```text
Desired: 2
Minimum: 2
Maximum: 4
```

Run:

```bash
./load-test.sh
```

Monitor:

```text
CloudWatch CPU
```

and:

```text
ASG Activity
```

The ASG may launch additional instances when the scaling policy conditions are met.

Possible state:

```text
2 instances
      |
      | CPU load
      v
3 instances
      |
      | continued load
      v
4 instances
```

Do not assume scaling occurs immediately.

---

# 69. Verify New EC2 Automation

When a new instance launches:

```text
EC2
→ Instances
```

Open the new instance.

Verify:

```text
Docker installed
Nginx installed
Django container running
Target Group healthy
```

On the instance:

```bash
sudo docker ps
sudo systemctl status nginx
curl http://localhost/health/
```

The critical test is that the new instance was configured by User Data.

No manual installation should be required.

---

# 70. Demonstrate Scale-In

Stop the load test:

```text
CTRL + C
```

Wait for CPU to decrease.

CloudWatch should eventually provide the low utilization data required by the scaling policy.

The ASG can then reduce capacity.

For example:

```text
4 instances
     |
     | low CPU
     v
3 instances
     |
     | low CPU
     v
2 instances
```

Minimum capacity remains:

```text
2
```

---

# 71. Final Health Check

ALB:

```bash
curl http://YOUR_ALB_DNS/health/
```

Target Group:

```text
Healthy
```

ASG:

```text
Desired = 2
Minimum = 2
Maximum = 4
```

RDS:

```text
Available
```

Docker:

```bash
sudo docker ps
```

Nginx:

```bash
sudo systemctl status nginx
```

Django:

```bash
curl http://localhost:8000/health/
```

Nginx:

```bash
curl http://localhost/health/
```

---

# 72. Useful Docker Commands

List containers:

```bash
sudo docker ps
```

List all containers:

```bash
sudo docker ps -a
```

Logs:

```bash
sudo docker logs django-app
```

Follow logs:

```bash
sudo docker logs -f django-app
```

Restart:

```bash
sudo docker restart django-app
```

Stop:

```bash
sudo docker stop django-app
```

Remove:

```bash
sudo docker rm django-app
```

Pull image:

```bash
sudo docker pull YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1
```

---

# 73. Useful Nginx Commands

Check status:

```bash
sudo systemctl status nginx
```

Start:

```bash
sudo systemctl start nginx
```

Stop:

```bash
sudo systemctl stop nginx
```

Restart:

```bash
sudo systemctl restart nginx
```

Reload:

```bash
sudo systemctl reload nginx
```

Enable:

```bash
sudo systemctl enable nginx
```

Configuration test:

```bash
sudo nginx -t
```

Show configuration:

```bash
sudo nginx -T
```

---

# 74. Useful System Commands

Check IP:

```bash
ip addr
```

Check routes:

```bash
ip route
```

Check listening ports:

```bash
sudo ss -tulpn
```

Check port 80:

```bash
sudo ss -tulpn | grep :80
```

Check port 8000:

```bash
sudo ss -tulpn | grep :8000
```

Check port 5432:

```bash
sudo ss -tulpn | grep :5432
```

Check disk:

```bash
df -h
```

Check memory:

```bash
free -h
```

Check CPU:

```bash
top
```

---

# 75. Common Problem: Django Module Not Found

Error:

```text
ModuleNotFoundError: No module named 'django'
```

Check:

```bash
docker run --rm YOUR_IMAGE python -c "import django; print(django.get_version())"
```

Check:

```bash
cat requirements.txt
```

It should contain:

```text
Django==5.2.17
gunicorn
psycopg[binary]
```

Rebuild:

```bash
docker build --no-cache -t devops-django-app:2.1 .
```

Push:

```bash
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.1
```

---

# 76. Common Problem: RDS Connection Failed

Check DNS:

```bash
getent hosts YOUR_RDS_ENDPOINT
```

Check port:

```bash
nc -zv YOUR_RDS_ENDPOINT 5432
```

Check:

```text
RDS Security Group
```

It must allow:

```text
TCP 5432
Source: ec2-sg
```

Check RDS:

```text
Public access: No
Status: Available
```

---

# 77. Common Problem: Database Does Not Exist

Error:

```text
FATAL: database "devopsdb" does not exist
```

Connect to RDS:

```bash
psql \
  -h YOUR_RDS_ENDPOINT \
  -U django_admin \
  -d postgres
```

Run:

```text
\l
```

Verify:

```text
devopsdb
```

If it does not exist, create it:

```sql
CREATE DATABASE devopsdb;
```

Then:

```text
\q
```

Run migration again:

```bash
sudo docker run --rm \
  --env-file /home/ubuntu/django.env \
  YOUR_IMAGE \
  python manage.py migrate
```

---

# 78. Common Problem: Target Group Unhealthy

Check:

```bash
curl -i http://localhost/health/
```

Then:

```bash
curl -i http://localhost:8000/health/
```

Both should return:

```text
HTTP 200
```

Check Nginx:

```bash
sudo nginx -t
```

Check:

```bash
sudo systemctl status nginx
```

Check Docker:

```bash
sudo docker ps
```

Target Group should use:

```text
Protocol: HTTP
Port: 80
Path: /health/
Success code: 200
```

---

# 79. Common Problem: Target Group Returns 301

A redirect such as:

```text
301
```

can cause the health check to fail if the target group expects:

```text
200
```

Check:

```bash
curl -I http://localhost/health/
```

Expected:

```text
HTTP/1.1 200 OK
```

Avoid an unnecessary HTTP → HTTPS redirect for the health-check endpoint unless the Target Group success-code configuration is intentionally changed.

For this lab, use:

```text
HTTP
/health/
200
```

---

# 80. Common Problem: Nginx 502 Bad Gateway

Check Django:

```bash
sudo docker ps
```

Then:

```bash
curl http://localhost:8000/health/
```

If Django is not responding:

```bash
sudo docker logs django-app
```

Restart:

```bash
sudo docker restart django-app
```

Check Nginx:

```bash
sudo nginx -t
```

Then:

```bash
sudo systemctl restart nginx
```

---

# 81. Common Problem: ECR Access Denied

Check IAM role:

```bash
aws sts get-caller-identity
```

Check ECR:

```bash
aws ecr describe-repositories \
  --repository-names devops-django-app \
  --region us-east-1
```

Login:

```bash
aws ecr get-login-password \
  --region us-east-1 \
  | sudo docker login \
      --username AWS \
      --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

The EC2 IAM role needs:

```text
AmazonEC2ContainerRegistryReadOnly
```

---

# 82. Common Problem: Secrets Manager AccessDenied

Run:

```bash
aws secretsmanager get-secret-value \
  --secret-id devops-django/rds \
  --region us-east-1
```

If AccessDenied appears:

Check IAM role:

```text
DevOpsDjangoEC2ECRRole
```

It must have:

```text
secretsmanager:GetSecretValue
```

for:

```text
devops-django/rds
```

---

# 83. Common Problem: New ASG Instance Has No Public IP

This is not automatically a problem.

The important traffic path is:

```text
ALB
   |
   v
EC2 private IP
```

The EC2 instance does not need a public IP for ALB → EC2 traffic.

For this architecture, public IPs are primarily useful for direct administration/testing.

If SSH access to automatically created instances is required, configure the Launch Template accordingly.

---

# 84. Common Problem: ALB Has HTTP but No HTTPS

Security Group:

```text
HTTPS 443
```

does not automatically create an HTTPS listener.

A listener must be configured separately.

For this lab:

```text
HTTP :80
```

is sufficient.

HTTPS requires:

```text
ACM certificate
+
HTTPS listener :443
+
Target Group
```

---

# 85. Verify Complete Architecture

The final traffic flow must be:

```text
User
 |
 | HTTP :80
 v
Application Load Balancer
 |
 | HTTP :80
 v
Target Group
 |
 +-----------------------+
 |                       |
 v                       v
EC2 Instance             EC2 Instance
 |                       |
Nginx :80               Nginx :80
 |                       |
Docker :8000            Docker :8000
 |                       |
Django                   Django
 \                       /
  \                     /
   +------- RDS --------+
           PostgreSQL
           :5432
```

The database must not be publicly accessible.

---

# 86. Git Repository Structure

Recommended:

```text
DevOps-Django-AWS-Project/
│
├── app/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   └── core/
│       ├── views.py
│       ├── models.py
│       ├── admin.py
│       └── apps.py
│
├── user-data/
│   └── bootstrap.sh
│
├── scripts/
│   └── load-test.sh
│
└── README.md
```

---

# 87. .gitignore

Create:

```text
.gitignore
```

Content:

```text
venv/
__pycache__/
*.pyc
.env
*.pem
*.key
db.sqlite3
.aws/
```

Never commit:

```text
AWS credentials
RDS password
Secrets Manager values
.pem files
private keys
django.env
.env
```

---

# 88. Generate a New Django Secret Key

For a new environment:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated value into your environment configuration.

Do not publish the real secret key.

---

# 89. Git Commands

Go to repository root:

```powershell
cd "E:\DevOps\Aws Practice\DevOps-Django-AWS-Project"
```

Initialize:

```bash
git init
```

Check:

```bash
git status
```

Add:

```bash
git add .
```

Commit:

```bash
git commit -m "Initial DevOps Django AWS project"
```

Rename branch:

```bash
git branch -M main
```

Add GitHub remote:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

Push:

```bash
git push -u origin main
```

---

# 90. Update Application Version

When application code changes:

```powershell
docker build --no-cache -t devops-django-app:2.2 .
```

Tag:

```powershell
docker tag `
  devops-django-app:2.2 `
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.2
```

Push:

```powershell
docker push `
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/devops-django-app:2.2
```

Then create a new Launch Template version using:

```text
2.2
```

Do not delete the image version currently used by the Launch Template until the new version has been tested.

---

# 91. AWS Resource Validation Checklist

## VPC

- [ ] VPC created
- [ ] 10.0.0.0/16
- [ ] Public-A
- [ ] Public-B
- [ ] Private-A
- [ ] Private-B
- [ ] Internet Gateway
- [ ] Route tables

## Security Groups

- [ ] alb-sg
- [ ] ec2-sg
- [ ] rds-sg
- [ ] ALB -> EC2 port 80
- [ ] EC2 -> RDS port 5432
- [ ] Internet -> ALB port 80

## RDS

- [ ] PostgreSQL
- [ ] devopsdb
- [ ] Private
- [ ] Port 5432
- [ ] rds-sg
- [ ] Available

## ECR

- [ ] devops-django-app
- [ ] Application image pushed
- [ ] Correct image tag

## EC2

- [ ] Docker
- [ ] Django container
- [ ] Nginx
- [ ] RDS connection

## Target Group

- [ ] devops-django-tg
- [ ] HTTP 80
- [ ] /health/
- [ ] HTTP 200
- [ ] Healthy targets

## ALB

- [ ] devops-django-alb
- [ ] Internet-facing
- [ ] HTTP 80
- [ ] Target Group attached

## Launch Template

- [ ] Correct AMI
- [ ] Correct instance type
- [ ] Correct IAM role
- [ ] Correct Security Group
- [ ] User Data configured

## ASG

- [ ] Desired 2
- [ ] Minimum 2
- [ ] Maximum 4
- [ ] Target Group attached
- [ ] ELB health checks
- [ ] Target tracking

## CloudWatch

- [ ] CPU monitoring
- [ ] Scale-out alarm
- [ ] Scale-in alarm

---

# 92. Final Testing Checklist

Run:

```bash
curl http://localhost:8000/health/
```

Then:

```bash
curl http://localhost/health/
```

Then:

```text
http://YOUR_ALB_DNS/health/
```

Verify:

```text
Django
   ↓
Docker
   ↓
Nginx
   ↓
Target Group
   ↓
ALB
   ↓
Browser
```

Then test:

```text
ASG scale-out
ASG scale-in
```

Finally verify:

```text
RDS remains available
All Target Group instances are healthy
```

---

# 93. Cleanup After Lab

If the project needs to remain available for demonstration, keep:

```text
VPC
RDS
ECR
ALB
Target Group
Launch Template
ASG
CloudWatch alarms
Secrets Manager secret
IAM role
```

Remove only resources that are confirmed unnecessary.

---

# 94. Accidental Aurora Database Cleanup

If an accidental Aurora database/cluster was created during the lab, carefully verify its name before deleting it.

Example:

```text
database-1
```

Do NOT delete:

```text
devops-django-db
```

unless you intentionally want to destroy the project database.

For an unused Aurora cluster:

```text
RDS
→ Databases
→ Select accidental Aurora cluster
→ Actions
→ Delete
```

If you do not need a final snapshot, choose the appropriate option to avoid creating another retained snapshot.

Deletion is irreversible.

---

# 95. Remove Unnecessary Manual EC2 Instances

The final architecture is intended to use the Auto Scaling Group.

Before terminating manually created EC2 instances:

```text
EC2
→ Target Groups
→ devops-django-tg
→ Targets
```

Identify:

```text
ASG-managed instances
```

and:

```text
manually created instances
```

Do not terminate the ASG-managed instances.

If the ASG has:

```text
Minimum: 2
Desired: 2
Maximum: 4
```

it should maintain two instances.

---

# 96. Check Elastic IPs

AWS Console:

```text
EC2
→ Elastic IPs
```

If an Elastic IP is no longer associated with anything:

```text
Release Elastic IP
```

Do not release an IP that is still required.

---

# 97. ECR Cleanup

List images:

```powershell
aws ecr list-images `
  --repository-name devops-django-app `
  --region us-east-1
```

Keep the image version currently referenced by the Launch Template.

For example:

```text
2.1
```

Do not delete the active version.

Old unused versions can be removed after verification.

---

# 98. Final Project Result

The final system provides:

```text
Dockerized Django application
        |
        v
Amazon ECR
        |
        v
Launch Template
        |
        v
Auto Scaling Group
        |
        +-------------------+
        |                   |
        v                   v
     EC2 #1              EC2 #2
        |                   |
      Nginx               Nginx
        |                   |
      Docker              Docker
        |                   |
      Django              Django
        \                   /
         \                 /
          +----- RDS -----+
             PostgreSQL
```

Public traffic:

```text
Internet
   |
   v
ALB :80
   |
   v
Target Group :80
   |
   v
Nginx :80
   |
   v
Django :8000
   |
   v
RDS PostgreSQL :5432
```

---

# 99. Complete Build Order From Scratch

If rebuilding this project from zero, follow this exact order:

```text
1. Install prerequisites
2. Configure AWS CLI
3. Create Git repository
4. Create Django project
5. Create Django health endpoint
6. Create requirements.txt
7. Create Dockerfile
8. Build Docker image
9. Test Docker locally
10. Create ECR repository
11. Push Docker image to ECR
12. Create VPC
13. Create public subnets
14. Create private subnets
15. Create Internet Gateway
16. Configure route tables
17. Create NAT Gateway if required
18. Create ALB security group
19. Create EC2 security group
20. Create RDS security group
21. Create RDS subnet group
22. Create PostgreSQL RDS
23. Test RDS
24. Create Secrets Manager secret
25. Create EC2 IAM role
26. Create initial EC2
27. Install Docker
28. Pull ECR image
29. Configure database environment
30. Run Django migrations
31. Start Django container
32. Install Nginx
33. Configure Nginx
34. Test Nginx → Django
35. Create Target Group
36. Register EC2 targets
37. Configure health check
38. Create ALB
39. Test ALB
40. Create Launch Template
41. Add User Data
42. Create Auto Scaling Group
43. Set desired = 2
44. Set minimum = 2
45. Set maximum = 4
46. Attach Target Group
47. Enable ELB health checks
48. Create target tracking policy
49. Verify ASG instances
50. Verify Target Group health
51. Verify CloudWatch alarms
52. Run load test
53. Demonstrate scale-out
54. Verify automatically created EC2
55. Stop load test
56. Demonstrate scale-in
57. Perform final validation
58. Remove unnecessary AWS resources
59. Push documentation to GitHub
```

---

# 100. Important Rules

Never commit:

```text
AWS Access Key
AWS Secret Key
RDS Password
Secrets Manager password
.pem files
.env files
django.env
```

Never expose RDS publicly just to make connectivity easier.

Never open:

```text
5432
```

to:

```text
0.0.0.0/0
```

The correct flow is:

```text
EC2 → RDS
```

not:

```text
Internet → RDS
```

Do not manually configure every new ASG instance.

The purpose of the Launch Template User Data is automatic configuration.

---

# 101. Final Interview Explanation

If asked to explain this project:

> I deployed a Dockerized Django application on AWS using an Application Load Balancer and Auto Scaling Group. The Django application runs inside Docker behind Nginx. The ALB distributes HTTP traffic to healthy EC2 instances through a Target Group. PostgreSQL is hosted separately in Amazon RDS private subnets. Database credentials are stored in AWS Secrets Manager and accessed by EC2 through an IAM role. The Launch Template contains User Data that automatically installs Docker and Nginx, authenticates with ECR, retrieves the database secret, runs migrations, starts the Django container, configures Nginx and makes the instance ready for the Target Group. The ASG maintains a minimum of two instances and can scale up to four based on CloudWatch CPU utilization. I also performed load testing to demonstrate scale-out and scale-in.

---

# 102. Final Architecture

```text
                          INTERNET
                              |
                              |
                           HTTP :80
                              |
                              v
                 +-------------------------+
                 | Application Load        |
                 | Balancer                |
                 | devops-django-alb       |
                 +------------+------------+
                              |
                              |
                         Target Group
                       devops-django-tg
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
          EC2 / ASG       EC2 / ASG       EC2 / ASG
              |               |               |
          Nginx :80       Nginx :80       Nginx :80
              |               |               |
          Docker          Docker          Docker
              |               |               |
          Django          Django          Django
              |               |               |
              +---------------+---------------+
                              |
                              |
                         TCP :5432
                              |
                              v
                 +-------------------------+
                 | PostgreSQL RDS          |
                 | devops-django-db        |
                 | Private Subnet          |
                 +-------------------------+
```

Supporting AWS Services:

```text
       +------------------+
       | Amazon ECR       |
       | Docker Image     |
       +------------------+

       +------------------+
       | Secrets Manager  |
       | DB Credentials   |
       +------------------+

       +------------------+
       | IAM Role         |
       | ECR + Secret     |
       +------------------+

       +------------------+
       | CloudWatch       |
       | CPU / Scaling    |
       +------------------+
```

# END

A few important points for the GitHub version:

1. **Replace every `YOUR_ACCOUNT_ID`, `YOUR_RDS_ENDPOINT`, `YOUR_ALB_DNS`, `YOUR_KEY_PAIR`, and `YOUR_USERNAME` placeholder.**
2. **Do not replace the password placeholders with the real password in the README.**
3. Keep `devops-django/rds` in Secrets Manager, but never put its actual secret contents into GitHub.
4. The Launch Template User Data is the key part of the lab: it demonstrates that a third EC2 instance can be created and configured automatically rather than manually. This is specifically required by the practical paper.
5. The ASG should remain `min=2`, `max=4`, with the Target Group attached, matching the practical requirements.
6. The RDS database remains a separate database tier and should be private, with PostgreSQL access restricted to the EC2 security group.
7. The Nginx → Django relationship is `80 → 8000`, while the ALB → Target Group relationship is `80 → 80`.

This version is intentionally written as a **rebuild manual**, rather than a short portfolio README, so someone cloning the GitHub repository can follow the project from an empty AWS environment through Docker, RDS, ALB, ASG, User Data, CloudWatch and scaling.
