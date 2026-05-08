import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines

# ==========================================
# 0. 环境与基础设置
# ==========================================
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 修复 Excel 导出时间缺少“年份”的函数
def fix_date_format(date_series):
    s = date_series.astype(str).str.strip()
    mask = s.str.match(r'^\d{1,2}/\d{1,2}\s')
    s.loc[mask] = '2026/' + s.loc[mask]
    return pd.to_datetime(s, errors='coerce')

# ==========================================
# 1. 数据读取与解析
# ==========================================
file_path = '2026日常反馈重点问题汇总表（产品&运营） (12).xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

time_cols = ['反馈时间', '产品接收时间', '产品转研发时间', '研发反馈修复时间']
for col in time_cols:
    df[col] = fix_date_format(df[col])

df['创建时间'] = pd.to_datetime(df['创建时间'], errors='coerce')

# 筛选3月份的数据
df_march = df[df['创建时间'].dt.month == 3].copy()

# ==========================================
# 2. 输出两张数据统计表格 (复刻截图，占比保留两位小数)
# ==========================================
print("=" * 40)
# 【表格1】问题类型分布占比
type_counts = df_march['问题类型'].value_counts().reset_index()
type_counts.columns = ['问题类型', '个数']
total_issues = type_counts['个数'].sum()

if total_issues > 0:
    # 修改点：使用 lambda 表达式强制保留两位小数，并拼接百分号
    type_counts['占比'] = (type_counts['个数'] / total_issues * 100).apply(lambda x: f"{x:.2f}%")
    print("📊 【3月份问题类型分布】")
    print("-" * 40)
    print(type_counts.to_string(index=False))

print("\n" + "=" * 40)

# 【表格2】系统Bug模块分布占比
bug_types = ['常规bug', '异常bug', '第三方bug']
bug_df = df_march[df_march['问题类型'].isin(bug_types)].copy()

if not bug_df.empty:
    module_counts = bug_df['问题模块'].value_counts().reset_index()
    module_counts.columns = ['问题模块', '个数']
    total_bugs = module_counts['个数'].sum()
    
    # 修改点：强制保留两位小数
    module_counts['占比'] = (module_counts['个数'] / total_bugs * 100).apply(lambda x: f"{x:.2f}%")
    print("🐞 【3月份系统Bug模块分布】")
    print("-" * 40)
    print(module_counts.to_string(index=False))
    
    # 修改点：结论文案也保留两位小数
    bug_ratio = f"{(total_bugs / total_issues * 100):.2f}" if total_issues > 0 else "0.00"
    print("-" * 40)
    print(f"💡 结论提取：3月份系统Bug（含第三方）共计 {total_bugs} 个，占总问题数的 {bug_ratio}%")
print("=" * 40 + "\n")


# ==========================================
# 3. 处理时长计算与数据清洗
# ==========================================
df_march['产品处理时长'] = (df_march['产品接收时间'] - df_march['反馈时间']).dt.total_seconds() / 60
df_march['研发处理时长'] = (df_march['研发反馈修复时间'] - df_march['产品转研发时间']).dt.total_seconds() / 60

# 清洗数据：剔除负数、空值
df_march.loc[df_march['产品处理时长'] < 0, '产品处理时长'] = np.nan
df_march.loc[df_march['研发处理时长'] < 0, '研发处理时长'] = np.nan
df_march = df_march.dropna(subset=['产品处理时长', '研发处理时长'], how='all')

# 95%分位以外的离群值剔除
prod_95th = df_march['产品处理时长'].quantile(0.95)
rd_95th = df_march['研发处理时长'].quantile(0.95)

df_march.loc[df_march['产品处理时长'] > prod_95th, '产品处理时长'] = np.nan
df_march.loc[df_march['研发处理时长'] > rd_95th, '研发处理时长'] = np.nan
df_march = df_march.dropna(subset=['产品处理时长', '研发处理时长'], how='all')

# 计算并输出平均处理时长
avg_prod_time = round(df_march['产品处理时长'].mean(), 2)
avg_rd_time = round(df_march['研发处理时长'].mean(), 2)

print(f"⏱️ 3月份产品平均处理时长: {avg_prod_time} 分钟")
print(f"⏱️ 3月份研发平均处理时长: {avg_rd_time} 分钟\n")


# ==========================================
# 4. 绘制抖动散点图 (严格复刻截图样式)
# ==========================================
plot_data = pd.DataFrame({
    '阶段': ['产品处理时长'] * df_march['产品处理时长'].notna().sum() + 
            ['研发处理时长'] * df_march['研发处理时长'].notna().sum(),
    '时长': list(df_march['产品处理时长'].dropna()) + 
            list(df_march['研发处理时长'].dropna())
})

plt.figure(figsize=(9, 6))

colors = ['#1f77b4', '#2ca02c']  

sns.stripplot(
    x='阶段', 
    y='时长', 
    data=plot_data, 
    hue='阶段',
    jitter=True, 
    alpha=0.8,
    palette=colors,
    size=6,
    legend=False 
)

plt.title('处理时长分布（去除离群值后）', fontsize=14, pad=15)
plt.ylabel('处理时长（分钟）', fontsize=12)
plt.xlabel('') 

legend_elements = [
    mlines.Line2D([0], [0], marker='o', color='w', markerfacecolor='#1f77b4', markersize=8, label='产品处理时长'),
    mlines.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ca02c', markersize=8, label='研发处理时长')
]
plt.legend(handles=legend_elements, loc='upper right')

plt.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.show()