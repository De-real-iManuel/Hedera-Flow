# CI/CD Setup Guide

This document explains the GitHub Actions CI/CD pipeline for Hedera Flow MVP.

## Overview

The project uses GitHub Actions for continuous integration and deployment with the following workflows:

1. **Frontend CI** - Lints and builds Next.js application
2. **Backend CI** - Tests and lints FastAPI backend
3. **Deploy Preview** - Deploys PR previews to Vercel
4. **Deploy Production** - Deploys to production (Vercel + Supabase)
5. **Security Scan** - Runs security audits and CodeQL analysis

## Workflows

### 1. Frontend CI (`frontend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Only when frontend files change

**Jobs:**
- Install dependencies
- Run ESLint
- Type-check with TypeScript
- Build Next.js application
- Upload build artifacts

**Requirements:**
- Node.js 20.x
- No secrets required for basic CI

### 2. Backend CI (`backend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Only when backend files change

**Jobs:**
- Setup PostgreSQL and Redis services
- Install Python dependencies
- Run code formatters (Black, isort)
- Run linter (Flake8)
- Run pytest test suite

**Requirements:**
- Python 3.11 and 3.12
- PostgreSQL 16
- Redis 7

### 3. Deploy Preview (`deploy-preview.yml`)

**Triggers:**
- Pull requests to `main` branch

**Jobs:**
- Deploy preview to Vercel
- Comment PR with preview URL

**Required Secrets:**
- `VERCEL_TOKEN` - Vercel authentication token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID

### 4. Deploy Production (`deploy-production.yml`)

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**Jobs:**
- Deploy frontend to Vercel production
- Deploy backend migrations to Supabase

**Required Secrets:**
- `VERCEL_TOKEN` - Vercel authentication token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID
- `SUPABASE_DB_URL` - Supabase database connection URL
- `SUPABASE_ACCESS_TOKEN` - Supabase API token

### 5. Security Scan (`security-scan.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Weekly schedule (Mondays at 9 AM UTC)

**Jobs:**
- NPM security audit
- Python safety check
- CodeQL security analysis

**Requirements:**
- No secrets required
- CodeQL requires `security-events: write` permission

## Setup Instructions

### 1. Initial Repository Setup

```bash
# Initialize git repository (if not already done)
git init

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/hedera-flow-mvp.git

# Create main and develop branches
git checkout -b main
git push -u origin main

git checkout -b develop
git push -u origin develop
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

#### Vercel Secrets (Required for deployment)

1. **VERCEL_TOKEN**
   - Go to https://vercel.com/account/tokens
   - Create a new token
   - Copy and add to GitHub secrets

2. **VERCEL_ORG_ID** and **VERCEL_PROJECT_ID**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Login and link project
   vercel login
   vercel link
   
   # Get IDs from .vercel/project.json
   cat .vercel/project.json
   ```

#### Supabase Secrets (Required for backend deployment)

3. **SUPABASE_DB_URL**
   - Format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`
   - Get from Supabase dashboard → Settings → Database

4. **SUPABASE_ACCESS_TOKEN**
   - Go to https://app.supabase.com/account/tokens
   - Generate new token
   - Copy and add to GitHub secrets

#### Optional Secrets

5. **NEXT_PUBLIC_API_URL** (optional)
   - Your backend API URL
   - Default: `http://localhost:8000`

### 3. Branch Protection Rules

Configure branch protection for `main`:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Select: `Lint and Build Frontend`
     - Select: `Test and Lint Backend`
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings

### 4. Enable GitHub Actions

1. Go to Settings → Actions → General
2. Set "Actions permissions" to "Allow all actions and reusable workflows"
3. Set "Workflow permissions" to "Read and write permissions"
4. Enable "Allow GitHub Actions to create and approve pull requests"

### 5. Test the Workflows

```bash
# Create a test branch
git checkout -b test/ci-setup

# Make a small change
echo "# CI/CD Test" >> README.md

# Commit and push
git add .
git commit -m "test: verify CI/CD workflows"
git push origin test/ci-setup

# Create a pull request on GitHub
# Verify that workflows run successfully
```

## Workflow Status Badges

Add these badges to your README.md:

```markdown
![Frontend CI](https://github.com/YOUR_USERNAME/hedera-flow-mvp/workflows/Frontend%20CI/badge.svg)
![Backend CI](https://github.com/YOUR_USERNAME/hedera-flow-mvp/workflows/Backend%20CI/badge.svg)
![Security Scan](https://github.com/YOUR_USERNAME/hedera-flow-mvp/workflows/Security%20Scan/badge.svg)
```

## Troubleshooting

### Frontend CI Fails

**Issue:** ESLint errors
```bash
# Fix locally
npm run lint -- --fix
git add .
git commit -m "fix: resolve linting issues"
```

**Issue:** TypeScript errors
```bash
# Check types locally
npx tsc --noEmit
# Fix errors and commit
```

### Backend CI Fails

**Issue:** Test failures
```bash
# Run tests locally
cd backend
pytest tests/ -v
# Fix failing tests and commit
```

**Issue:** Linting errors
```bash
# Format code
black .
isort .
git add .
git commit -m "style: format code"
```

### Deployment Fails

**Issue:** Missing secrets
- Verify all required secrets are configured in GitHub
- Check secret names match exactly (case-sensitive)

**Issue:** Vercel deployment fails
```bash
# Test deployment locally
vercel --prod
```

**Issue:** Supabase migration fails
- Verify database URL is correct
- Check migration files are valid SQL
- Test migrations locally first

## Best Practices

1. **Always create feature branches**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Keep commits atomic and descriptive**
   ```bash
   git commit -m "feat: add user authentication"
   git commit -m "fix: resolve CORS issue"
   git commit -m "test: add billing calculation tests"
   ```

3. **Run tests locally before pushing**
   ```bash
   # Frontend
   npm run lint
   npm run build
   
   # Backend
   cd backend
   pytest tests/
   ```

4. **Review CI logs for failures**
   - Click on failed workflow in GitHub Actions tab
   - Expand failed step to see error details
   - Fix issues and push again

5. **Use draft PRs for work in progress**
   - Create PR as draft while developing
   - Mark as "Ready for review" when CI passes

## Maintenance

### Update Dependencies

```bash
# Frontend
npm update
npm audit fix

# Backend
cd backend
pip list --outdated
pip install --upgrade [package-name]
```

### Update Workflow Actions

Periodically update GitHub Actions to latest versions:
- `actions/checkout@v4` → Check for v5
- `actions/setup-node@v4` → Check for v5
- `actions/setup-python@v5` → Check for v6

## Support

For issues with CI/CD:
1. Check workflow logs in GitHub Actions tab
2. Review this documentation
3. Check GitHub Actions documentation: https://docs.github.com/actions
4. Check Vercel documentation: https://vercel.com/docs
5. Check Supabase documentation: https://supabase.com/docs

---

**Last Updated:** February 19, 2026
**Maintained By:** Hedera Flow Team
