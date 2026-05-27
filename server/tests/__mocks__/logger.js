// Logger mock for testing
const noop = () => {};
const logger = (tag) => ({
  debug: noop,
  info: noop,
  warn: noop,
  error: noop,
});
logger.debug = noop;
logger.info = noop;
logger.warn = noop;
logger.error = noop;
module.exports = logger;
