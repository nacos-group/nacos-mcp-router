#!/usr/bin/env node

import { Router, RouterConfig } from './router';
import { logger } from './logger';
import { config } from './config';

function formatReason(reason: unknown): string {
  if (reason instanceof Error) {
    const name = reason.name || 'Error';
    const message = reason.message || '';
    const stack = reason.stack ? `\n${reason.stack}` : '';
    // Keep it single-line friendly; stack is on following lines
    return `${name}: ${message}${stack}`;
  }
  try {
    return typeof reason === 'string' ? reason : JSON.stringify(reason);
  } catch {
    return String(reason);
  }
}

// Global error handlers to prevent process crashes
process.on('unhandledRejection', (reason) => {
  const msg = formatReason(reason);
  logger.error(`Unhandled Rejection: ${msg}`);
  setTimeout(() => process.exit(1), 100);
});

process.on('uncaughtException', (error) => {
  const msg = formatReason(error);
  logger.error(`Uncaught Exception: ${msg}`);
  setTimeout(() => process.exit(1), 100);
});

async function main() {
    try {
      const router = new Router(config as RouterConfig);
      // router.start();
      logger.info(`nacos mcp router start`);
      await router.start();
      logger.info('Nacos MCP Router started successfully');
    } catch (error) {
      const msg = formatReason(error);
      logger.error(`Failed to start Nacos MCP Router: ${msg}`);
      setTimeout(() => process.exit(1), 100);
    }
  }
  
  main();