# API 文档（自动生成）

> 生成时间: 2026-05-25T06:41:18.051825

## admin\analysis.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /ranking | 消费排行（手机号脱敏，支持分页） |
| GET | /trend | 销售趋势（日期范围查询代替 DATE() 函数，支持索引） |

## admin\coupons.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |
| POST | / |  |
| PUT | /:id |  |

## admin\dashboard.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |

## admin\deposits.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |
| PUT | /:id/return | 退还押金 — 原子操作防竞态 |

## admin\feedback.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |

## admin\login.js

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | / |  |

## admin\orders.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 订单列表 |
| PUT | /:id/deliver |  |
| PUT | /:id/complete |  |
| POST | /:id/assign |  |

## admin\products.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |
| POST | / |  |
| PUT | /:id |  |

## admin\stations.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |
| POST | / |  |
| PUT | /:id |  |
| PUT | /:id/toggle |  |

## admin\users.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |

## admin\warnings.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / |  |
| PUT | /:id/resolve |  |

## auth.js

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /wx-login | 微信登录 - 生产环境调用微信接口，开发环境用 mock |
| POST | /register | 实名注册（事务保护，防止竞态条件） |
| GET | /profile | 获取用户信息（敏感字段脱敏） |

## coupons.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /available | 可领取的优惠券 |
| POST | /:couponId/receive | 领取优惠券（事务保护，防止竞态重复领取） |
| GET | /my | 我的优惠券 |

## feedback.js

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | / |  |

## orders.js

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | / | 创建订单（事务保护，避免数据不一致） |
| GET | / | 订单列表（支持分页） |
| GET | /detail/:orderNo | 订单详情（通过 order_no） |

## products.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 商品列表（公开接口，无需登录） |
| GET | /:id | 商品详情（参数校验：id 必须为正整数） |

## sms.js

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /send |  |
| POST | /verify |  |

## stations.js

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 获取所有启用的配送站（小程序端用，公开接口） |

