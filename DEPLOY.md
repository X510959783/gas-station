# 园中园燃气系统 — 新服务器部署指南

## 一、购买云服务器

推荐配置：
- **CPU**: 2核以上
- **内存**: 4GB 以上
- **系统**: CentOS 7.x / Ubuntu 20.04+ / Windows Server 2019+
- **带宽**: 3Mbps 以上
- **推荐服务商**: 阿里云 ECS、腾讯云 CVM

---

## 二、服务器环境安装

### 2.1 安装 Node.js (版本 16+)
```bash
# Linux (CentOS)
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Linux (Ubuntu)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2.2 安装 MySQL 8.0
```bash
# Linux
sudo yum install -y mysql-server  # CentOS
sudo apt-get install -y mysql-server  # Ubuntu

# 启动并设置密码
sudo systemctl start mysqld
sudo mysql_secure_installation
```

### 2.3 安装 Nginx（用于反向代理和静态文件服务）
```bash
sudo yum install -y nginx  # CentOS
sudo apt-get install -y nginx  # Ubuntu
```

---

## 三、部署后端服务

### 3.1 上传代码
将 `d:\gas-station\server` 目录完整上传到服务器，例如 `/opt/gas-station/server`

### 3.2 初始化数据库
```bash
mysql -u root -p < /opt/gas-station/server/init.sql
```

### 3.3 修改数据库密码
```bash
cd /opt/gas-station/server
node reset-password.js
```
如需修改管理员密码，编辑 `reset-password.js` 中的 ADMIN_USERNAME 和 NEW_PASSWORD。

### 3.4 配置环境变量
创建 `/opt/gas-station/server/.env`：
```
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=gas_station
JWT_SECRET=your-random-secret-string
PORT=3000
```

### 3.5 安装依赖并启动
```bash
cd /opt/gas-station/server
npm install --production
npm install -g pm2
pm2 start app.js --name gas-server
pm2 save
pm2 startup  # 开机自启
```

---

## 四、部署管理后台前端

### 4.1 修改 API 地址
编辑 `d:\gas-station\admin\vite.config.js`，修改 proxy 为生产地址：
```js
server: {
  port: 5173,
  proxy: { '/api': 'http://localhost:3000' }  // 后端地址
}
```

编辑 `d:\gas-station\admin\src\api\index.js`，修改 axios baseURL：
```js
const api = axios.create({ baseURL: '/api' })  // Nginx 代理
```

### 4.2 构建生产包
```bash
cd d:\gas-station\admin
npm install
npm run build
```
构建产物在 `dist/` 目录，上传到服务器 `/opt/gas-station/admin-dist/`

---

## 五、部署客户小程序

### 5.1 修改 API 地址
编辑 `miniapp/utils/api.js`，将 `BASE_URL` 改为生产地址：
```js
const BASE_URL = 'https://你的域名/api'
```

### 5.2 配置微信小程序
1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 注册小程序（如已注册跳过）
3. 获取 AppID
4. 编辑 `miniapp/manifest.json`，填入 AppID

### 5.3 构建上传
1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)
2. 打开 `d:\gas-station\miniapp` 项目
3. 菜单：发行 → 小程序-微信
4. 在微信开发者工具中上传代码
5. 在微信公众平台提交审核

---

## 六、配置 Nginx

创建 `/etc/nginx/conf.d/gas-station.conf`：

```nginx
server {
    listen 80;
    server_name 你的域名.com;

    # 管理后台
    location /admin/ {
        alias /opt/gas-station/admin-dist/;
        try_files $uri $uri/ /admin/index.html;
    }

    # 客户小程序 H5（如有）
    location / {
        root /opt/gas-station/h5-dist/;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

重启 Nginx：
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## 七、配置 HTTPS（强烈建议）

推荐使用 Let's Encrypt 免费证书：
```bash
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名.com
```

---

## 八、验证清单

| 项目 | 验证方式 |
|------|---------|
| 后端健康检查 | `curl http://你的域名/api/health` |
| 管理后台登录 | 浏览器打开 `http://你的域名` → 登录 |
| 客户小程序 API | `curl http://你的域名/api/products` |
| 数据库连接 | `pm2 logs gas-server` 查看日志 |

---

## 九、默认管理员账号

数据库初始包含以下账号（密码均为 `adminyxrq123`，可通过 reset-password.js 修改）：

| 用户名 | 角色 | 说明 |
|--------|------|------|
| yxrqadmin | super_admin | 超级管理员 |
| admin | super_admin | 老板 |
| manager | admin | 经理 |
| dispatcher | dispatcher | 调度员 |
| zhangsan | delivery | 张三 |
| lisi | delivery | 李四 |

---

## 十、当前功能清单

### 已完成
- 管理后台：仪表盘、订单管理、用户管理、商品管理、配送站管理、优惠券管理、预警管理、用气分析、钢瓶押金、反馈管理
- 客户小程序：微信登录、实名注册、商品浏览、下单、订单列表/详情、优惠券、问题反馈
- 后端：全部 API 已对接 MySQL，JWT 认证，每日预警引擎
- 短信验证码（开发模式记录在日志中，生产需对接阿里云/腾讯云短信）

### 待对接（生产环境）
- 微信小程序真实登录（wx.login → 微信 code2session）
- 真实短信服务商对接
- 微信支付对接
- 配送员 App 功能
