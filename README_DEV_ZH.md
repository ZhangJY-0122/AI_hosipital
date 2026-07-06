# AI Hospital 二次开发说明

本文档记录本地复现、DeepSeek 接入、病例扩展和上传 GitHub 的最小流程。

## 1. 环境准备

```cmd
cd /d D:\project_code\AI_Hospital-main
python -m pip install -r requirements.txt
```

Windows 下建议运行前开启 UTF-8 模式：

```cmd
set "PYTHONUTF8=1"
```

## 2. 使用 DeepSeek API

本项目的 GPT 引擎使用 OpenAI SDK。DeepSeek 兼容 OpenAI API，因此可以复用 `OPENAI_API_KEY` 和 `OPENAI_API_BASE`。

```cmd
cd /d D:\project_code\AI_Hospital-main\src
set "OPENAI_API_KEY=你的DeepSeek_API_KEY"
set "OPENAI_API_BASE=https://api.deepseek.com/v1"
set "PYTHONUTF8=1"
```

先测试 API 是否可用：

```cmd
python -c "from openai import OpenAI; import os; c=OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_API_BASE')); r=c.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'hi'}], max_tokens=20); print(r.choices[0].message.content)"
```

## 3. 最终病例集复现

```cmd
cd /d D:\project_code\AI_Hospital-main\src
scripts\run_deepseek_final.cmd
```

输出文件：

```text
src\outputs\dialog_history_iiyi\dialog_history_deepseek_final.jsonl
```

## 4. 增加更多病例

`run.py` 期望 `--patient_database` 指向一个 JSON 数组，每个病例至少包含：

```json
[
  {
    "id": 1001,
    "profile": "患者扮演提示词",
    "medical_record": {
      "一般资料": "...",
      "主诉": "...",
      "现病史": "...",
      "辅助检查": "...",
      "诊断结果": "..."
    }
  }
]
```

常见坑：

- 文件必须是 UTF-8，最好不要带 BOM。
- 最外层必须是数组 `[...]`，不能是单个对象 `{...}`。
- `profile` 用来模拟患者回答，`medical_record` 用来给检查员/报告员查询。

新增或整理病例后，先运行格式校验：

```cmd
cd /d D:\project_code\AI_Hospital-main\src
python scripts\validate_patients.py data\patients.json
```

## 5. 上传到自己的 GitHub

如果当前目录还不是 Git 仓库：

```cmd
cd /d D:\project_code\AI_Hospital-main
git init
git add .
git commit -m "Improve AI Hospital reproduction workflow"
```

在 GitHub 创建一个空仓库后，绑定远程地址：

```cmd
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

注意不要提交真实 API Key。建议只提交 `.env.example`，不要提交 `.env`。
