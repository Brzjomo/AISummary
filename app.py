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
    "文档转文稿": "将用户输入的内容转换为纯文本，要求最大程度的保留信息完整，同时转换后的文本要求便于朗读和记忆。转换后的文本不用于阅读，只用于听读。",
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
    "百度文心": {
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
        "models": {
            "文心一言4.0": "ernie-bot-4",
            "文心一言Turbo": "ernie-bot-turbo",
            "文心一言": "ernie-bot"
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
            "Qwen2.5-72B-Instruct": "Qwen/Qwen2.5-72B-Instruct",
            "QwQ-32B-Preview": "Qwen/QwQ-32B-Preview",
            "QVQ-72B-Preview": "Qwen/QVQ-72B-Preview",
            "Qwen2.5-Coder-32B-Instruct": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "DeepSeek-V2.5": "deepseek-ai/DeepSeek-V2.5"
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

def scan_txt_files(directory):
    """扫描目录及其子目录中的所有txt文件"""
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    return txt_files

def process_file(file_path, client, system_prompt, model_id):
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
            stream=False
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"处理文件时出错: {str(e)}"

def save_response(file_path, response):
    """将响应保存为md文件"""
    # 获取原文件所在目录和文件名
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    # 直接将.txt替换为.md
    md_filename = filename.replace('.txt', '.md')
    md_path = os.path.join(directory, md_filename)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(response)
    
    return md_path

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
            
            # 扫描文件
            with st.spinner("正在扫描文件..."):
                txt_files = scan_txt_files(directory)
            
            if not txt_files:
                st.warning("📂 未找到txt文件")
                return
            
            st.info(f"找到 {len(txt_files)} 个txt文件")
            
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 创建一个区域显示处理结果
            results_area = st.empty()
            processed_files = []
            
            for i, file_path in enumerate(txt_files):
                status_text.text(f"⏳ 正在处理: {file_path}")
                
                # 处理文件
                response = process_file(file_path, client, all_prompts[selected_prompt_name], model_id)
                
                # 保存响应
                md_path = save_response(file_path, response)
                processed_files.append((file_path, md_path))
                
                # 更新进度
                progress = (i + 1) / len(txt_files)
                progress_bar.progress(progress)
                
                # 更新处理结果显示
                results_df = pd.DataFrame(
                    processed_files,
                    columns=['源文件', '结果文件']
                )
                results_area.dataframe(
                    results_df,
                    hide_index=True,
                    use_container_width=True
                )
            
            status_text.text("✅ 处理完成！")
            st.success(f"成功处理 {len(txt_files)} 个文件")
            
        except Exception as e:
            st.error(f"❌ 处理过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 