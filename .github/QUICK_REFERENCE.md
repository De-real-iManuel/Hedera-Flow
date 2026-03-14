# CI/CD Quick Reference

Quick commands and tips for working with the CI/CD pipeline.

## Common Commands

### Local Testing (Before Push)

```bash
# Frontend checks
npm run lint              # Run ESLint
npm run lint -- --fix     # Auto-fix linting issues
npx tsc --noEmit         # Type check
npm run build            # Build production bundle

# Backend checks
cd backend
black .                  # Format code
isort .                  # Sort imports
flake8 .                 # Lint code
pytest tests/ -v         # Run tests
pytest tests/ --cov      # Run tests with coverage
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Stage and commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/your-feature

# Update branch with main
git checkout main
git pull origin main
git checkout feature/your-feature
git rebase main
```

### Viewing CI/CD Status

```bash
# View workflow runs
gh run list

# View specific workflow
gh run view <run-id>

# Watch workflow in real-time
gh run watch

# Re-run failed workflow
gh run rerun <run-id>
```

## Workflow Triggers

| Workflow | Trigger | When |
|----------|---------|------|
| Frontend CI | Push/PR to main/develop | Frontend files change |
| Backend CI | Push/PR to main/develop | Backend files change |
| Deploy Preview | PR to main | Any PR opened/updated |
| Deploy Production | Push to main | Code merged to main |
| Security Scan | Push/PR/Schedule | Weekly + on changes |

## Fixing Common Issues

### ESLint Errors

```bash
# Auto-fix most issues
npm run lint -- --fix

# Check specific file
npx eslint app/page.tsx

# Disable rule for specific line (use sparingly)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
```

### TypeScript Errors

```bash
# Check all files
npx tsc --noEmit

# Check specific file
npx tsc --noEmit app/page.tsx

# Generate declaration files
npx tsc --declaration
```

### Python Formatting

```bash
# Format all files
black .

# Format specific file
black app/main.py

# Check without modifying
black --check .

# Sort imports
isort .
```

### Test Failures

```bash
# Run specific test
pytest tests/test_auth.py::test_login

# Run with verbose output
pytest tests/ -vv

# Run with print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf
```

## GitHub Secrets Required

### Vercel Deployment
- `VERCEL_TOKEN` - Get from https://vercel.com/account/tokens
- `VERCEL_ORG_ID` - From `.vercel/project.json`
- `VERCEL_PROJECT_ID` - From `.vercel/project.json`

### Supabase Deployment
- `SUPABASE_DB_URL` - Database connection string
- `SUPABASE_ACCESS_TOKEN` - API token from Supabase

### Optional
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Branch Protection Rules

Recommended settings for `main` branch:

- ✅ Require pull request before merging
- ✅ Require approvals: 1
- ✅ Require status checks to pass:
  - `Lint and Build Frontend`
  - `Test and Lint Backend`
- ✅ Require branches to be up to date
- ✅ Require conversation resolution before merging
- ❌ Allow force pushes: Never
- ❌ Allow deletions: Never

## Commit Message Examples

```bash
# Features
git commit -m "feat(auth): add HashPack wallet integration"
git commit -m "feat(ocr): implement Tesseract.js client-side OCR"

# Bug fixes
git commit -m "fix(billing): correct tax calculation for Spain"
git commit -m "fix(ui): resolve mobile responsive issues"

# Documentation
git commit -m "docs(api): update payment endpoint documentation"
git commit -m "docs(readme): add CI/CD setup instructions"

# Refactoring
git commit -m "refactor(hedera): extract HCS logging to service"
git commit -m "refactor(db): optimize query performance"

# Tests
git commit -m "test(auth): add unit tests for JWT validation"
git commit -m "test(billing): add integration tests for payment flow"

# Chores
git commit -m "chore(deps): update Next.js to 14.2.18"
git commit -m "chore(ci): add security scan workflow"
```

## Debugging CI Failures

### View Logs

1. Go to GitHub Actions tab
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step to see error

### Common Fixes

**Build fails with "Module not found"**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Tests fail locally but pass in CI**
```bash
# Check environment variables
cat .env.local

# Use same Node/Python version as CI
nvm use 20  # Node
pyenv local 3.11  # Python
```

**Deployment fails**
```bash
# Verify secrets are set
gh secret list

# Test Vercel deployment locally
vercel --prod
```

## Performance Tips

### Speed Up CI

- Use `npm ci` instead of `npm install` (faster, more reliable)
- Cache dependencies (already configured)
- Run only affected tests
- Use matrix builds for parallel testing

### Reduce Build Time

```bash
# Frontend
npm run build -- --profile  # Analyze build

# Backend
pytest tests/ -n auto  # Parallel test execution
```

## Useful Links

- [GitHub Actions Docs](https://docs.github.com/actions)
- [Vercel CLI Docs](https://vercel.com/docs/cli)
- [Supabase CLI Docs](https://supabase.com/docs/guides/cli)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Getting Help

1. Check workflow logs in GitHub Actions
2. Review [CICD_SETUP.md](.github/CICD_SETUP.md)
3. Search existing issues
4. Ask in team Discord/Slack
5. Create new issue with `ci` label

---

**Last Updated:** February 19, 2026
