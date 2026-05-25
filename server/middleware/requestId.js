const { v4: uuidv4 } = require('uuid')

function requestId(req, res, next) {
  req.id = req.headers['x-request-id'] || uuidv4().slice(0, 8)
  res.setHeader('X-Request-Id', req.id)
  next()
}

module.exports = requestId
