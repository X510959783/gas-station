import re
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r"D:\AI-Knowledge"
VAULT_PATTERN = re.compile(r'`?D:\\AI-Knowledge\\([^`\n]+\.md)`?')
IN_CODE_BLOCK = False

def to_wikilink(m):
    global IN_CODE_BLOCK
    full = m.group(0)
    path = m.group(1)
    # 检查是否在代码块中
    if IN_CODE_BLOCK:
        return full
    # 去掉 .md 后缀
    name = path.replace('.md', '')
    # 转正斜杠给 Obsidian
    name = name.replace('\\', '/')
    return f'[[{name}]]'

def process_file(filepath):
    global IN_CODE_BLOCK
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result = []
    for line in lines:
        # 追踪代码块状态
        if line.strip().startswith('```'):
            IN_CODE_BLOCK = not IN_CODE_BLOCK
            result.append(line)
            continue
        if IN_CODE_BLOCK:
            result.append(line)
            continue
        # 替换路径引用
        line = VAULT_PATTERN.sub(to_wikilink, line)
        result.append(line)

    new_content = '\n'.join(result)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

count = 0
for root, dirs, files in os.walk(VAULT):
    # 跳过 .git 和 node_modules
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '.obsidian')]
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            if process_file(fp):
                count += 1
                print(f'  OK {os.path.relpath(fp, VAULT)}')

print(f'\n转换完成：{count} 个文件')
