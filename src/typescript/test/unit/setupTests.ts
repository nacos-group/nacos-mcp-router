// Setup file for Jest tests
import '@testing-library/jest-dom';

// Mock any global objects or functions needed for testing
global.console = {
  ...console,
  // Override any console methods here if needed
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn(),
} as any;
