// Mock for uuid v14 (ESM-only, Jest needs CJS)
const uuidv4 = () => '00000000-0000-0000-0000-000000000000';
module.exports = { v4: uuidv4 };
module.exports.v4 = uuidv4;
module.exports.default = { v4: uuidv4 };
