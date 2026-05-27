# -*- coding: utf-8 -*-
"""代理绕过模块 — Windows系统代理指向CC Proxy但服务未运行时使用
在每个需要网络的脚本开头 import proxy_config 即可绕过系统代理
"""
import os


def bypass_system_proxy():
    """清除代理环境变量, 强制Python直连网络"""
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'):
        os.environ.pop(key, None)
    # 设置urllib不使用系统代理
    os.environ['no_proxy'] = '*'
    os.environ['NO_PROXY'] = '*'


def patch_urllib():
    """为urllib安装无代理handler"""
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    except Exception:
        pass


def patch_requests():
    """为requests库设置无代理 (如果已安装)"""
    try:
        import requests
        # monkey-patch Session to default to no proxy
        _orig_init = requests.Session.__init__
        def _patched_init(self, *args, **kwargs):
            _orig_init(self, *args, **kwargs)
            self.proxies = {}
            self.trust_env = False
        requests.Session.__init__ = _patched_init
    except Exception:
        pass


# 自动执行
bypass_system_proxy()
patch_urllib()
patch_requests()
