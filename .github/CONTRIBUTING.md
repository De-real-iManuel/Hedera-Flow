# Contributing to Hedera Flow MVP

Thank you for your interest in contributing to Hedera Flow! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Commit Guidelines](#commit-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Testing Guidelines](#testing-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- Python 3.11 or higher
- Docker and Docker Compose
- Git
- Hedera testnet account

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hedera-flow-mvp.git
   cd hedera-flow-mvp
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy example files
   cp .env.local.example .env.local
   cp backend/.env.example backend/.env
   
   # Edit with your values
   ```

5. **Start development services**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d
   
   # Start frontend
   npm run dev
   
   # Start backend (in another terminal)
   cd backend
   uvicorn main:app --reload
   ```

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

- `feature/` - New features (e.g., `feature/user-authentication`)
- `fix/` - Bug fixes (e.g., `fix/ocr-confidence-calculation`)
- `refactor/` - Code refactoring (e.g., `refactor/billing-engine`)
- `test/` - Test additions or updates (e.g., `test/payment-flow`)
- `docs/` - Documentation updates (e.g., `docs/api-specification`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### Workflow Steps

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Frontend
   npm run lint
   npm run build
   
   # Backend
   cd backend
   pytest tests/
   black .
   isort .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add user authentication"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch
   - Fill out the PR template completely
   - Link related issues
   - Wait for CI checks to pass
   - Request review from maintainers

## Coding Standards

### Frontend (TypeScript/React)

- Use TypeScript for all new code
- Follow React best practices and hooks guidelines
- Use functional components over class components
- Prefer named exports over default exports
- Use Tailwind CSS for styling (no inline styles)
- Keep components small and focused (< 200 lines)
- Use meaningful variable and function names

**Example:**
```typescript
// Good
export function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading } = useUser(userId);
  
  if (isLoading) return <Spinner />;
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold">{data.name}</h2>
    </div>
  );
}

// Bad
export default function Component(props: any) {
  const d = props.data;
  return <div style={{ background: 'white' }}>{d.name}</div>;
}
```

### Backend (Python/FastAPI)

- Follow PEP 8 style guide
- Use type hints for all function parameters and returns
- Use Pydantic models for request/response validation
- Keep functions small and focused (< 50 lines)
- Use async/await for I/O operations
- Add docstrings to all public functions

**Example:**
```python
# Good
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str
    country_code: str

async def create_user(user_data: UserCreate) -> User:
    """
    Create a new user account.
    
    Args:
        user_data: User registration data
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If email already exists
    """
    # Implementation
    pass

# Bad
def create_user(data):
    # No type hints, no docstring
    pass
```

### Code Formatting

**Frontend:**
- ESLint for linting
- Prettier for formatting (if configured)
- 2 spaces for indentation

**Backend:**
- Black for code formatting
- isort for import sorting
- Flake8 for linting
- 4 spaces for indentation

Run formatters before committing:
```bash
# Frontend
npm run lint -- --fix

# Backend
cd backend
black .
isort .
```

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, no logic change)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements
- `ci` - CI/CD changes

### Examples

```bash
# Feature
git commit -m "feat(auth): add HashPack wallet integration"

# Bug fix
git commit -m "fix(ocr): correct confidence score calculation"

# Documentation
git commit -m "docs(api): update payment endpoint documentation"

# Breaking change
git commit -m "feat(billing)!: change tariff calculation method

BREAKING CHANGE: Tariff calculation now uses time-of-use rates"
```

## Pull Request Process

1. **Ensure CI passes**
   - All tests must pass
   - No linting errors
   - Build succeeds

2. **Update documentation**
   - Update README if needed
   - Add/update API documentation
   - Update CHANGELOG.md

3. **Request review**
   - Assign at least one reviewer
   - Address review comments promptly
   - Keep PR focused (< 500 lines changed)

4. **Merge requirements**
   - ✅ CI checks pass
   - ✅ At least one approval
   - ✅ No merge conflicts
   - ✅ Branch is up to date with main

5. **After merge**
   - Delete your feature branch
   - Close related issues
   - Update project board

## Testing Guidelines

### Frontend Tests

- Write tests for all components
- Test user interactions
- Test edge cases and error states
- Use React Testing Library

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Backend Tests

- Write tests for all endpoints
- Test business logic thoroughly
- Test error handling
- Use pytest fixtures

```python
import pytest
from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "country_code": "ES"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()
    assert response.json()["user"]["email"] == "test@example.com"
```

### Test Coverage

- Aim for > 80% code coverage
- Focus on critical paths first
- Don't test third-party libraries
- Test business logic, not implementation details

## Questions?

- Open an issue for questions
- Join our Discord community
- Check existing documentation
- Review closed PRs for examples

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Hedera Flow! 🚀
