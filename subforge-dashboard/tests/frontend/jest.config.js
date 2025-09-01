const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: '../../frontend/',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/../../frontend/src/components/$1',
    '^@/pages/(.*)$': '<rootDir>/../../frontend/src/pages/$1',
    '^@/lib/(.*)$': '<rootDir>/../../frontend/src/lib/$1',
    '^@/hooks/(.*)$': '<rootDir>/../../frontend/src/hooks/$1',
    '^@/services/(.*)$': '<rootDir>/../../frontend/src/services/$1',
    '^@/app/(.*)$': '<rootDir>/../../frontend/src/app/$1',
  },
  testMatch: [
    '<rootDir>/unit/**/*.test.{js,jsx,ts,tsx}',
    '<rootDir>/integration/**/*.test.{js,jsx,ts,tsx}',
  ],
  collectCoverageFrom: [
    '../../frontend/src/**/*.{js,jsx,ts,tsx}',
    '!../../frontend/src/**/*.d.ts',
    '!../../frontend/src/**/layout.tsx',
    '!../../frontend/src/**/loading.tsx',
    '!../../frontend/src/**/not-found.tsx',
    '!../../frontend/src/**/error.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx'],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  testEnvironmentOptions: {
    url: 'http://localhost:3001',
  },
  setupFiles: ['<rootDir>/jest.polyfills.js'],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)