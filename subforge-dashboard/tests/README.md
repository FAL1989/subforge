# SubForge Dashboard Test Suite

Comprehensive testing infrastructure for the SubForge Dashboard application, covering backend APIs, frontend components, integration scenarios, and end-to-end user workflows.

## Test Architecture

```
tests/
├── backend/                 # Backend API tests (Python/pytest)
│   ├── unit/               # Unit tests for models, schemas, services
│   ├── integration/        # Database and WebSocket integration tests
│   ├── performance/        # Load and performance tests
│   └── security/           # Security and validation tests
├── frontend/               # Frontend component tests (Jest/RTL)
│   ├── unit/              # Component unit tests
│   ├── integration/       # API integration tests
│   └── e2e/               # End-to-end user workflow tests
├── integration/            # Full-stack integration tests
├── e2e/                   # Playwright end-to-end tests
├── fixtures/              # Test data and utilities
└── utils/                 # Test utilities and helpers
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Backend dependencies: `pip install -r backend/requirements.txt`
- Frontend dependencies: `npm install` (in frontend directory)

### Running Tests

#### All Tests
```bash
python tests/run_tests.py --all
```

#### Specific Test Suites
```bash
# Backend tests only
python tests/run_tests.py --backend

# Frontend tests only  
python tests/run_tests.py --frontend

# Integration tests
python tests/run_tests.py --integration

# End-to-end tests
python tests/run_tests.py --e2e
```

#### With Coverage
```bash
python tests/run_tests.py --all --coverage
```

#### Individual Test Commands
```bash
# Backend (from tests/ directory)
pytest backend/ -v

# Frontend (from frontend/ directory)
npm test

# E2E (from tests/e2e/ directory)
npx playwright test
```

## Test Categories

### 1. Backend Tests (Python/pytest)

#### Unit Tests
- **Models**: SQLAlchemy model validation, relationships, methods
- **API Endpoints**: FastAPI route testing with mocked dependencies
- **Schemas**: Pydantic schema validation and serialization
- **WebSocket**: WebSocket manager functionality and message handling
- **Services**: Business logic and external service integrations

```bash
# Run specific backend test categories
pytest backend/unit/ -m models
pytest backend/unit/ -m api
pytest backend/unit/ -m websocket
```

#### Performance Tests
- **Load Testing**: Concurrent request handling
- **Database Performance**: Query optimization and bulk operations
- **WebSocket Scalability**: Connection limits and message throughput
- **Memory Usage**: Resource consumption monitoring

```bash
pytest backend/performance/ -m performance --maxfail=1
```

#### Security Tests
- **SQL Injection**: Input validation and parameterized queries
- **XSS Protection**: Output sanitization
- **Authentication**: Token validation and session management
- **Rate Limiting**: API abuse prevention
- **Data Leakage**: Error message information disclosure

```bash
pytest backend/security/ -m security
```

### 2. Frontend Tests (Jest/React Testing Library)

#### Component Unit Tests
- **Rendering**: Component rendering with various props
- **User Interactions**: Click, form input, drag-and-drop events
- **State Management**: Component state changes and effects
- **Hooks**: Custom hook behavior and dependencies
- **Error Boundaries**: Error handling and fallback UI

```bash
# Run specific frontend test patterns
npm test -- --testPathPattern=components
npm test -- --testNamePattern="WebSocket"
npm test -- --watchAll=false
```

#### Integration Tests
- **API Communication**: HTTP requests and response handling
- **WebSocket Integration**: Real-time data updates
- **Routing**: Navigation and URL state management
- **Theme Provider**: Theme switching functionality
- **Form Validation**: Complex form workflows

### 3. Integration Tests

Full-stack integration testing covering:
- **API Workflow**: Complete CRUD operations with database persistence
- **WebSocket Communication**: Real-time updates between frontend and backend
- **Database Consistency**: Transaction integrity and cascade operations
- **Authentication Flow**: Login/logout and session management

```bash
pytest integration/ -v --tb=short
```

### 4. End-to-End Tests (Playwright)

Browser-based testing of complete user journeys:
- **Dashboard Navigation**: Multi-page navigation workflows
- **Agent Management**: Create, update, delete agent workflows
- **Task Board**: Drag-and-drop task management
- **Real-time Updates**: WebSocket-driven UI updates
- **Responsive Design**: Mobile and desktop layouts
- **Accessibility**: WCAG compliance and keyboard navigation
- **Cross-browser**: Chrome, Firefox, Safari, Edge compatibility

```bash
# Run E2E tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Run specific browser
npx playwright test --project=chromium

# Run in headed mode (see browser)
npx playwright test --headed
```

## Test Configuration

### Backend Configuration (pytest.ini)
```ini
[tool:pytest]
minversion = 6.0
testpaths = backend
python_files = test_*.py
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Tests that run slowly
addopts = 
    -ra -v
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

### Frontend Configuration (jest.config.js)
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}
```

### E2E Configuration (playwright.config.ts)
```typescript
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
})
```

## Test Data and Fixtures

### Backend Fixtures
- **Agent Fixtures**: Sample agent data, bulk data generation
- **Task Fixtures**: Task workflows, status transitions
- **WebSocket Messages**: Real-time update scenarios
- **Performance Data**: Large datasets for performance testing
- **Security Payloads**: Common attack vectors for security testing

### Frontend Mocks
- **API Responses**: Mocked HTTP responses
- **WebSocket Messages**: Simulated real-time events
- **Router Mocks**: Navigation testing
- **External Services**: Third-party integration mocks

## Coverage Requirements

### Minimum Coverage Thresholds
- **Backend**: 80% line coverage, 70% branch coverage
- **Frontend**: 70% line coverage, 70% branch coverage
- **Critical Paths**: 95% coverage for authentication, payment, data persistence

### Coverage Reports
```bash
# Backend coverage
pytest --cov=app --cov-report=html
# Report in htmlcov/index.html

# Frontend coverage  
npm test -- --coverage
# Report in coverage/lcov-report/index.html

# Combined coverage report
python tests/run_tests.py --all --coverage
```

## Performance Benchmarks

### Backend Performance Targets
- **API Response Time**: < 500ms for 95% of requests
- **Database Queries**: < 100ms for simple queries
- **WebSocket Messages**: < 50ms message processing
- **Concurrent Users**: Support 1000+ concurrent WebSocket connections

### Frontend Performance Targets
- **Page Load Time**: < 2 seconds for initial load
- **Component Rendering**: < 100ms for state updates
- **Bundle Size**: < 1MB initial bundle
- **Memory Usage**: < 50MB heap size for typical usage

## Security Testing

### Automated Security Checks
- **Input Validation**: SQL injection, XSS, command injection
- **Authentication**: Token validation, session security
- **Authorization**: Role-based access control
- **Data Sanitization**: Output encoding and escaping
- **Rate Limiting**: API abuse prevention
- **Error Handling**: Information disclosure prevention

### Security Test Categories
```bash
# Run security-specific tests
pytest backend/security/ -m security
pytest backend/unit/test_api_* -k "security"
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/ --cov=app
      
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --coverage
      
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd tests/e2e && npx playwright install
      - run: python tests/run_tests.py --e2e
```

## Debugging Tests

### Backend Debugging
```bash
# Run tests with pdb debugger
pytest backend/unit/test_api_agents.py::test_create_agent --pdb

# Verbose output
pytest -vv -s backend/

# Run specific test
pytest backend/unit/test_models.py::TestAgentModel::test_agent_creation
```

### Frontend Debugging
```bash
# Debug mode
npm test -- --no-coverage --watchAll=false --verbose

# Run specific test
npm test -- --testNamePattern="AgentStatus"

# Update snapshots
npm test -- --updateSnapshot
```

### E2E Debugging
```bash
# Run with browser visible
npx playwright test --headed

# Debug mode with browser dev tools
npx playwright test --debug

# Generate test report
npx playwright show-report
```

## Test Maintenance

### Adding New Tests
1. **Backend**: Add to appropriate `backend/` subdirectory following pytest conventions
2. **Frontend**: Add `.test.tsx` files alongside components
3. **Integration**: Add to `integration/` directory with full-stack scenarios
4. **E2E**: Add `.spec.ts` files to `e2e/tests/` directory

### Test Data Management
- Use factories for generating test data
- Keep fixtures minimal and focused
- Clean up test data after each test
- Use database transactions for test isolation

### Performance Monitoring
- Monitor test execution time
- Identify slow tests with `--durations=10`
- Use parallel execution for independent tests
- Cache dependencies where possible

## Troubleshooting

### Common Issues

#### Backend Test Issues
```bash
# Database connection issues
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Missing test dependencies
pip install -r backend/requirements.txt

# Port conflicts
pkill -f "uvicorn\|pytest"
```

#### Frontend Test Issues
```bash
# Node modules issues
rm -rf node_modules package-lock.json
npm install

# Jest cache issues
npm test -- --clearCache

# WebSocket connection timeouts
export JEST_TIMEOUT=30000
```

#### E2E Test Issues
```bash
# Browser installation
npx playwright install

# Port conflicts
lsof -ti:3001,8000 | xargs kill -9

# Headless mode issues
npx playwright test --headed --browser=chromium
```

For more detailed troubleshooting, check the individual test logs and the generated test reports in `test-results/`.