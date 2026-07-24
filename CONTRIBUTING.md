# Contributing Guidelines

Thank you for contributing to JyotishAI. Follow these standards to ensure consistent code quality and project structure.

## Development Setup

1. Fork and clone repository:
```bash
git clone https://github.com/your-username/JyotishAi.git
cd JyotishAi
```

2. Configure Python virtual environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements/base.txt
```

3. Install Node.js dependencies:
```bash
cd ../frontend
npm install
```

4. Verify local test execution:
```bash
# Backend pytest
cd ../backend
pytest

# Frontend TypeScript validation
cd ../frontend
npx tsc --noEmit
```

## Branch Naming Conventions

Use lowercase branch names prefixed with the category of change:

- `feat/feature-name` - New features or capabilities.
- `fix/bug-description` - Bug fixes and patches.
- `refactor/component-name` - Code structural improvements without changing functionality.
- `docs/topic-name` - Documentation updates.
- `chore/task-name` - Build scripts, dependencies, or infrastructure updates.

Examples:
- `feat/openrouter-provider-integration`
- `fix/embedding-dimensionality-mismatch`
- `docs/api-endpoint-specifications`

## Commit Message Format

Follow Conventional Commits guidelines:

`<type>(<scope>): <short summary>`

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `refactor`: Refactoring production code
- `test`: Adding or updating unit tests
- `chore`: Maintenance tasks or dependency upgrades

Examples:
```
feat(rag): add support for OpenRouter embedding provider
fix(chat): resolve empty streaming bubble on connection timeout
docs(architecture): add sequence diagram for document ingestion
```

## Pull Request Process

1. Create a branch matching the naming convention.
2. Implement your changes following established coding standards.
3. Verify TypeScript compilation (`npx tsc --noEmit`) and backend test suite execution (`pytest`).
4. Push your branch to GitHub and open a Pull Request targeting `main`.
5. Ensure PR description clearly states:
   - Problem statement or feature motivation.
   - Summary of changes made.
   - Manual and automated verification steps completed.
6. Obtain approval from at least one repository maintainer before merging.

## Coding Standards

### Backend (Python)
- Code formatting: Follow PEP 8 guidelines (4 spaces indentation, 100 character max line length).
- Type Hints: Use explicit type annotations for function arguments and return values.
- Async I/O: Prefer `async/await` syntax for database and HTTP API operations.
- Exception Handling: Raise specific domain exceptions inheriting from `JyotishException`. Never use bare `except:`.

### Frontend (TypeScript / Next.js)
- Framework Conventions: Use Next.js App Router file structure (`app/`).
- Component Rules: Keep client components (`"use client"`) scoped to interactive sections. Use React Server Components where interactive state is unnecessary.
- Type Safety: Do not use `any` types. Define explicit TypeScript interfaces in `types/`.
- Styling: Use Tailwind CSS classes. Avoid arbitrary hardcoded pixel offsets where utility flex/grid layout suffices.

## Testing Guidelines

- Write unit tests for new backend services in `backend/tests/`.
- Verify database queries work with async sessions.
- Ensure mock fixtures are used for external LLM API dependencies during automated test runs.
