# Odoo ECS Deployment Guide (EC2 Launch Type)

This guide details how to deploy your Odoo container to AWS Elastic Container Service (ECS) running on EC2 instances.

## 1. Prerequisites
- **AWS CLI** installed and configured (`aws configure`).
- **Docker** installed locally.
- **Aurora PostgreSQL** database running and accessible from your VPC.

## 2. Elastic Container Registry (ECR)
You need a place to store your Docker images.

1.  **Create Repository**:
    ```bash
    aws ecr create-repository --repository-name tdm-teto
    ```
2.  **Login to ECR**:
    ```bash
    aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
    ```
3.  **Build & Tag**:
    ```bash
    # Build the production image (includes code & config)
    docker build -t tdm-teto .
    
    # Tag it
    docker tag tdm-teto:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/tdm-teto:latest
    ```
4.  **Push**:
    ```bash
    docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/tdm-teto:latest
    ```

## 3. ECS Task Definition
Create a `task-def.json` file. This defines how your container runs.

**Important**:
- You must pass the database credentials as Environment Variables.
- Since we baked `odoo.conf` into the image, we just need to override the connection params.

```json
{
  "family": "odoo-task",
  "networkMode": "bridge",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "<aws_account_id>.dkr.ecr.<region>.amazonaws.com/tdm-teto:latest",
      "memory": 1024,
      "cpu": 512,
      "portMappings": [
        {
          "containerPort": 8069,
          "hostPort": 8069,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "HOST", "value": "your-aurora-endpoint" },
        { "name": "USER", "value": "odoo" },
        { "name": "PASSWORD", "value": "your-db-password" },
        { "name": "PORT", "value": "5432" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/odoo-app",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["EC2"],
  "memory": "1024",
  "cpu": "512"
}
```

**Register the Task**:
```bash
aws ecs register-task-definition --cli-input-json file://task-def.json
```

## 4. ECS Cluster & Service (EC2)

1.  **Create Cluster** (if you don't have one):
    *   Go to ECS Console > Clusters > Create Cluster.
    *   Select **EC2 Linux + Networking**.
    *   Choose instance type (e.g., t3.medium).
    *   **Security Group**: Ensure inbound port 8069 is open.

2.  **Create Service**:
    *   Go to Cluster > Services > Create.
    *   **Launch type**: EC2.
    *   **Task Definition**: `odoo-task` (latest revision).
    *   **Service Name**: `odoo-service`.
    *   **Number of tasks**: 1 (or more for scaling, but Odoo scaling requires sticky sessions).

## 5. Updates
To deploy new code:
1.  **Rebuild & Push** image to ECR.
2.  **Update Service**:
    ```bash
    aws ecs update-service --cluster <cluster-name> --service odoo-service --force-new-deployment
    ```
    This forces ECS to pull the latest image and restart the containers.

## 6. Scaling & Autoscaling (Golden Image Strategy)
Yes, using your Docker image as a "Golden Image" is best practice. However, if you enable **Autoscaling** (running more than 1 task), you **MUST** handle Odoo's stateful nature:

1.  **Sessions (Sticky Sessions)**:
    *   Odoo stores user sessions on the disk by default.
    *   If you have 2 containers (A and B), and a user is switched from A to B, they will be logged out.
    *   **Fix**: Enable **Sticky Sessions** (Target Group Stickiness) on your AWS Application Load Balancer (ALB).

2.  **Filestore (Attachments)**:
    *   Odoo stores uploads (PDFs, images) in `/var/lib/odoo`.
    *   If you scale up, new containers won't see files uploaded to the old ones.
    *   **Fix**: Mount an **AWS EFS (Elastic File System)** volume to `/var/lib/odoo` in your Task Definition.

## 7. Migrating from Your Setup (EC2 + EFS for Code)
You mentioned you currently store **Code** and **Filestore** on EFS. When moving to Docker/ECS, you should split this:

| Component | Your Current Setup | Docker/ECS Best Practice |
| :--- | :--- | :--- |
| **Source Code** | On EFS (Shared) | **Baked into Docker Image** (Immutable) |
| **Filestore** | On EFS | **Keep on EFS** (`/var/lib/odoo`) |
| **Updates** | Git pull on EFS | **Push new Image** (Safe Rolling Update) |

**Why bake code into the image?**
*   **Safety**: Storing code on EFS means one bad file edit crashes *all* servers instantly.
*   **Rollback**: With Docker images, if v2 fails, you just tell ECS to switch back to v1.
*   **Performance**: Reading python files from block storage (Image) is faster than network storage (EFS).
