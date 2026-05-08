import pandas as pd
import os
import re

def generate_weekly_report():
    # 1. 输入参数
    file_path = r"C:\Users\Lenovo\.codebuddy\liuruichen\淘福客问题管理\2026日常反馈重点问题汇总表（产品&运营） (18).xlsx"
    target_week = "04.25-04.30"
    target_sheet = "产品内部表新"
    if not os.path.exists(file_path):
        print("❌ 文件路径不存在，请检查后重试。")
        return

    try:
        # 2. 读取数据
        df = pd.read_excel(file_path,sheet_name=target_sheet)
        
        # 3. 筛选本周数据
        weekly_df = df[df['周'] == target_week].copy()
        
        if weekly_df.empty:
            print(f"❌ 未找到周次为 '{target_week}' 的数据。")
            return
# --- 4. 核心逻辑：去重冗余子任务 ---
        # 定义需要比对的五个字段
        compare_cols = ['处理人', '问题模块', '问题类型', '问题原因', '创建时间']
        
        # 检查这五个字段是否全部存在于表格中
        existing_cols = [c for c in compare_cols if c in weekly_df.columns]
        
        # 使用 drop_duplicates 配合 keep='first' 实现你的逻辑：
        # 如果相邻或多行数据的这几个字段完全一致，只保留第一行 (第n行)
        # 注意：这里假设你的子任务是紧跟在主任务后面的
        before_count = len(weekly_df)
        weekly_df = weekly_df.drop_duplicates(subset=existing_cols, keep='first')
        after_count = len(weekly_df)
        
        print(f"💡 已自动过滤掉 {before_count - after_count} 条重复的子任务数据。")
        
        total_count = len(weekly_df)

        # 4. 统计“问题类型”分布
        # 定义属于系统Bug的子类
        bug_types = ['常规bug', '异常bug', '第三方bug']
        
        # 计算系统Bug总数（包含以上三种）
        bug_df = weekly_df[weekly_df['问题类型'].isin(bug_types)]
        bug_total = len(bug_df)
        
        # 计算其他类型的分布（排除Bug类）
        other_types_series = weekly_df[~weekly_df['问题类型'].isin(bug_types)]['问题类型'].value_counts()
        
        # 拼接类型统计字符串
        type_details = []
        for name, count in other_types_series.items():
            type_details.append(f"{name}{count}个")

        # 插入汇总后的系统Bug项（先加入列表，再统一排序）
        type_details.append(f"系统Bug问题{bug_total}个（包括第三方Bug）")

        # 工具函数：从描述字符串末尾抽取数量，用于排序
        def extract_count(text: str) -> int:
            match = re.search(r'(\d+)个', text)
            return int(match.group(1)) if match else 0

        # 按数量降序排序类型明细
        type_details.sort(key=extract_count, reverse=True)

        # 5. 统计“系统Bug”的模块分布
        bug_module_dist = bug_df['问题模块'].value_counts()
        module_details = [f"{mod}{count}个" for mod, count in bug_module_dist.items()]

        # 按数量降序排序模块明细
        module_details.sort(key=extract_count, reverse=True)

        # 6. 按照要求格式输出
        print("\n" + "="*50)
        print(f"本周接收问题 {total_count}个，其中包括：{'、'.join(type_details)}")
        print(f"系统Bug模块分布（包括第三方Bug）：{'、'.join(module_details)}")
        print("="*50)

    except Exception as e:
        print(f"❌ 统计出错: {e}")

if __name__ == "__main__":
    generate_weekly_report()