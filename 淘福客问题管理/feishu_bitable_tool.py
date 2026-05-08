"""
飞书多维表格读写工具

功能:
1. 写: Excel/数据 → 创建或追加写入飞书多维表格
2. 读: 飞书多维表格 → 导出为 Excel / DataFrame 分析

使用方法:
1. 填写下方的 APP_ID 和 APP_SECRET
2. 运行脚本，选择操作模式
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
import time
import pandas as pd
import numpy as np

# ==================== 配置 ====================
APP_ID = "cli_a95720e993f89cc0"
APP_SECRET = "hkCLCpDI3saV1N7qQKqapcyQuMwa57Xj"
USER_ID = "6935338025601777665"  # 刘瑞辰的飞书用户 ID（用于自动授予编辑权限）
# ==============================================

BASE_URL = "https://open.feishu.cn/open-apis"


# ================================================================
#  基础能力：鉴权 & API 调用
# ================================================================

def get_tat():
    """获取 Tenant Access Token"""
    resp = requests.post(
        f"{BASE_URL}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取 TAT 失败: {data}")
    return data["tenant_access_token"]


def api_call(tat, method, path, body=None):
    """通用 API 调用"""
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {tat}", "Content-Type": "application/json"}
    resp = getattr(requests, method)(url, headers=headers, json=body)
    return resp.json()


# ================================================================
#  工具函数
# ================================================================

def fix_date_format(date_series):
    """修复日期格式（如 '3/15 10:00' → '2026-03-15 10:00'）"""
    s = date_series.astype(str).str.strip()
    mask = s.str.match(r'^\d{1,2}/\d{1,2}\s')
    s.loc[mask] = '2026/' + s.loc[mask]
    return pd.to_datetime(s, errors='coerce')


def format_datetime(dt):
    """格式化 datetime 为文本字符串"""
    if pd.isna(dt):
        return ""
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt)


DATE_COLS = {'创建时间', '反馈时间', '产品接收时间', '产品转研发时间', '研发反馈修复时间'}


def build_records(df, cols):
    """将 DataFrame 行转为飞书记录格式"""
    records = []
    for idx, row in df.iterrows():
        record_fields = {}
        for col in cols:
            val = row[col]
            field_name = str(col)[:30]

            if pd.isna(val):
                record_fields[field_name] = ""
            elif isinstance(val, pd.Timestamp):
                formatted = format_datetime(val)
                record_fields[field_name] = formatted if formatted else None
            elif isinstance(val, (int, float)):
                if np.isinf(val) or np.isnan(val):
                    record_fields[field_name] = ""
                else:
                    record_fields[field_name] = int(val) if isinstance(val, (np.int64, np.int32)) else float(val)
            else:
                s_val = str(val).strip()
                record_fields[field_name] = s_val if s_val else ""

        records.append({"fields": record_fields})
    return records


# ================================================================
#  写入功能
# ================================================================

def create_bitable(tat, name):
    """创建多维表格，返回 app_token 和默认 table_id（自动授予当前用户编辑权限）"""
    print(f">>> 创建多维表格: {name} ...")
    result = api_call(tat, "post", "/bitable/v1/apps", {"name": name})
    code = result.get("code")
    if code != 0:
        raise Exception(f"创建多维表格失败 (code={code}): {result.get('msg')}\n完整返回: {json.dumps(result, ensure_ascii=False)}\n\n请到开放平台开通 bitable:app 权限")

    app_info = result["data"]["app"]
    app_token = app_info["app_token"]
    table_id = app_info["default_table_id"]
    print(f"   OK! app_token: {app_token[:15]}...  默认表ID: {table_id}")

    # 自动授予当前用户编辑权限（使用 drive/v1/permissions API）
    try:
        api_call(tat, "post", f"/drive/v1/permissions/{app_token}/members?type=bitable", {
            "member_type": "openid",
            "member_id": USER_ID,
            "perm": "full_access"
        })
        print(f"   ✓ 已授予当前用户完全访问权限")
    except Exception as e:
        print(f"   ~ 授予权限失败(可能需要手动申请): {e}")

    return app_token, table_id


def create_or_update_fields(tat, app_token, table_id, fields):
    """批量添加字段到数据表（已存在则跳过）"""
    for f in fields:
        try:
            api_call(tat, "post", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", f)
            print(f"   + 字段: {f['field_name']}")
        except Exception:
            print(f"   ~ 字段 {f['field_name']} 已存在，跳过")


def batch_create_records(tat, app_token, table_id, records, batch_size=50):
    """批量写入记录（每批最多 50 条），返回成功数"""
    total = len(records)
    print(f"\n>>> 开始写入 {total} 条记录 (每批 {batch_size})...")

    success_count = 0
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        result = api_call(tat, "post", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create", {
            "records": batch
        })

        code = result.get("code")
        if code == 0:
            success_count += len(batch)
            print(f"   [{batch_num}/{total_batches}] 写入 {len(batch)} 条 ✓")
        else:
            print(f"   [{batch_num}/{total_batches}] 失败: {result.get('msg')} ({code})")

        if batch_num < total_batches:
            time.sleep(0.3)

    print(f"\n   共成功写入 {success_count}/{total} 条记录!")
    return success_count


def write_excel_to_bitable(excel_file, table_name=None, month_filter=None):
    """
    将 Excel 数据写入飞书多维表格（主流程）

    Args:
        excel_file: Excel 文件路径
        table_name: 多维表格名称（默认用文件名）
        month_filter: 筛选指定月份的数据（如 3 表示三月），None 则不过滤
    """
    tat = get_tat()
    print("   ✓ 获取凭证成功\n")

    # 读取 Excel
    print(f"[1/4] 读取 Excel: {excel_file}")
    df = pd.read_excel(excel_file, engine='openpyxl')
    time_cols = ['反馈时间', '产品接收时间', '产品转研发时间', '研发反馈修复时间']
    for col in time_cols:
        if col in df.columns:
            df[col] = fix_date_format(df[col])
    if '创建时间' in df.columns:
        df['创建时间'] = pd.to_datetime(df['创建时间'], errors='coerce')

    if month_filter and '创建时间' in df.columns:
        df = df[df['创建时间'].dt.month == month_filter].copy()

    cols = list(df.columns)
    print(f"   OK! 共 {len(df)} 条数据, 列: {cols}\n")

    # 创建多维表格
    name = table_name or excel_file.replace('.xlsx', '')
    print("[2/4] 创建多维表格...")
    app_token, table_id = create_bitable(tat, name)

    # 定义字段并添加
    print("\n[3/4] 定义字段...")
    col_type_map = {"序号": 3}  # 数字类型映射
    fields = []
    for col in cols:
        field_name = str(col)[:30]
        field_type = col_type_map.get(col, 1)  # 默认文本
        fields.append({"field_name": field_name, "type": field_type})

    create_or_update_fields(tat, app_token, table_id, fields)

    # 写入记录
    print("\n[4/4] 写入数据...")
    records = build_records(df, cols)
    success = batch_create_records(tat, app_token, table_id, records)

    print("\n" + "=" * 55)
    if success > 0:
        print(f"  同步完成! 成功写入 {success} 条记录")
        print(f"  多维表格链接: https://www.feishu.cn/base/{app_token}")
    else:
        print("  未写入任何记录")
    print("=" * 55)

    return app_token


# ================================================================
#  读取功能
# ================================================================

def list_tables(tat, app_token):
    """列出多维表格下所有数据表"""
    result = api_call(tat, "get", f"/bitable/v1/apps/{app_token}/tables")
    if result.get("code") != 0:
        raise Exception(f"获取表列表失败: {result}")
    return result["data"]["items"]


def list_fields(tat, app_token, table_id):
    """列出数据表所有字段"""
    result = api_call(tat, "get", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields")
    if result.get("code") != 0:
        raise Exception(f"获取字段列表失败: {result}")
    return result["data"]["items"]


def fetch_all_records(tat, app_token, table_id, page_size=100):
    """
    分页拉取全部记录

    Returns:
        list[dict]: 记录列表，每条包含 fields 字典
    """
    all_records = []
    page_token = None

    while True:
        body = {"page_size": page_size}
        if page_token:
            body["page_token"] = page_token

        result = api_call(tat, "post", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search", body)

        if result.get("code") != 0:
            raise Exception(f"读取记录失败: {result}")

        items = result["data"].get("items", [])
        all_records.extend(items)

        has_more = result["data"].get("has_more", False)
        if not has_more or not items:
            break

        page_token = result["data"].get("page_token")

    print(f"   OK! 共读取 {len(all_records)} 条记录")
    return all_records


def records_to_dataframe(records):
    """将飞书记录转为 DataFrame"""
    rows = [r["fields"] for r in records if "fields" in r]
    return pd.DataFrame(rows)


def read_bitable_to_excel(app_token, output_file=None, table_id=None):
    """
    从飞书多维表格读取数据并导出为 Excel

    Args:
        app_token: 多维表格 app_token
        output_file: 输出 Excel 路径（默认自动生成）
        table_id: 指定数据表 ID（None 则使用默认表）
    """
    tat = get_tat()

    # 如果没传 table_id，先获取默认表
    if not table_id:
        tables = list_tables(tat, app_token)
        default_table = [t for t in tables if t.get("default")][0]
        table_id = default_table["table_id"]
        print(f"   使用默认数据表: {default_table['name']}\n")

    print("[1/3] 拉取字段定义...")
    field_items = list_fields(tat, app_token, table_id)
    print(f"   OK! 共 {len(field_items)} 个字段\n")

    print("[2/3] 拉取全部记录...")
    records = fetch_all_records(tat, app_token, table_id)
    print()

    print("[3/3] 转换为 DataFrame...")
    df = records_to_dataframe(records)
    print(f"   OK! DataFrame 形状: {df.shape}\n")

    # 导出到 Excel
    if output_file is None:
        output_file = f"bitable_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df.to_excel(output_file, index=False, engine='openpyxl')
    print("=" * 55)
    print(f"  导出完成! 文件: {output_file}")
    print(f"  共 {len(df)} 条记录, {len(df.columns)} 个字段")
    print("=" * 55)

    return df


def read_bitable_to_dataframe(app_token, table_id=None):
    """
    从飞书多维表格读取数据，返回 DataFrame（不导出文件）

    适用于需要进一步数据分析的场景
    """
    tat = get_tat()
    if not table_id:
        tables = list_tables(tat, app_token)
        default_table = [t for t in tables if t.get("default")][0]
        table_id = default_table["table_id"]

    print(f">>> 正在从多维表格读取数据...")
    records = fetch_all_records(tat, app_token, table_id)
    return records_to_dataframe(records)


# ================================================================
#  主入口 - 交互模式
# ================================================================

def main():
    print("=" * 55)
    print("  飞书多维表格读写工具")
    print("=" * 55)
    print("\n可选操作:")
    print("  1. 写入模式 — Excel 数据 → 新建多维表格")
    print("  2. 读取模式 — 多维表格 → 导出 Excel")
    print("  3. 读取模式 — 多维表格 → 返回 DataFrame (代码调用)")
    print()

    mode = input("  请选择 [1/2/3]: ").strip()

    try:
        if mode == "1":
            excel = input("  Excel 文件路径 (回车使用默认): ").strip() or '2026日常反馈重点问题汇总表（产品&运营） (12).xlsx'
            name = input("  表格名称 (回车使用文件名): ").strip() or None
            m = input("  筛选月份 (如 3, 回车跳过): ").strip()
            month = int(m) if m else None
            write_excel_to_bitable(excel, name, month)

        elif mode == "2":
            token = input("  多维表格 app_token: ").strip()
            out = input("  输出文件名 (回车自动生成): ").strip() or None
            read_bitable_to_excel(token, out)

        elif mode == "3":
            token = input("  多维表格 app_token: ").strip()
            df = read_bitable_to_dataframe(token)
            print(f"\n  DataFrame 已就绪! shape={df.shape}, 可继续分析:")
            print(f"   列名: {list(df.columns)[:10]}{'...' if len(df.columns)>10 else ''}")
            import IPython; IPython.embed()  # 进入交互式 shell

        else:
            print("  无效选择")
    except KeyboardInterrupt:
        print("\n  已取消")
    except Exception as e:
        print(f"\n  ERROR: {e}")


if __name__ == "__main__":
    main()
