"""500.com让球指数解析器 - 完整版
每家公司 = 4个内嵌表 = 20个数字
表1(赔率): 初盘3 + 即时3
表2(概率): 初盘3 + 即时3
表3(返还率): 初盘1 + 即时1
表4(凯利): 初盘3 + 即时3
"""
import re, os

def find_html(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if f.endswith('.html') and '_files' not in root:
                return os.path.join(root, f)
    return None

def parse(html):
    positions = [m.start() for m in re.finditer(r'ttl=\"zy\"', html)]
    companies = {}

    for i, pos in enumerate(positions):
        seq = i + 1
        chunk = html[pos:pos+5000]

        # 提取公司名
        nearby = html[max(0,pos-1200):pos+200]
        titles = re.findall(r'title=\"([^\"]*)\"', nearby)
        name = titles[-1] if titles else f'#{seq}'

        # 找4个内嵌表
        tables = re.findall(
            r'<table[^>]*class=\"pl_table_data\"[^>]*>(.*?)</table>',
            chunk, re.DOTALL
        )

        if len(tables) < 4:
            continue

        # 提取每个表的数字（支持%后缀）
        def extract_nums(table_html):
            nums = re.findall(r'>\s*(\d+\.\d{2,3})%?\s*<', table_html)
            return [float(n) for n in nums]

        t1 = extract_nums(tables[0])  # 赔率: 初盘3 + 即时3 = 6
        t2 = extract_nums(tables[1])  # 概率: 初盘3 + 即时3 = 6
        t3 = extract_nums(tables[2])  # 返还率: 初盘1 + 即时1 = 2
        t4 = extract_nums(tables[3])  # 凯利: 初盘3 + 即时3 = 6

        if len(t1) >= 6 and len(t4) >= 6:
            companies[seq] = {
                'name': name,
                'odds': {
                    'init': t1[0:3], 'inst': t1[3:6]
                },
                'prob': {
                    'init': t2[0:3] if len(t2) >= 6 else [],
                    'inst': t2[3:6] if len(t2) >= 6 else []
                },
                'return_rate': {
                    'init': t3[0] if len(t3) >= 2 else 0,
                    'inst': t3[1] if len(t3) >= 2 else 0
                },
                'kelly': {
                    'init': t4[0:3], 'inst': t4[3:6]
                }
            }

    return companies

if __name__ == '__main__':
    folder = r'C:\Users\51095\Desktop\足彩\斯达 2-0 瓦勒伦加05-25.20.30'
    path = find_html(folder)
    if not path: print('ERROR'); exit(1)

    with open(path, 'r', encoding='gb2312', errors='replace') as f:
        html = f.read()

    cos = parse(html)
    print(f'公司: {len(cos)}')

    for seq in [1, 2, 3]:
        if seq in cos:
            c = cos[seq]
            print(f"\n#{seq}: {c['name']}")
            print(f"  赔率: 初{c['odds']['init']} -> 即{c['odds']['inst']}")
            print(f"  概率: 初{c['prob']['init']} -> 即{c['prob']['inst']}")
            print(f"  返还率: 初{c['return_rate']['init']:.2f}% -> 即{c['return_rate']['inst']:.2f}%")
            print(f"  凯利: 初{c['kelly']['init']} -> 即{c['kelly']['inst']}")
