import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def extract_content_from_record(record: Dict[str, Any]):
    """
    从一条记录中提取assistant的content字符串或对象。
    支持多种可能的结构：
      - record['response']['body']['choices'][0]['message']['content']
      - record['response']['body']['choices'][0]['text']
      - record['choices'][0]['message']['content']
      - record['response']['choices'] ... 等

    返回 (content_obj, raw_content_str)
    - content_obj: 尝试将raw_content_str解析为JSON后的对象，若解析失败则为None
    - raw_content_str: 原始字符串内容（如果找不到则为None）
    """
    # 深度查找可能的位置
    raw = None

    # 常见路径尝试顺序
    paths_to_try = [
        ("response", "body", "choices"),
        ("response", "choices"),
        ("choices",),
        ("body", "choices"),
    ]

    for p in paths_to_try:
        node = record
        ok = True
        for key in p:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                ok = False
                break
        if not ok:
            continue

        # node 期望为 choices 列表
        if isinstance(node, list) and len(node) > 0:
            first = node[0]
            # message.content
            if isinstance(first, dict) and 'message' in first and isinstance(first['message'], dict) and 'content' in first['message']:
                raw = first['message']['content']
                break
            # text
            if isinstance(first, dict) and 'text' in first:
                raw = first['text']
                break
            # 直接字符串
            if isinstance(first, str):
                raw = first
                break

    # 作为最后兜底，尝试直接在record中寻找 message
    if raw is None:
        # record['response']['body'] 直接为字符串
        try_paths = [
            ("response", "body"),
            ("response",),
            (),
        ]
        for p in try_paths:
            node = record
            ok = True
            for key in p:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    ok = False
                    break
            if not ok:
                continue
            if isinstance(node, dict) and 'message' in node and isinstance(node['message'], dict) and 'content' in node['message']:
                raw = node['message']['content']
                break
            if isinstance(node, str):
                raw = node
                break

    if raw is None:
        return None, None

    # 如果raw是非字符串（可能已经是JSON对象），直接返回
    if not isinstance(raw, str):
        return raw, json.dumps(raw, ensure_ascii=False)

    # 尝试将字符串解析为JSON对象
    try:
        parsed = json.loads(raw)
        return parsed, raw
    except Exception:
        return None, raw


def aggregate_usage(usage_acc: Dict[str, int], usage_obj: Dict[str, Any]):
    """将单条记录的usage累加到usage_acc里"""
    if not isinstance(usage_obj, dict):
        return
    for key in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
        val = usage_obj.get(key)
        if isinstance(val, int):
            usage_acc[key] = usage_acc.get(key, 0) + val


def process_jsonl_file(input_path: str, output_dir: str, stats_path: str = None):
    ensure_dir(output_dir)

    total = {
        'records': 0,
        'saved': 0,
        'skipped': 0,
        'usage': {}
    }

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception as e:
                print(f"跳过第 {line_no} 行：无法解析为 JSON: {e}")
                total['skipped'] += 1
                continue

            total['records'] += 1

            # 获取 custom_id
            custom_id = record.get('custom_id') or record.get('id') or f"row{line_no:06d}"
            # 保证是字符串
            custom_id = str(custom_id)

            # 提取 content
            content_obj, raw_content = extract_content_from_record(record)

            # 如果找不到content，则尝试其他位置
            if raw_content is None:
                # 有些记录里可能直接在 response.body 中
                resp = record.get('response') or {}
                body = None
                if isinstance(resp, dict):
                    body = resp.get('body')
                if isinstance(body, dict) and 'choices' in body:
                    # 已经在extract_content_from_record尝试过，这里直接跳过
                    pass

            # 保存到文件
            out_path = os.path.join(output_dir, f"{custom_id}.json")
            try:
                # 优先保存解析后的 JSON 对象（如果存在），否则保存原始字符串作为 "content" 字段
                if content_obj is not None:
                    with open(out_path, 'w', encoding='utf-8') as wf:
                        json.dump(content_obj, wf, ensure_ascii=False, indent=2)
                elif raw_content is not None:
                    # 保存为一个包含 content 的 JSON 对象
                    with open(out_path, 'w', encoding='utf-8') as wf:
                        json.dump({"content": raw_content}, wf, ensure_ascii=False, indent=2)
                else:
                    # 找不到content，保存整个record以便排查
                    with open(out_path, 'w', encoding='utf-8') as wf:
                        json.dump(record, wf, ensure_ascii=False, indent=2)

                total['saved'] += 1

            except Exception as e:
                print(f"保存 {out_path} 失败: {e}")
                total['skipped'] += 1
                continue

            # 累加 usage 信息
            # usage 可能位于 record['response']['body']['usage'] 或 record['response']['usage'] 或 record['usage']
            usage_obj = None
            try:
                if isinstance(record.get('response'), dict):
                    resp = record.get('response')
                    if isinstance(resp.get('body'), dict) and 'usage' in resp.get('body'):
                        usage_obj = resp['body']['usage']
                    elif 'usage' in resp:
                        usage_obj = resp['usage']
                if usage_obj is None and 'usage' in record:
                    usage_obj = record['usage']
            except Exception:
                usage_obj = None

            if usage_obj:
                aggregate_usage(total['usage'], usage_obj)

    # 输出统计结果
    print('\n=== 提取完成 ===')
    print(f"总记录数: {total['records']}")
    print(f"已保存: {total['saved']}")
    print(f"跳过/失败: {total['skipped']}")
    print("累积 token 用量:")
    for k, v in total['usage'].items():
        print(f"  {k}: {v}")

    # 写入 stats 文件（如果指定）
    if stats_path:
        try:
            with open(stats_path, 'w', encoding='utf-8') as sf:
                json.dump(total, sf, ensure_ascii=False, indent=2)
            print(f"已保存统计文件: {stats_path}")
        except Exception as e:
            print(f"保存统计文件失败: {e}")

    return total


def main():
    parser = argparse.ArgumentParser(description='从 JSONL 中提取每行的 assistant content 并保存为 {custom_id}.json，统计 token 用量')
    parser.add_argument('input', nargs='?', default=None, help='输入 JSONL 文件路径或目录（可选，留空将交互式输入）')
    parser.add_argument('-o', '--out', default=None, help='输出根目录 (可选)。若未指定，则在每个 JSONL 文件同目录创建同名目录保存结果)')
    parser.add_argument('-s', '--stats', default=None, help='可选：统计结果保存路径（单文件时为文件路径，多文件时将保存到每个输出目录下的 stats.json）')

    args = parser.parse_args()

    input_path = args.input
    # 交互式输入：当未提供 positional 参数时，提示用户输入
    if not input_path:
        try:
            input_path = input('请输入 JSONL 文件路径或目录: ').strip()
        except Exception:
            input_path = None

    if not input_path:
        print('未提供输入路径，操作已取消')
        return 1

    input_path = os.path.abspath(input_path)

    # 收集所有要处理的 jsonl 文件
    jsonl_files = []
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.jsonl'):
            jsonl_files = [input_path]
        else:
            print(f"错误：指定的文件不是 .jsonl 文件: {input_path}")
            return 1
    elif os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for fn in files:
                if fn.lower().endswith('.jsonl'):
                    jsonl_files.append(os.path.join(root, fn))
    else:
        print(f"错误：路径不存在: {input_path}")
        return 1

    if not jsonl_files:
        print('未找到任何 .jsonl 文件。')
        return 1

    print(f"找到 {len(jsonl_files)} 个 .jsonl 文件，开始逐个处理...")

    # 如果提供了 -o 输出根目录，则在该根目录下为每个文件创建以文件名为名的子目录
    out_root = args.out
    multiple = len(jsonl_files) > 1

    for idx, jf in enumerate(sorted(jsonl_files), 1):
        print(f"\n[{idx}/{len(jsonl_files)}] 处理: {jf}")
        stem = Path(jf).stem
        jf_dir = os.path.dirname(jf)

        if out_root:
            # 使用用户指定的输出根目录
            out_dir = os.path.join(os.path.abspath(out_root), stem)
        else:
            # 在输入文件同目录创建同名目录
            out_dir = os.path.join(jf_dir, stem)

        # stats 路径策略：若用户指定 -s 且仅处理单文件，则使用该路径；
        # 若处理多个文件且用户给了 -s，则在每个输出目录写入 stats.json
        if args.stats:
            if multiple:
                stats_path = os.path.join(out_dir, 'stats.json')
            else:
                stats_path = args.stats
        else:
            stats_path = None

        # 确保输出目录存在
        ensure_dir(out_dir)

        process_jsonl_file(jf, out_dir, stats_path)

    print('\n全部处理完成')
    return 0


if __name__ == '__main__':
    main()
