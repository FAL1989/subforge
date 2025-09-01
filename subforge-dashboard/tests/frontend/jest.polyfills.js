// Polyfills for Jest environment

// Mock for fetch API
import 'whatwg-fetch'

// Mock for TextEncoder/TextDecoder
const { TextEncoder, TextDecoder } = require('util')
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock for crypto API (for UUID generation in tests)
const crypto = require('crypto')
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => crypto.randomUUID(),
    getRandomValues: (array) => crypto.getRandomValues(array),
    subtle: crypto.webcrypto?.subtle,
  },
})

// Mock for URL API
const { URL, URLSearchParams } = require('url')
global.URL = URL
global.URLSearchParams = URLSearchParams

// Mock for performance API
global.performance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByName: jest.fn(() => []),
  getEntriesByType: jest.fn(() => []),
}