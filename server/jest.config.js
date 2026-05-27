// Jest 配置 — 智能测试框架
const path = require('path');

const uuidMock = path.resolve(__dirname, 'tests/__mocks__/uuid.js');
const loggerMock = path.resolve(__dirname, 'tests/__mocks__/logger.js');
const dbMock = path.resolve(__dirname, 'tests/__mocks__/config-db.js');
const authMock = path.resolve(__dirname, 'tests/__mocks__/middleware-auth.js');

module.exports = {
  testEnvironment: 'node',
  testTimeout: 15000,
  verbose: true,
  forceExit: true,
  detectOpenHandles: true,
  setupFiles: ['./tests/setup.js'],
  moduleNameMapper: {
    '^uuid$': uuidMock,
    '^uuidv4$': uuidMock,
    '^(\./|\.\./|\.\./\.\./)utils/logger$': loggerMock,
    '^(\./|\.\./|\.\./\.\./)config/db$': dbMock,
    '^(\./|\.\./|\.\./\.\./)middleware/auth$': authMock,
  },
};
