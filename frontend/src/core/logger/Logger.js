/**
 * Log levels in order of severity.
 */
export const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  SILENT: 4,
};

const LEVEL_LABEL = {
  [LogLevel.DEBUG]: 'DEBUG',
  [LogLevel.INFO]: 'INFO',
  [LogLevel.WARN]: 'WARN',
  [LogLevel.ERROR]: 'ERROR',
};

const LEVEL_COLOR = {
  [LogLevel.DEBUG]: 'color: #6b7280',   // gray
  [LogLevel.INFO]: 'color: #2563eb',    // blue
  [LogLevel.WARN]: 'color: #d97706',    // amber
  [LogLevel.ERROR]: 'color: #dc2626',   // red
};

export class Logger {
  /**
   * @param {object} opts
   * @param {string} [opts.namespace]   - prefix like "[Auth]"
   * @param {number} [opts.level]       - minimum level to print
   * @param {boolean} [opts.enabled]    - master on/off switch
   */
  constructor({ namespace = 'App', level = LogLevel.DEBUG, enabled = true } = {}) {
    this.namespace = namespace;
    this.level = level;
    this.enabled = enabled;
  }

  /** Create a child logger with a new namespace, sharing config. */
  child(namespace) {
    return new Logger({
      namespace: `${this.namespace}:${namespace}`,
      level: this.level,
      enabled: this.enabled,
    });
  }

  setLevel(level) { this.level = level; }
  setEnabled(enabled) { this.enabled = enabled; }

  debug(...args) { this._log(LogLevel.DEBUG, args); }
  info(...args)  { this._log(LogLevel.INFO,  args); }
  warn(...args)  { this._log(LogLevel.WARN,  args); }
  error(...args) { this._log(LogLevel.ERROR, args); }

  /* ---------------- internals ---------------- */

  _log(level, args) {
    if (!this.enabled) return;
    if (level < this.level) return;

    const label = LEVEL_LABEL[level];
    const color = LEVEL_COLOR[level];
    const time = new Date().toISOString().substring(11, 23); // HH:MM:SS.mmm
    const prefix = `%c[${time}] [${label}] [${this.namespace}]`;

    // Route to the correct console method
    const method =
      level === LogLevel.ERROR ? 'error'
      : level === LogLevel.WARN ? 'warn'
      : level === LogLevel.INFO ? 'info'
      : 'log';

    // eslint-disable-next-line no-console
    console[method](prefix, color, ...args);
  }
}