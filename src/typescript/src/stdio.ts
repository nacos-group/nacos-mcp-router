#!/usr/bin/env node

import { Router, RouterConfig } from './router';
import { logger } from './logger';
import { config } from './config';

// Global error handlers to prevent process crashes
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

async function main() {
    try {
      const router = new Router(config as RouterConfig);
      // router.start();
      logger.info(`nacos mcp router start`);
      await router.start();
      logger.info('Nacos MCP Router started successfully');
    } catch (error) {
      logger.error('Failed to start Nacos MCP Router:', error);
      process.exit(1);
    }
  }
  
  main();