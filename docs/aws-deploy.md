# Deploying MEK MCP on AWS

This server has two runtime modes:

- `mek-mcp`: local MCP over stdio
- `mek-mcp-http`: remote MCP over HTTP, defaulting to `streamable-http` on `/mcp`

For AWS, build and publish the Docker image first, then run it behind a managed
HTTPS endpoint.

## 1. Local prerequisites

- Docker running locally
- AWS CLI authenticated to the target account
- An AWS Region selected, for example `eu-central-1`

Set shared variables:

```bash
export AWS_REGION=eu-central-1
export ECR_REPO=mek-mcp
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export IMAGE_TAG=$(git rev-parse --short HEAD)
export IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
```

## 2. Build the container

```bash
docker build -t "$ECR_REPO:$IMAGE_TAG" .
```

The container listens on port `8000` and starts:

```bash
mek-mcp-http
```

Important environment variables:

- `MEK_MCP_HOST`: defaults to `0.0.0.0`
- `MEK_MCP_PORT`: defaults to `8000`
- `PORT`: overrides `MEK_MCP_PORT` when the platform injects it
- `MEK_MCP_TRANSPORT`: `streamable-http` by default, or `sse`

## 3. Push the image to ECR

Create the repository once:

```bash
aws ecr create-repository \
  --repository-name "$ECR_REPO" \
  --image-scanning-configuration scanOnPush=true \
  --region "$AWS_REGION"
```

Log Docker in to ECR:

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin \
    "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
```

Tag and push:

```bash
docker tag "$ECR_REPO:$IMAGE_TAG" "$IMAGE_URI"
docker push "$IMAGE_URI"
```

## 4. Run it on AWS

Recommended default: ECS Fargate behind an Application Load Balancer.

Use:

- ECR image: `$IMAGE_URI`
- Container port: `8000`
- Launch type: Fargate
- Target group target type: `ip`
- Load balancer listener: HTTPS for production, HTTP only for a short test
- Health check: TCP if available, otherwise add a small HTTP health endpoint
  before using an HTTP health check path

If AWS App Runner is available in your account, it is the shortest path:

- Source: ECR image
- Port: `8000`
- Health check protocol: TCP
- Environment: `MEK_MCP_TRANSPORT=streamable-http`

AWS now documents that App Runner is no longer open to new customers, so ECS
Fargate is the safer long-term path for a new AWS account.

## 5. Connect an MCP client

The remote MCP endpoint is:

```text
https://<your-domain-or-load-balancer>/mcp
```

Configure the MCP client to use HTTP/streamable HTTP transport with that URL.
Keep the local `mek` stdio configuration until the remote URL is verified.

Do not leave the service publicly reachable for broad use without an access
control layer. For a first private test, restrict the load balancer security
group to trusted source IPs. For a durable setup, put authentication in front of
the service or keep it private behind a controlled network path.
