# AI-anxiety

AI 焦虑多维度自我反思与行动支持 MVP（Streamlit）。

## 量表结构
共 4 个维度（21 题），每题 1–5 分：
- L 维度：学习焦虑（L1–L8）
- J 维度：工作替代担忧（J1–J6）
- S 维度：社会技术风险担忧（S1–S4）
- C 维度：类人 AI 构型恐惧（C1–C3）

填写后会输出 4 维度得分报告，并选择其中一个维度进入后续对话与干预流程。

## 运行
```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```

## LLM 环境变量（可选）
支持 OpenAI-compatible `/v1/chat/completions`。未配置时会自动使用 Mock。

本项目仅通过环境变量读取 LLM 配置：
```bash
export LLM_BASE_URL="https://api.example.com"
export LLM_API_KEY="YOUR_API_KEY"
export LLM_MODEL="your-model-name"
export LLM_TIMEOUT="30"
```

Streamlit Cloud Secrets 示例（不含真实 key）：
```toml
[secrets]
LLM_BASE_URL = "https://api.example.com"
LLM_API_KEY = "YOUR_API_KEY"
LLM_MODEL = "your-model-name"
```

## Deploy
### Streamlit Community Cloud（推荐）
1) 将仓库推到 GitHub。  
2) 在 Streamlit Community Cloud 里连接 GitHub，选择仓库和分支。  
3) 设置 Main file path 为 `app_streamlit.py`。  
4) 在 “Secrets” 中填入 `LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`（不填则使用 Mock）。  
5) 点击 Deploy，完成后访问生成的公开 URL。

### Render（备选）
1) 在 Render 新建 Web Service，连接 GitHub 仓库。  
2) 选择分支并设置 Start Command：  
   `streamlit run app_streamlit.py --server.port $PORT --server.headless true`  
3) 配置环境变量 `LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`。  
4) 部署完成后访问服务 URL。

## Security
不要提交任何 API key 或敏感信息到仓库。  
Secrets/环境变量应存放在 Streamlit Cloud Secrets 或 Render/Railway 的环境变量设置中。  

## 本地运行提示（受限环境）
如果在受限环境无法绑定端口，请在本机终端运行，并使用 polling 文件监听：  
`STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll streamlit run app_streamlit.py --server.port 8505 --server.headless true`
