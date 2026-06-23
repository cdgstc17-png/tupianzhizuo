# fashion-image-prep-web

一个可直接部署到 Streamlit Community Cloud 的服装图片前期素材工具。
默认使用不调用 OpenAI API 的免费手动模式，也保留可选的 API 自动模式。

用户上传一张衣服图片后，网页会：

- 等比例制作 3 种白底参考图，不拉伸、不裁切衣服主体
- 免费模式下整理用户手动粘贴的 ChatGPT 输出，不产生 API 费用
- API 模式下生成压缩图并使用 OpenAI 多模态模型自动分析
- 把完整结果按固定标题拆分成 6 个文本文件
- 生成使用说明并打包成 ZIP 下载

本项目不会调用 ComfyUI，不会自动生成视频，不使用数据库、用户系统或任务队列。

## 生成的 ZIP 内容

```text
original.png
cloth_1x1.png
cloth_9x16.png
cloth_comfy_input.png
all_prompts.txt
clothing_analysis.txt
script.txt
scene_analysis.txt
character_9view_prompt.txt
garment_9view_prompt.txt
motion_prompts.txt
README.txt
```

API 自动模式会额外包含 `compressed_for_gpt.jpg`。

## 两种处理模式

### 免费手动模式（默认）

免费模式不读取 API Key，也不会调用 OpenAI API：

1. 用户先把衣服图片发送给 ChatGPT。
2. 让 ChatGPT 按本项目的 6 个固定标题生成完整内容。
3. 在网页上传同一张图片。
4. 把 ChatGPT 的完整输出粘贴到“粘贴 ChatGPT 输出内容”文本框。
5. 点击“生成素材包”。

网页只会处理图片、保存粘贴文本、拆分 TXT 并打包 ZIP，不产生 OpenAI API 费用。

### API 自动模式（可选）

API 模式会把长边不超过 1024px 的压缩图片发送给 OpenAI，并自动获取文字内容。
每张新图片在当前浏览器会话内只调用一次 API，但会产生相应 API 费用。

## 完全通过网页部署到 Streamlit Cloud

下面的操作不需要本地终端。

### 第一步：创建 GitHub 仓库

1. 登录 [GitHub](https://github.com/)。
2. 点击右上角 `+`，选择 `New repository`。
3. 仓库名称填写 `fashion-image-prep-web`。
4. 建议选择 `Private`，然后点击 `Create repository`。
5. 在仓库页面点击 `uploading an existing file`，把本项目中的文件和文件夹上传。

建议把 `app.py`、`requirements.txt` 等文件直接放在仓库根目录。  
`.streamlit/secrets.toml.example` 只是示例，不包含真实密钥，可以上传。

### 第二步：在 Streamlit Community Cloud 创建应用

1. 打开 [Streamlit Community Cloud](https://share.streamlit.io/) 并使用 GitHub 登录。
2. 点击 `Create app` 或 `New app`。
3. 选择刚创建的 GitHub 仓库和分支。
4. Main file path 填写 `app.py`。
5. 暂时不要提交，先打开应用的 `Advanced settings`。
6. Python version 建议选择 `3.12`。

如果你把整个 `fashion-image-prep-web` 文件夹放进了仓库，而不是把文件放在仓库根目录，那么 Main file path 应填写：

```text
fashion-image-prep-web/app.py
```

### 第三步：按需配置 OpenAI Secrets

只使用免费手动模式时，不需要配置任何 Secrets。

如需使用 API 自动模式，在 Streamlit Cloud 的 `Advanced settings` → `Secrets`
中填写：

```toml
OPENAI_API_KEY = "你的 OpenAI API Key"
OPENAI_MODEL = "gpt-5.5"
```

然后保存并部署。未配置 API Key 时，免费模式仍可正常使用。

Streamlit Cloud 会自动读取与 `app.py` 同目录的 `requirements.txt`，安装
Streamlit、Pillow 和 OpenAI Python SDK，不需要在网页服务器上手动安装。

请不要：

- 把真实 API Key 写进 `app.py`
- 把真实 API Key 上传到 GitHub
- 把示例文件改成包含真实 Key 的文件再提交

如果你的 OpenAI 账户不能使用默认模型，只需在 Secrets 中把 `OPENAI_MODEL` 改成账户可用、支持图片输入的模型名称，无需修改代码。

## 网页使用方法

### 免费手动模式

1. 打开部署后的 Streamlit 页面。
2. 保持默认的“免费手动模式”。
3. 先把衣服图片发给 ChatGPT，获得包含 6 个固定标题的输出。
4. 上传同一张 JPG、JPEG、PNG 或 WEBP 图片。
5. 把 ChatGPT 输出粘贴到大文本框。
6. 点击“生成素材包”，然后下载 ZIP。

### API 自动模式

1. 切换为“API 自动模式”。
2. 上传衣服图片。
3. 点击“生成素材包”。
4. 等待一次 OpenAI API 分析完成，然后下载 ZIP。

同一张图片在同一个浏览器会话中会缓存 API 模式结果。重复点击时会直接
复用，不会再次请求 API。免费模式按“图片 + 粘贴文本”缓存结果。

## 修改提示词

所有 GPT 指令都在：

```text
templates/all_in_one_prompt.txt
```

可以直接在 GitHub 网页中编辑这个文件。请逐字保留下面 6 个固定标题，否则自动拆分会失败：

```text
【1. 服装分析】
【2. 对镜自拍视频脚本】
【3. 脚本画面分析】
【4. 人物九视图生成提示词】
【5. 服装九视图生成提示词】
【6. Wan2.2 人物动作提示词】
```

## 费用与隐私

- 免费手动模式不调用 OpenAI API，不会把图片或粘贴文本发送给 OpenAI。
- API 自动模式每张新图片只调用一次 OpenAI API。
- API 模式费用取决于所选模型、图片大小和输出长度。
- 只有 API 模式会把压缩图片发送给 OpenAI。
- 本项目不使用数据库；生成结果保存在当前 Streamlit 会话内存中，并通过浏览器下载。

## 常见问题

### 页面提示没有配置 OPENAI_API_KEY

免费模式不需要 API Key。只有选择 API 自动模式时，才需要打开 Streamlit
Cloud 应用设置，在 `Secrets` 中添加 Key。

### 提示模型不存在或无权访问

把 Streamlit Secrets 中的 `OPENAI_MODEL` 改成你的 OpenAI API 账户可用且支持图片输入的模型。

### GPT 输出没有被正确拆分

完整输出仍会保存在 `all_prompts.txt`。检查模型是否保留了 6 个固定标题，也可以加强 `templates/all_in_one_prompt.txt` 中的格式要求。

### ZIP 会永久保存在服务器吗

不会。项目没有数据库，ZIP 在内存中生成，供当前浏览器会话下载。

## 部署前检查清单

- `app.py` 和 `requirements.txt` 位于同一目录
- `templates/all_in_one_prompt.txt` 已上传
- `.streamlit/secrets.toml.example` 中没有真实密钥
- 如只使用免费模式，可以不配置任何 Secrets
- 如需 API 自动模式，Streamlit Cloud Secrets 中需配置 `OPENAI_API_KEY`
- Main file path 指向正确的 `app.py`
- Python version 选择 3.12
