import os
import re
import glob
import time
from datetime import datetime
from openpyxl import Workbook
import requests

# ==================== 飞书多维表格 ====================

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

def _feishu_get_tat(app_id, app_secret):
    """获取飞书 Tenant Access Token"""
    r = requests.post(
        f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret}
    )
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"获取飞书 Token 失败: {data}")
    return data["tenant_access_token"]

def _feishu_api_call(tat, method, path, body=None):
    """通用飞书 API 调用"""
    url = f"{FEISHU_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {tat}", "Content-Type": "application/json"}
    r = getattr(requests, method)(url, headers=headers, json=body)
    return r.json()

def _feishu_create_table(tat, name):
    """创建多维表格，返回 (app_token, table_id)"""
    result = _feishu_api_call(tat, "post", "/bitable/v1/apps", {"name": name})
    if result.get("code") != 0:
        raise Exception(f"创建多维表格失败: {result}")
    return result["data"]["app"]["app_token"], result["data"]["app"]["default_table_id"]

def _feishu_add_fields(tat, app_token, table_id, field_defs):
    """添加字段到数据表（field_defs: list of dict，每项含 field_name 和 type）"""
    for f in field_defs:
        try:
            _feishu_api_call(tat, "post",
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", f)
        except Exception:
            pass  # 字段已存在则跳过

def _date_to_ts(val):
    """将日期字符串/datetime 转为飞书时间戳（毫秒）"""
    if not val:
        return ""
    if isinstance(val, (int, float)):
        # 可能已经是时间戳或数字
        try:
            dt = datetime.fromtimestamp(float(val))
            return int(dt.timestamp() * 1000)
        except:
            return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M",
                     "%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(val.strip(), fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
    return val

def _build_feishu_record(item, headers):
    """将一条 dict 数据转为飞书记录格式"""
    fields = {}
    for h in headers:
        val = item.get(h, "")
        # 空值处理
        if val is None or (isinstance(val, str) and val.strip() == ""):
            fields[h] = ""
        elif h in ("反馈时间", "产品接收时间", "产品转研发时间", "研发反馈修复时间", "创建时间"):
            # 时间字段转毫秒时间戳
            ts = _date_to_ts(val)
            fields[h] = ts if ts else ""
        elif isinstance(val, bool):
            fields[h] = val
        else:
            fields[h] = str(val) if val else ""
    return {"fields": fields}

def save_to_bitable(data_list, headers, config):
    """
    将数据写入飞书多维表格
    
    Args:
        data_list: list[dict] 数据列表
        headers: list[str] 表头列表
        config: 飞书配置 dict，需包含 app_id, app_secret, user_open_id
    
    Returns:
        str: 多维表格链接
    """
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    user_open_id = config["user_open_id"]
    
    tat = _feishu_get_tat(app_id, app_secret)
    
    # 1. 创建多维表格
    now = datetime.now().strftime("%m-%d %H:%M")
    table_name = f"问题记录表_{now}"
    print(f"\n📋 正在创建飞书多维表格 [{table_name}]...")
    
    app_token, table_id = _feishu_create_table(tat, table_name)
    print(f"   表格已创建")
    
    # 2. 授权当前用户（使用 drive/v1 permissions API）
    try:
        _feishu_api_call(tat, "post",
            f"/drive/v1/permissions/{app_token}/members?type=bitable",
            {
                "member_type": "openid",
                "member_id": user_open_id,
                "perm": "full_access"
            })
        print(f"   ✓ 已授予你完全访问权限")
    except Exception as e:
        print(f"   ⚠ 授权失败(可手动打开链接申请): {e}")
    
    # 3. 创建字段（全部用文本类型 type=1，简单可靠）
    field_defs = [{"field_name": h, "type": 1} for h in headers]
    _feishu_add_fields(tat, app_token, table_id, field_defs)
    
    # 4. 分批写入记录（每批最多50条）
    batch_size = 50
    total = len(data_list)
    success_count = 0
    
    for i in range(0, total, batch_size):
        batch = data_list[i:i + batch_size]
        records = [_build_feishu_record(item, headers) for item in batch]
        
        result = _feishu_api_call(tat, "post",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            {"records": records}
        )
        
        if result.get("code") == 0:
            success_count += len(batch)
        else:
            print(f"   ⚠ 批次写入失败: {result.get('msg')}")
        
        time.sleep(0.3)  # 避免限频
    
    link = f"https://www.feishu.cn/base/{app_token}"
    print(f"   ✅ 成功写入 {success_count}/{total} 条记录!")
    print(f"🔗 链接: {link}")
    
    return link


# ==================== Excel 相关函数 ====================

def clean_old_files(output_dir, max_files):
    """删除编号最小的文件，确保最多保留 max_files 个"""
    pattern = os.path.join(output_dir, "问题记录表*.xlsx")
    existing_files = glob.glob(pattern)
    
    if len(existing_files) >= max_files:
        sorted_files = sorted(existing_files)
        files_to_delete = sorted_files[:len(existing_files) - max_files + 1]
        
        for f in files_to_delete:
            try:
                os.remove(f)
                print(f"🗑️ 已删除旧文件: {os.path.basename(f)}")
            except Exception as e:
                print(f"⚠️ 删除失败 {os.path.basename(f)}: {e}")

def get_new_filename(base_path, max_files):
    """自动生成递增的文件名"""
    output_dir = os.path.dirname(base_path)
    base_name = os.path.basename(base_path)
    
    clean_old_files(output_dir, max_files)
    
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_name)
    i = 1
    while True:
        new_name = f"{name}_{i:02d}{ext}"
        full_new_path = os.path.join(output_dir, new_name)
        if not os.path.exists(full_new_path):
            return full_new_path
        i += 1

def clean_name(name):
    """手动硬编码清洗函数"""
    if not name: return ""
    mapping = {
        "阿泽": "林智泽",
        "钱林达": "linda",
        "hemei": "何美"
    }
    name = str(name)
    for k, v in mapping.items():
        if k.lower() in name.lower():
            name = v
            break
            
    name = re.sub(r'研发|产研|产品|@微信|@.*?\s', '', name)
    name = re.sub(r'（.*?）|\(.*?\)|\-.*', '', name)
    return name.strip()

def save_to_excel(data_list, filename, headers):
    """将 JSON 数据保存为 Excel"""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)

    for item in data_list:
        item["反馈人"] = clean_name(item.get("反馈人", ""))
        item["处理人"] = clean_name(item.get("处理人", ""))
        row = [item.get(h, "") for h in headers]
        ws.append(row)

    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18

    wb.save(filename)