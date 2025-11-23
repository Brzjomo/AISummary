import streamlit as st
import os
import json
from openai import OpenAI
from pathlib import Path
import pandas as pd

# 预设的system prompts
DEFAULT_PROMPTS = {
    "通用助手": "You are a helpful assistant.",
    "文章总结": "You are an expert at summarizing text. Please provide a concise summary in Chinese.",
    "文档转文稿": "将用户输入的内容转换为文稿，要求最大程度的保留信息完整，但不包含任何md格式，不要使用列表格式。如果有emoji，则转换为相应文本。表示箭头的符号组合，例如：'->'使用'>'表示，'<-'使用'<'表示。",
    "SRT字幕创建概括性笔记": "你是一个AI学习助手，负责根据用户提供的SRT字幕文件生成结构化的Markdown格式笔记或知识总结。请按照以下步骤处理输入，并输出一个便于复习和定位的Markdown文档：\n\n输入解析：\n输入是一个SRT格式的字幕文件，包含多个条目，每个条目由编号、时间戳（格式如：00:00:01,000 --> 00:00:04,000）和文本内容组成。\n解析SRT文件，提取所有条目的时间戳和对应文本。忽略无关格式（如空白行）。\n\n知识点提取与分析：\n分析每个时间戳对应的文本内容，识别关键知识点，包括但不限于：\n核心概念、定义或理论\n重要事实、数据或例子\n步骤、流程或总结性陈述\n任何重复或强调的内容\n使用自然语言处理技术提炼知识点，避免冗余，聚焦于用户可能需要的复习重点。\n\nMarkdown格式组织：\n使用标准的Markdown语法组织内容：\n使用#、##、###等标题级别创建清晰的结构层次\n使用列表（-或1.）呈现知识点\n使用表格（如需要）整理结构化信息\n使用代码块（如需要）展示技术内容\n使用粗体或斜体强调重点\n\n时间戳标记：\n在每个知识点旁边明确标记对应的SRT时间戳，格式为：[开始时间 --> 结束时间]\n如果多个时间戳对应同一知识点，可合并标记或分别注明。\n\n输出要求：\n可以混合其他语言，但主体用中文输出。\n生成完整的Markdown文档，包含以下部分：\n文档标题和简要说明\n按主题或时间顺序组织的知识点总结\n确保输出简洁、准确，覆盖所有重要内容。\n\n示例输出格式：\n<MARKDOWN>\n### 基础理论\n- **知识点1**：简要描述概念内容 [`00:00:01,000 --> 00:00:04,000`]\n- **知识点2**：另一重要概念说明 [`00:00:05,000 --> 00:00:08,000`]\n### 关键技术\n1. **技术要点1**：详细说明 [`00:00:10,000 --> 00:00:15,000`]\n2. **技术要点2**：补充说明 [`00:00:16,000 --> 00:00:20,000`]",
    "SRT转换PotPlayer书签Json": "你是一个AI学习助手，负责根据用户提供的SRT字幕文件生成结构化的JSON格式知识点书签。请按照以下步骤处理输入，并输出一个符合指定JSON格式的知识点书签文件：\n\n输入解析\n- 输入是一个SRT格式的字幕文件，包含多个条目\n- 每个条目由编号、时间戳（格式如：00:00:01,000 --> 00:00:04,000）和文本内容组成\n- 解析SRT文件，提取所有条目的时间戳和对应文本，忽略无关格式（如空白行）\n\n知识点提取与分析\n分析每个时间戳对应的文本内容，识别关键知识点，包括但不限于：\n- 核心概念、定义或理论\n- 重要事实、数据或例子\n- 步骤、流程或总结性陈述\n- 任何重复或强调的内容\n- 技术要点或操作说明\n\n使用自然语言处理技术提炼知识点，要求：\n- 避免冗余，聚焦于用户可能需要的复习重点\n- 每个知识点名称应简洁明了，长度适中\n- 合并相邻时间段的相关内容形成完整知识点\n- 按时间顺序组织知识点\n\n时间戳验证与边界检查\n- 严格基于SRT文件中实际存在的时间戳\n- 只使用字幕条目的开始时间作为知识点时间标记\n- 确保所有时间标记都在SRT文件的时间范围内\n- 不生成超出实际字幕内容范围的时间戳\n- 如果SRT文件有明确的结束时间，确保所有时间标记不超过该时间\n\nJSON格式要求\n输出必须严格遵循以下JSON格式：\n{\n  \"bookmarks_count\": 书签总数,\n  \"bookmarks\": [\n    {\n      \"index\": \"序号\",\n      \"name\": \"知识点名称\",\n      \"time_formatted\": \"HH:MM:SS.mmm\"\n    }\n  ]\n}\n\n时间格式处理\n- 将SRT时间戳格式（00:00:01,000）转换为目标格式（00:00:01.000）\n- 使用开始时间作为该知识点的时间标记\n- 时间格式：HH:MM:SS.mmm（小时:分钟:秒.毫秒）\n\n输出要求\n- 输出必须是完整、有效的JSON格式\n- 总结的知识点必须准确对应SRT文件的时间戳\n- 每个知识点条目必须与其srt内容来源的时间戳对应\n- 严格按时间顺序排列书签条目，严禁调换顺序\n- 索引从\"0\"开始连续编号\n- 知识点名称使用中文，确保准确表达内容\n- 覆盖所有重要知识点，避免遗漏关键信息\n- 不要包含```json标记，直接输出纯JSON内容\n- 确保所有时间戳都在SRT文件的实际时间范围内\n- 不要添加任何额外的解释说明\n\n示例输出\n{\n  \"bookmarks_count\": 2,\n  \"bookmarks\": [\n    {\n    \"index\": \"0\",\n    \"name\": \"ClayBuildUpBrush工具介绍\",\n    \"time_formatted\": \"00:06:34.415\"\n    },\n    {\n    \"index\": \"1\",\n    \"name\": \"通过Tool → Load Tool from Project可以从项目中单独加载工具\",\n    \"time_formatted\": \"00:07:00.427\"\n    }\n  ]\n}\n\n处理流程\n1. 解析SRT文件，提取时间戳和文本内容\n2. 分析文本内容，识别和提炼关键知识点\n3. 合并相关时间段的内容形成完整知识点\n4. 为每个知识点生成简洁的名称\n5. 验证时间戳不超出SRT文件范围\n6. 严格按时间顺序组织并编号\n7. 输出符合格式要求的JSON\n\n请确保输出的JSON文件可以直接用于后续处理，格式正确且内容完整。",
}

# AI提供者配置
DEFAULT_PROVIDERS = {
    "阿里通义": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "通义千问Flash": "qwen-flash",
            "通义千问Plus": "qwen-plus",
            "通义千问3Max": "qwen3-max",
            "通义千问Turbo": "qwen-turbo"
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

def process_file(file_path, client, system_prompt, model_id, temperature=0.7, output_format='txt'):
    """处理单个文件并返回AI响应
    Args:
        file_path: 输入文件路径
        client: OpenAI客户端
        system_prompt: 系统提示词
        model_id: 模型ID
        temperature: 温度参数
        output_format: 输出格式(txt, json等)
    Returns:
        处理结果（根据output_format返回相应格式）
    """
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
        
        response_content = completion.choices[0].message.content
        
        # 如果输出格式是json，则将结果包装成JSON格式
        if output_format.lower() == 'json':
            result_data = {
                'source_file': file_path,
                'original_content_length': len(content),
                'system_prompt': system_prompt,
                'model': model_id,
                'temperature': temperature,
                'response': response_content
            }
            return json.dumps(result_data, ensure_ascii=False, indent=2)
        
        return response_content
    except Exception as e:
        error_msg = f"处理文件时出错: {str(e)}"
        if output_format.lower() == 'json':
            error_data = {
                'source_file': file_path,
                'error': error_msg
            }
            return json.dumps(error_data, ensure_ascii=False, indent=2)
        return error_msg

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
                options=["md", "txt", "srt", "log", "json"],
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
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_button = st.button("🚀 开始处理", type="primary", key="start_process_btn", disabled=not (api_key and directory))
    
    # 仅当选择阿里通义时显示JSONL生成按钮
    if selected_provider == "阿里通义":
        with col2:
            generate_jsonl_button = st.button("📋 生成JSONL", type="secondary", key="generate_jsonl_btn", disabled=not (api_key and directory))
    else:
        generate_jsonl_button = False
    
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
                    response = process_file(file_path, client, all_prompts[selected_prompt_name], model_id, temperature, selected_output_format)

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
    
    # 处理JSONL生成按钮（仅当选择阿里通义时可用）
    if selected_provider == "阿里通义" and generate_jsonl_button:
        try:
            # 导入JSONL生成器
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
            from generate_jsonl import JSONLGenerator
            
            with st.spinner("正在生成JSONL文件..."):
                # 获取当前设置
                model_id = all_providers[selected_provider]["models"][selected_model]
                temperature = get_model_temperature()
                system_prompt = all_prompts[selected_prompt_name]
                
                # 扫描输入文件
                input_files = scan_files_by_extension(directory, selected_file_types)
                
                if not input_files:
                    file_types_str = ", ".join(selected_file_types)
                    st.warning(f"📂 未找到指定类型的文件（{file_types_str}）")
                else:
                    # 生成JSONL文件
                    generator = JSONLGenerator(
                        model=model_id,
                        temperature=temperature,
                        system_prompt=system_prompt,
                        input_dir=directory,
                        input_extensions=selected_file_types,
                        output_dir=directory,
                        output_extension=selected_file_types[0] if selected_file_types else 'txt'
                    )
                    
                    output_files = generator.generate_jsonl(base_filename='batch_requests')
                    
                    if output_files:
                        st.success(f"✅ JSONL文件生成完成！")
                        for output_file in output_files:
                            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                            st.info(f"📄 {os.path.basename(output_file)} - {file_size_mb:.2f}MB")
                        
                        st.markdown("---")
                        st.subheader("JSONL文件规范校验")
                        st.success("✓ UTF-8编码")
                        st.success("✓ 每行一个JSON对象")
                        st.success(f"✓ 模型：{model_id}")
                        st.success(f"✓ 温度：{temperature}")
                        st.info(f"ℹ️ 总请求数：{len(input_files)}")
                        if len(output_files) > 1:
                            st.warning(f"⚠️ 文件过大，已自动分割为 {len(output_files)} 个文件")
                    else:
                        st.error("❌ 生成JSONL文件失败")
        
        except Exception as e:
            st.error(f"❌ 生成JSONL过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 