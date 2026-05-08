import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# 解决中文字体显示问题
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

def parse_custom_time(time_val, create_date):
    if pd.isna(time_val) or str(time_val).strip() == "":
        return None
    if isinstance(time_val, datetime):
        return time_val.replace(second=0, microsecond=0)
    
    time_str = str(time_val).strip()
    try:
        parts = time_str.split()
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1][:5]
            full_str = f"2026/{date_part} {time_part}" 
            return datetime.strptime(full_str, "%Y/%m/%d %H:%M")
        elif ":" in time_str:
            time_part = time_str[:5]
            if pd.notna(create_date):
                base_date = pd.to_datetime(create_date).strftime("%Y/%m/%d")
                return datetime.strptime(f"{base_date} {time_part}", "%Y/%m/%d %H:%M")
    except:
        return None
    return None

def analyze_time_efficiency():
    file_path = r"C:\Users\Lenovo\.cursor\liuruichen\数据目录\2026日常反馈重点问题汇总表（产品&运营） (12).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ 路径不存在: {file_path}")
        return

    try:
        df = pd.read_excel(file_path)
        df['创建时间'] = pd.to_datetime(df['创建时间'], errors='coerce')
        
        # 清洗时间列
        cols = ['反馈时间', '产品接收时间', '产品转研发时间', '研发反馈修复时间']
        for col in cols:
            if col in df.columns:
                df[col + '_clean'] = df.apply(lambda r: parse_custom_time(r[col], r['创建时间']), axis=1)

        # 计算分钟数
        df['总处理分钟'] = df.apply(
            lambda r: (r['研发反馈修复时间_clean'] - r['反馈时间_clean']).total_seconds()/60
            if pd.notna(r['反馈时间_clean']) and pd.notna(r['研发反馈修复时间_clean']) else None,
            axis=1
        )
        
        df['产品处理分钟'] = df.apply(
            lambda r: ((r['产品接收时间_clean'] if pd.notna(r['产品接收时间_clean']) else r['产品转研发时间_clean']) - r['反馈时间_clean']).total_seconds()/60 
            if pd.notna(r['反馈时间_clean']) and (pd.notna(r['产品接收时间_clean']) or pd.notna(r['产品转研发时间_clean'])) else None, axis=1
        )
        
        df['研发处理分钟'] = df.apply(
            lambda r: (r['研发反馈修复时间_clean'] - r['产品转研发时间_clean']).total_seconds()/60
            if pd.notna(r['研发反馈修复时间_clean']) and pd.notna(r['产品转研发时间_clean']) else None,
            axis=1
        )

        # --- 1. 去噪 (1440分钟内) 并计算平均值 ---
        limit = 1440 
        avg_prod = df[(df['产品处理分钟'] >= 0) & (df['产品处理分钟'] <= limit)]['产品处理分钟'].mean()
        avg_dev = df[(df['研发处理分钟'] >= 0) & (df['研发处理分钟'] <= limit)]['研发处理分钟'].mean()

        print("\n" + "="*30)
        print(f"📊 核心时效统计 (已去噪 - 阈值 {limit}min):")
        print(f"🔹 产品平均处理耗时: {avg_prod:.1f} 分钟")
        print(f"🔹 研发平均修复耗时: {avg_dev:.1f} 分钟")
        print("="*30 + "\n")

        # --- 2. 仅绘制模块耗时柱状图 ---
        m_df = df[(df['总处理分钟'] >= 0) & (df['总处理分钟'] <= limit)].dropna(subset=['总处理分钟', '问题模块'])
        if not m_df.empty:
            module_avg = m_df.groupby('问题模块')['总处理分钟'].mean().sort_values(ascending=False).reset_index()
            
            plt.figure(figsize=(10, 6))
            sns.barplot(data=module_avg, x='问题模块', y='总处理分钟', palette='Blues_r')
            
            plt.title('各问题模块 - 平均总处理耗时 (分钟/去噪后)', fontsize=14, fontweight='bold', pad=20)
            plt.ylabel('平均耗时 (分钟)')
            plt.xticks(rotation=35)
            
            # 标注数值
            for i, v in enumerate(module_avg['总处理分钟']):
                plt.text(i, v + 2, f'{v:.1f}', ha='center', fontweight='bold')
            
            plt.tight_layout()
            plt.show()

    except Exception as e:
        print(f"❌ 程序出错: {e}")

if __name__ == "__main__":
    analyze_time_efficiency()