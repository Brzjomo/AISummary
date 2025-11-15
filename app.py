import streamlit as st
import os
import json
from openai import OpenAI
from pathlib import Path
import pandas as pd

# 预设的system prompts
DEFAULT_PROMPTS = {
    "文章总结": "You are an expert at summarizing text. Please provide a concise summary in Chinese.",
    "代码分析": "You are a code review expert. Please analyze the code and provide suggestions.",
    "通用助手": "You are a helpful assistant.",
    "文档转文稿": "将用户输入的内容转换为文稿，要求最大程度的保留信息完整，但不包含任何md格式，不要使用列表格式。如果有emoji，则转换为相应文本。表示箭头的符号组合，例如：'->'使用'>'表示，'<-'使用'<'表示。",
}

# AI提供者配置
DEFAULT_PROVIDERS = {
    "阿里通义": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "通义千问Plus": "qwen-plus",
            "通义千问Turbo": "qwen-turbo",
            "通义千问Max": "qwen-max"
        }
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": {
            "DeepSeek Chat": "deepseek-chat"
        }
    },
    "智谱AI": {
        "base_url": "https://open.bigmodel.cn/api/paas/v3/model-api",
        "models": {
            "智谱ChatGLM Turbo": "chatglm_turbo",
            "智谱ChatGLM Pro": "chatglm_pro",
            "智谱ChatGLM Std": "chatglm_std"
        }
    },
    "硅基流动": {
        "base_url": "https://api.siliconflow.cn/v1",
        "models": {
            "Hunyuan-A13B-Instruct": "tencent/Hunyuan-A13B-Instruct",
            "Qwen3-Next-80B-A3B-Instruct": "Qwen/Qwen3-Next-80B-A3B-Instruct",
            "Qwen3-Omni-30B-A3B-Thinking": "Qwen/Qwen3-Omni-30B-A3B-Thinking",
            "Qwen3-Omni-30B-A3B-Instruct": "Qwen/Qwen3-Omni-30B-A3B-Instruct",
            "DeepSeek-V3": "deepseek-ai/DeepSeek-V3"
        }
    }
}

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {'custom_prompts': {}, 'providers': {}, 'provider_keys': {}}

def save_config(config):
    """保存配置文件"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_custom_prompts():
    """加载保存的自定义prompts"""
    config = load_config()
    return config.get('custom_prompts', {})

def save_custom_prompts(prompts):
    """保存自定义prompts"""
    config = load_config()
    config['custom_prompts'] = prompts
    save_config(config)

def scan_files_by_extension(directory, extensions):
    """扫描目录及其子目录中指定扩展名的文件
    Args:
        directory: 目录路径
        extensions: 扩展名列表，如 ['txt', 'srt']（不包含点）
    """
    matched_files = []
    extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in extensions:
                matched_files.append(os.path.join(root, file))
    return matched_files

def process_file(file_path, client, system_prompt, model_id, temperature=0.7):
    """处理单个文件并返回AI响应"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': content}
            ],
            temperature=temperature,
            stream=False
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"处理文件时出错: {str(e)}"

def save_response(file_path, response, output_format='md'):
    """将响应保存为指定格式的文件
    Args:
        file_path: 原文件路径
        response: AI响应内容
        output_format: 输出文件格式，如 'md', 'txt', 'srt' 等（不包含点）
    """
    # 获取原文件所在目录和文件名
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # 获取原文件的扩展名（如 .txt, .srt 等）
    file_ext = os.path.splitext(filename)[1]
    file_name_without_ext = os.path.splitext(filename)[0]
    
    # 如果没有包含点，自动添加
    if not output_format.startswith('.'):
        output_format = f'.{output_format}'
    
    # 生成输出文件名
    output_filename = file_name_without_ext + output_format
    output_path = os.path.join(directory, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response)
    
    return output_path

def load_providers():
    """加载AI提供者配置"""
    config = load_config()
    providers = config.get('providers', {})
    # 合并默认提供者和自定义提供者
    all_providers = {**DEFAULT_PROVIDERS, **providers}
    return all_providers

def save_provider(name, base_url, models):
    """保存自定义AI提供者"""
    config = load_config()
    if 'providers' not in config:
        config['providers'] = {}
    
    config['providers'][name] = {
        "base_url": base_url,
        "models": models
    }
    save_config(config)

def get_provider_api_key(provider_name):
    """获取提供者的API key"""
    config = load_config()
    provider_keys = config.get('provider_keys', {})
    return provider_keys.get(provider_name, '')

def save_provider_api_key(provider_name, api_key):
    """保存提供者的API key"""
    config = load_config()
    if 'provider_keys' not in config:
        config['provider_keys'] = {}
    config['provider_keys'][provider_name] = api_key
    save_config(config)

def get_model_temperature():
    """获取模型温度设置"""
    config = load_config()
    model_settings = config.get('model_settings', {})
    return model_settings.get('temperature', 0.7)

def save_model_temperature(temperature):
    """保存模型温度设置"""
    config = load_config()
    if 'model_settings' not in config:
        config['model_settings'] = {}
    config['model_settings']['temperature'] = temperature
    save_config(config)

def main():
    st.set_page_config(page_title="AI批量总结助手", layout="wide")
    
    # 侧边栏配置
    with st.sidebar:
        st.title("⚙️ 配置")
        
        # AI提供者配置
        st.subheader("AI提供者设置")
        
        # 加载所有提供者
        all_providers = load_providers()
        selected_provider = st.selectbox(
            "选择AI提供者",
            options=list(all_providers.keys()),
            help="选择要使用的AI服务提供商"
        )
        
        # 选择模型
        provider_config = all_providers[selected_provider]
        selected_model = st.selectbox(
            "选择模型",
            options=list(provider_config["models"].keys()),
            help="选择要使用的AI模型"
        )
        
        # API Key设置
        current_api_key = get_provider_api_key(selected_provider)
        api_key = st.text_input(
            f"{selected_provider} API Key", 
            value=current_api_key,
            type="password",
            help=f"输入{selected_provider}的API密钥"
        )
        
        if api_key != current_api_key:
            save_provider_api_key(selected_provider, api_key)
            st.success("API Key已保存")
        
        # 模型温度设置
        st.divider()
        st.subheader("模型参数设置")
        
        current_temperature = get_model_temperature()
        temperature = st.slider(
            "模型温度",
            min_value=0.0,
            max_value=2.0,
            value=current_temperature,
            step=0.1,
            help="温度值控制输出的随机性。0表示确定性输出（最稳定），2表示高随机性（最创意）。建议值：\n- 总结：0.3-0.5（较低）\n- 创意写作：1.0-1.5（较高）\n- 常规任务：0.7-0.8（适中）"
        )
        
        if temperature != current_temperature:
            save_model_temperature(temperature)
            st.success(f"温度已设置为 {temperature}")
        
        # 文件类型选择
        st.divider()
        st.subheader("文件类型选择")
        
        file_type_option = st.radio(
            "选择处理方式",
            options=["预设类型", "自定义类型"],
            horizontal=True,
            help="选择使用预设的文件类型或自定义",
            key="file_type_option"
        )
        
        if file_type_option == "预设类型":
            selected_file_types = st.multiselect(
                "选择要处理的文件类型",
                options=["txt", "srt", "md", "log"],
                default=["txt"],
                help="选择一个或多个文件类型",
                key="preset_file_types"
            )
        else:
            custom_types_input = st.text_input(
                "输入文件扩展名（逗号分隔）",
                value="txt,srt",
                placeholder="例：txt,srt,md,log",
                help="输入要处理的文件扩展名，用逗号分隔",
                key="custom_file_types"
            )
            selected_file_types = [t.strip() for t in custom_types_input.split(',') if t.strip()]
        
        if not selected_file_types:
            st.warning("请选择至少一个文件类型")
            selected_file_types = ["txt"]  # 默认值
        
        # 输出格式选择
        st.divider()
        st.subheader("输出格式设置")
        
        output_format_option = st.radio(
            "选择输出格式方式",
            options=["预设格式", "自定义格式"],
            horizontal=True,
            help="选择使用预设的输出格式或自定义",
            key="output_format_option"
        )
        
        if output_format_option == "预设格式":
            selected_output_format = st.selectbox(
                "选择输出文件格式",
                options=["md", "txt", "srt", "log"],
                index=0,
                help="所有处理结果都将保存为选中的格式",
                key="preset_output_format"
            )
        else:
            custom_output_format = st.text_input(
                "输入输出文件扩展名",
                value="md",
                placeholder="例：md, txt, srt",
                help="输入输出文件的扩展名（不包含点）",
                key="custom_output_format"
            )
            selected_output_format = custom_output_format.strip().lstrip('.')
        
        if not selected_output_format:
            st.warning("请输入有效的输出格式")
            selected_output_format = "md"  # 默认值
        
        st.markdown("---")

        # 添加新的提供者
        with st.expander("添加新的AI提供者"):
            new_provider_name = st.text_input("提供者名称")
            new_provider_base_url = st.text_input("Base URL")
            
            # 初始化session state
            if 'new_models' not in st.session_state:
                st.session_state.new_models = {}
            
            # 显示当前已添加的模型
            if st.session_state.new_models:
                st.write("已添加的模型：")
                for model_name, model_id in st.session_state.new_models.items():
                    st.write(f"- {model_name}: {model_id}")
            
            # 动态模型配置
            st.subheader("配置模型")
            
            col1, col2 = st.columns(2)
            with col1:
                model_name = st.text_input("模型显示名称")
            with col2:
                model_id = st.text_input("模型ID")
            
            if st.button("添加模型", key="add_model_btn") and model_name and model_id:
                st.session_state.new_models[model_name] = model_id
                st.success(f"已添加模型: {model_name}")
                st.rerun()
            
            # 清除模型按钮
            if st.session_state.new_models and st.button("清除所有模型", type="secondary", key="clear_models_btn"):
                st.session_state.new_models = {}
                st.rerun()
            
            # 保存提供者按钮
            if st.button("保存提供者", type="primary", key="save_provider_btn"):
                if new_provider_name and new_provider_base_url and st.session_state.new_models:
                    save_provider(new_provider_name, new_provider_base_url, st.session_state.new_models)
                    # 清空session state
                    st.session_state.new_models = {}
                    st.success("保存成功！")
                    st.rerun()
                else:
                    st.warning("请填写完整的提供者信息并至少添加一个模型")
        
        st.markdown("---")
        
        # Prompt管理
        st.subheader("Prompt管理")
        
        # 加载自定义prompts
        custom_prompts = load_custom_prompts()
        all_prompts = {**DEFAULT_PROMPTS, **custom_prompts}
        
        # Prompt选择
        selected_prompt_name = st.selectbox(
            "选择System Prompt",
            options=list(all_prompts.keys()),
            help="选择预设的prompt或添加自定义prompt"
        )
        selected_prompt = all_prompts[selected_prompt_name]
        
        with st.expander("查看当前Prompt内容"):
            st.text_area(
                "当前System Prompt",
                value=selected_prompt,
                height=100,
                disabled=True
            )
        
        # 删除自定义prompt的按钮
        if selected_prompt_name in custom_prompts:
            if st.button(f"🗑️ 删除 '{selected_prompt_name}'", type="secondary", key=f"delete_prompt_{selected_prompt_name}"):
                del custom_prompts[selected_prompt_name]
                save_custom_prompts(custom_prompts)
                st.success(f"已删除 '{selected_prompt_name}'")
                st.rerun()
        
        # 添加新的prompt
        with st.expander("添加新的Prompt"):
            new_prompt_name = st.text_input(
                "Prompt名称",
                help="为新的prompt起一个名字"
            )
            new_prompt_content = st.text_area(
                "Prompt内容",
                height=100,
                help="输入prompt的具体内容"
            )
            
            if st.button("💾 保存", type="primary", key="save_prompt_btn"):
                if new_prompt_name and new_prompt_content:
                    if new_prompt_name in DEFAULT_PROMPTS:
                        st.error("不能覆盖预设的Prompt")
                    else:
                        custom_prompts[new_prompt_name] = new_prompt_content
                        save_custom_prompts(custom_prompts)
                        st.success("保存成功！")
                        st.rerun()
                else:
                    st.warning("请填写完整的Prompt信息")
    
    # 主界面
    st.title("📝 AI批量总结助手")
    st.markdown("""
    ### 使用说明
    1. 在侧边栏配置API Key和选择合适的Prompt
    2. 输入要处理的文件目录路径
    3. 点击开始处理
    
    系统将自动：
    - 扫描目录下所有txt文件
    - 使用AI处理文件内容
    - 将结果保存为同名的md文件
    """)
    
    # 目录选择
    directory = st.text_input(
        "📁 处理目录",
        help="输入要处理的目录的完整路径，系统将处理该目录下所有的txt文件"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        start_button = st.button("🚀 开始处理", type="primary", key="start_process_btn", disabled=not (api_key and directory))
    
    if not api_key:
        st.warning("⚠️ 请先在侧边栏配置API Key")
    if not directory:
        st.warning("⚠️ 请输入要处理的目录路径")
    
    if start_button:
        try:
            with st.spinner("正在初始化AI客户端..."):
                client = OpenAI(
                    api_key=api_key,
                    base_url=all_providers[selected_provider]["base_url"]
                )
            
            # 获取选中的模型ID
            model_id = all_providers[selected_provider]["models"][selected_model]
            
            # 获取温度设置
            temperature = get_model_temperature()
            
            # 扫描文件
            with st.spinner("正在扫描文件..."):
                matched_files = scan_files_by_extension(directory, selected_file_types)
            
            if not matched_files:
                file_types_str = ", ".join(selected_file_types)
                st.warning(f"📂 未找到指定类型的文件（{file_types_str}）")
                return
            
            file_types_str = ", ".join(selected_file_types)
            st.info(f"找到 {len(matched_files)} 个文件 ({file_types_str})，输出格式: .{selected_output_format}，使用温度值: {temperature}")
            
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 创建一个区域显示处理结果（包含状态）
            results_area = st.empty()
            processed_files = []
            skipped_count = 0

            for i, file_path in enumerate(matched_files):
                status_text.text(f"⏳ 正在处理: {file_path}")

                # 生成对应的输出文件路径
                file_dir = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                file_name_without_ext = os.path.splitext(file_name)[0]
                output_filename = file_name_without_ext + f'.{selected_output_format}'
                output_path = os.path.join(file_dir, output_filename)

                # 如果已存在同名输出文件，则跳过处理
                if os.path.exists(output_path):
                    skipped_count += 1
                    processed_files.append((file_path, output_path, '跳过-已存在'))
                else:
                    # 处理文件
                    response = process_file(file_path, client, all_prompts[selected_prompt_name], model_id, temperature)

                    # 保存响应，使用指定的输出格式
                    output_path = save_response(file_path, response, selected_output_format)
                    processed_files.append((file_path, output_path, '已处理'))

                # 更新进度
                progress = (i + 1) / len(matched_files)
                progress_bar.progress(progress)

                # 更新处理结果显示
                results_df = pd.DataFrame(
                    processed_files,
                    columns=['源文件', '结果文件', '状态']
                )
                results_area.dataframe(
                    results_df,
                    hide_index=True,
                    use_container_width=True
                )
            
            status_text.text("✅ 处理完成！")
            st.success(f"完成：共扫描 {len(matched_files)} 个文件，已处理 {len(matched_files)-skipped_count} 个，跳过 {skipped_count} 个（已存在同名md）")
            
        except Exception as e:
            st.error(f"❌ 处理过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 