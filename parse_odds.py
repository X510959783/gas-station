"""500.com odds parser v2 - outputs JSON"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import re, os, json

def parse_folder(folder_path):
    result = {}

    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if not f.endswith('.html'): continue
            if '_files' in root: continue

            path = os.path.join(root, f)
            with open(path, 'r', encoding='gb2312', errors='replace') as fh:
                html = fh.read()

            title_match = re.findall(r'<title>(.*?)</title>', html)
            page_title = title_match[0] if title_match else ''

            # --- Asian handicap page (亚盘对比) ---
            if '亚盘' in page_title:
                # Find all company rows with quancheng spans
                quancheng = re.findall(r'<span class="quancheng"[^>]*>(.*?)</span>', html)
                # Find all timestamps
                times = re.findall(r'<time>(.*?)</time>', html)

                # Find handicap data: pattern after each quancheng
                # Each company has initial+instant handicap & timestamps
                result['asian_handicap'] = {
                    'company_count': len(quancheng),
                    'companies': quancheng,
                    'timestamps': times,
                }

            # --- Euro odds / Rangqiu index pages ---
            ttl_positions = [m.start() for m in re.finditer(r'ttl=\"zy\"', html)]
            if ttl_positions:
                # Use tb_plgs title for company names (more reliable)
                all_titles = re.findall(r'class=\"tb_plgs\"\s+title=\"([^\"]*)\"', html)

                companies = {}
                for i, pos in enumerate(ttl_positions):
                    seq = i + 1
                    name = all_titles[i] if i < len(all_titles) else f'#{seq}'

                    chunk = html[pos:pos+5000]

                    tables = re.findall(
                        r'<table[^>]*class=\"pl_table_data\"[^>]*>(.*?)</table>',
                        chunk, re.DOTALL
                    )

                    if len(tables) >= 4:
                        def ex(tbl):
                            return [float(n) for n in re.findall(r'>\s*(\d+\.\d{2,3})%?\s*<', tbl)]

                        t1, t2, t3, t4 = ex(tables[0]), ex(tables[1]), ex(tables[2]), ex(tables[3])

                        if len(t1) >= 6 and len(t4) >= 6:
                            companies[seq] = {
                                'name': name,
                                'odds': {'init': t1[0:3], 'instant': t1[3:6]},
                                'prob': {
                                    'init': t2[0:3] if len(t2) >= 6 else [],
                                    'instant': t2[3:6] if len(t2) >= 6 else [],
                                },
                                'return_rate': {
                                    'init': t3[0] if len(t3) >= 2 else 0,
                                    'instant': t3[1] if len(t3) >= 2 else 0,
                                },
                                'kelly': {'init': t4[0:3], 'instant': t4[3:6]},
                            }

                # Determine page type
                if 'rangqiu' in path or '让球' in page_title:
                    key = 'rangqiu_index'
                else:
                    key = 'euro_odds'

                result[key] = {
                    'company_count': len(companies),
                    'companies': companies,
                }

    return result

if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = r'C:\Users\51095\Desktop\足彩\斯达 2-0 瓦勒伦加05-25.20.30'

    data = parse_folder(folder)
    print(json.dumps(data, ensure_ascii=False, indent=2))
