import os
import re
import sys
import json
import yaml
from google import genai
import utils

# 当前脚本所在目录作为基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    """读取 YAML 配置文件"""
    config_path = os.path.join(BASE_DIR, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_skill_prompt(skill_name):
    """读取 Markdown 提示词模板"""
    skill_path = os.path.join(BASE_DIR, f"{skill_name}.md")
    with open(skill_path, "r", encoding="utf-8") as f:
        return f.read()

def load_and_preprocess_chat(input_path):
    """读取并预处理聊天记录"""
    if not os.path.exists(input_path):
        print(f"❌ 错误：找不到文件 {input_path}")
        return None
    with open(input_path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    return raw_content

def extract_json_from_text(text):
    """从大模型返回的文本中提取纯 JSON 字符串"""
    if "```json" in text:
        return text.split("```json")[-1].split("```")[0].strip()
    return text.strip()

def call_gemini_with_fallback(client, model_ids, final_prompt):
    """
    尝试调用多个模型，遇到 429 配额错误时自动切换到下一个模型
    """
    last_error = None
    for idx, model_id in enumerate(model_ids):
        try:
            print(f"\n🚀 正在尝试模型 [{idx+1}/{len(model_ids)}]: {model_id}")
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=final_prompt
            )

            full_text = ""
            print("\n" + "🧠 " + "="*15 + " AI 实时分析中 " + "="*15)
            for chunk in response_stream:
                sys.stdout.write(chunk.text)
                sys.stdout.flush()
                full_text += chunk.text

            print("\n" + "="*44 + "\n")
            return extract_json_from_text(full_text)

        except genai.errors.ClientError as e:
            last_error = e
            error_code = getattr(e, 'code', None)
            # 从错误消息中判断是否配额耗尽
            if error_code == 429 or 'RESOURCE_EXHAUSTED' in str(e) or 'Quota exceeded' in str(e):
                print(f"⚠️ 模型 {model_id} 额度已用完，正在切换下一个模型...")
                continue
            else:
                # 其他 ClientError 直接抛出
                raise

    # 所有模型都尝试过了
    print(f"\n❌ 所有模型额度均已用完，最后错误信息：")
    print(last_error)
    return None

def run_task():
    # 1. 加载配置
    config = load_config()

    # 2. 设置代理
    os.environ["http_proxy"] = config["proxy"]["http"]
    os.environ["https_proxy"] = config["proxy"]["https"]

    # 3. 读取聊天记录
    input_file = config["paths"]["input_file"]
    chat_content = load_and_preprocess_chat(input_file)
    if not chat_content: return

    # 4. 组装 Prompt
    prompt_template = load_skill_prompt("QuestionSkills")
    final_prompt = prompt_template.replace("{{content}}", chat_content)

    # 5. 初始化 AI 客户端
    client = genai.Client(api_key=config["gemini"]["api_key"])

    # 6. 获取模型列表并调用（支持自动切换）
    model_ids = config["gemini"].get("model_ids", [config["gemini"].get("model_id", "gemini-3.1-pro-preview")])
    current_data_text = call_gemini_with_fallback(client, model_ids, final_prompt)
    if not current_data_text:
        print("\n❌ 无法获取 AI 分析结果，请检查模型配额或网络连接。")
        return
    '''
    # 6. 交互微调循环
    while True:
        print("\n" + "="*30)
        print("📊 当前 AI 提取的结果预览：")
        print(current_data_text)
        print("="*30)
        
        feedback = input("\n💡 如果满意请按 'y' 写入 Excel；\n💡 如果需要微调，请直接输入你的意见：\n>>> ").strip()

        if not feedback:
            continue
        if feedback.lower() == 'y':
            break
        if len(feedback) <= 2:
            confirm = input(f"❓ 你的微调意见是【{feedback}】，确认吗？(y/n): ").strip().lower()
            if confirm != 'y': continue 

        print(f"🔄 正在根据意见【{feedback}】进行微调...")
        try:
            refine_prompt = f"这是之前的JSON数据：\n{current_data_text}\n\n请根据以下意见微调这个JSON：{feedback}。只返回纯JSON数组格式。"
            f_resp = client.models.generate_content(model=model_id, contents=refine_prompt)
            current_data_text = extract_json_from_text(f_resp.text)
        except Exception as e:
            print(f"❌ AI 微调失败，错误信息: {e}")
    '''
   # 7. 写入 Excel
    try:
        # 开启宽容模式解析 JSON
        data_list = json.loads(current_data_text, strict=False)
        base_output_path = os.path.join(BASE_DIR, config["paths"]["output_file"])
        max_files = config["settings"]["max_files"]
        
        # 在这里直接定义表头，与 md 提示词里的字段保持绝对一致
        headers = [
            "问题描述", "处理进度", "反馈人", "处理人", "问题模块", 
            "问题类型", "问题原因", "反馈时间", "产品接收时间", 
            "产品转研发时间", "研发反馈修复时间", "创建时间"
        ]
        
        new_file = utils.get_new_filename(base_output_path, max_files)
        utils.save_to_excel(data_list, new_file, headers)
        
        print(f"\n✅ 成功生成新文件：{new_file}")
        print(f"共写入 {len(data_list)} 条记录")
        """
        # 写入飞书多维表格
        try:
            feishu_config = config.get("feishu", {})
            if feishu_config.get("app_id") and feishu_config.get("app_secret"):
                utils.save_to_bitable(data_list, headers, feishu_config)
            else:
                print("⚠ 未配置飞书信息，跳过多维表格写入（请在 config.yaml 中添加 feishu 配置）")
        except Exception as e:
            print(f"⚠ 飞书多维表格写入失败: {e}")
        """
    except Exception as e:
        print(f"\n❌ JSON 解析或写入失败，错误信息：{e}")
        print("👇 这是 AI 返回的原始问题文本，你可以检查一下是哪里格式乱了：")
        print(current_data_text)
        

if __name__ == "__main__":
    run_task()