import { Logger, LogLevel } from './Logger';

const isProd = import.meta.env.PROD;

export const rootLogger = new Logger({
  namespace: 'App',
  level: isProd ? LogLevel.WARN : LogLevel.DEBUG,
  enabled: true,
});

/**
 * Get a namespaced child logger.
 * @param {string} namespace
 * @returns {Logger}
 */
export function createLogger(namespace) {
  return rootLogger.child(namespace);
}

export { Logger, LogLevel };