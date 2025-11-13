# Deploying MCP Server to Railway

This guide explains how to deploy the Biological APIs MCP Server to Railway.

## Prerequisites

- A Railway account ([sign up here](https://railway.app/))
- Your code pushed to a GitHub repository
- Railway CLI (optional, for CLI deployment)

## Quick Deploy (GitHub)

### Step 1: Push to GitHub

Ensure your code is in a GitHub repository:

```bash
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

### Step 2: Deploy on Railway

1. Go to [Railway Dashboard](https://railway.app/)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect the `railway.json` configuration

### Step 3: Generate Public Domain

1. Go to your service's **Settings** tab
2. Navigate to **Networking** section
3. Click **"Generate Domain"**
4. Your MCP server will be available at: `https://your-app-name.up.railway.app`

## Configuration Files

### `railway.json`

This file tells Railway how to build and run your app:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn medical_mcps.http_server:app --host 0.0.0.0 --port $PORT"
  }
}
```

### `requirements.txt`

Generated from `pyproject.toml` dependencies. Railway uses this to install Python packages.

**Note:** To regenerate `requirements.txt` after adding dependencies:

```bash
uv pip compile pyproject.toml -o requirements.txt --no-header --no-annotate
```

## Environment Variables

The server automatically reads Railway's `PORT` environment variable. No configuration needed!

For local development, you can still use `MCP_PORT`:

```bash
MCP_PORT=8000 uv run mcp-server
```

## MCP Endpoints

Once deployed, your MCP server will be available at:

- **Reactome**: `https://your-app.up.railway.app/tools/reactome/mcp`
- **KEGG**: `https://your-app.up.railway.app/tools/kegg/mcp`
- **UniProt**: `https://your-app.up.railway.app/tools/uniprot/mcp`
- **OMIM**: `https://your-app.up.railway.app/tools/omim/mcp`
- **GWAS Catalog**: `https://your-app.up.railway.app/tools/gwas/mcp`
- **Pathway Commons**: `https://your-app.up.railway.app/tools/pathwaycommons/mcp`
- **ChEMBL**: `https://your-app.up.railway.app/tools/chembl/mcp`
- **ClinicalTrials.gov**: `https://your-app.up.railway.app/tools/ctg/mcp`

## Deploy via CLI (Alternative)

### Install Railway CLI

```bash
npm install -g @railway/cli
```

### Authenticate

```bash
railway login
```

### Deploy

```bash
# Initialize Railway project (first time only)
railway init

# Deploy
railway up
```

## Monitoring

- **Logs**: View real-time logs in Railway dashboard
- **Metrics**: Check CPU, memory, and network usage
- **Deployments**: See deployment history and rollback if needed

## Troubleshooting

### Build Fails

- Check that `requirements.txt` includes all dependencies
- Verify Python version compatibility (requires Python 3.12+)

### Server Won't Start

- Check logs in Railway dashboard
- Verify `startCommand` in `railway.json` is correct
- Ensure port is set to `$PORT` (Railway's environment variable)

### MCP Client Can't Connect

- Verify the public domain is generated in Networking settings
- Check that the URL uses `https://` (Railway provides HTTPS automatically)
- Test endpoints directly: `curl https://your-app.up.railway.app/tools/reactome/mcp`

## Cost

- **Free Tier**: $5 credit/month (usually enough for low traffic)
- **Pay-as-you-go**: ~$0.000463/GB-hour RAM after free tier
- **Typical Cost**: $5-10/month for a small MCP server

## Auto-Deploy

Railway automatically deploys when you push to your GitHub repository's main branch.

To disable auto-deploy or change the branch:

1. Go to service **Settings**
2. Navigate to **Deployments**
3. Configure GitHub integration

## Next Steps

- Set up custom domain (optional)
- Configure environment variables if needed
- Set up monitoring alerts
- Review Railway's [FastAPI deployment guide](https://docs.railway.app/guides/fastapi)
