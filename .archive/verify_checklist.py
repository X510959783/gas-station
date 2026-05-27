"""
六维分析 — 验证门禁
每次分析前必须跑这个脚本，全部通过才能开始分析
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import re, os, json

def verify(folder_path):
    """验证指定文件夹里的数据完整性"""
    results = []

    # 1. 找所有 HTML 文件
    html_files = {}
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if f.endswith('.html') and '_files' not in root:
                key = '百家欧赔' if '百家欧赔' in f else ('让球指数' if '让球指数' in f else ('亚盘对比' if '亚盘对比' in f else '其他'))
                html_files[key] = os.path.join(root, f)

    results.append(('文件数', f"{len(html_files)}个: {list(html_files.keys())}"))

    # 2. 验证百家欧赔
    if '百家欧赔' in html_files:
        with open(html_files['百家欧赔'], 'r', encoding='gb2312', errors='replace') as f:
            html = f.read()

        ttl_zy = html.count('ttl="zy"')
        has_jc = '竞*官*' in html or '竞彩官*' in html
        has_kelly = '凯利' in html
        has_return = '返还率' in html
        page_title = re.findall(r'<title>(.*?)</title>', html)

        results.append(('百家欧赔-公司数', f'{ttl_zy}家'))
        results.append(('百家欧赔-竞彩', 'YES' if has_jc else 'NO'))
        results.append(('百家欧赔-凯利', 'YES' if has_kelly else 'NO'))
        results.append(('百家欧赔-返还率', 'YES' if has_return else 'NO'))
        results.append(('百家欧赔-标题', page_title[0] if page_title else 'N/A'))

    # 3. 验证亚盘对比
    if '亚盘对比' in html_files:
        with open(html_files['亚盘对比'], 'r', encoding='gb2312', errors='replace') as f:
            html = f.read()

        times = re.findall(r'<time>(.*?)</time>', html)
        titles = re.findall(r'class="tb_plgs"\s+title="([^"]*)"', html)

        results.append(('亚盘对比-公司数', f'{len(titles)}家'))
        results.append(('亚盘对比-时间戳', f'{len(times)}条'))
        if times:
            results.append(('亚盘对比-时间范围', f'{times[0]} ~ {times[-1]}'))

    # 4. 验证让球指数
    if '让球指数' in html_files:
        with open(html_files['让球指数'], 'r', encoding='gb2312', errors='replace') as f:
            html = f.read()

        ttl_zy = html.count('ttl="zy"')
        has_rangqiu = '让球' in html

        results.append(('让球指数-公司数', f'{ttl_zy}家'))
        results.append(('让球指数-让球列', 'YES' if has_rangqiu else 'NO'))

    # ===== 输出 =====
    all_pass = True
    print("=" * 50)
    print("数据验证报告")
    print("=" * 50)
    for item, value in results:
        # 简单检查
        is_warn = False
        if '竞彩' in item and 'NO' in str(value):
            is_warn = True
            all_pass = False
        if '公司数' in item:
            try:
                n = int(str(value).replace('家',''))
                if n < 10:
                    is_warn = True
            except: pass

        marker = " [WARN]" if is_warn else " [OK]"
        print(f"  {marker} {item}: {value}")

    print(f"\n门禁: {'通过 [OK]' if all_pass else '未通过 [WARN] 需要检查'}")
    return all_pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = r'C:\Users\51095\Desktop\足彩\斯达 2-0 瓦勒伦加05-25.20.30'
    verify(folder)
