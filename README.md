

# Obsidian Hugo Upload With Python

一个技术含量不高的脚本，用来配合我的 Hugo 发布流程。

## 功能

具体来说，它做了这么几件事：

- 获取 Obsidian 博客文件夹下最新的 Markdown 文件。
- 检测图片文件并上传到一个 S3-compatible 的存储服务中。
- 执行一系列的正则替换，包括：
  - 图片链接替换（由于我写了一个很好的 `render-image.html`，所以我的工作变得很轻松）
  - Wiki 双链 `[[]]` 替换为 `relref` 短代码
  - GitHub Alert 正则替换为 Hugo 短代码
- 将处理后的文件放入我的博客文件夹下。

## 使用

如果您是 Hugo Theme Efímero 的使用者，并且您的 Obsidian 博客文件夹和 Hugo 博客文件夹都在本地，且您的图片附件位置相对固定，您应该可以直接使用，否则您需要一定的改动。如果您对改动有疑问，可以提 issue，我或许能帮上忙。

- 下载本项目源码
- 把源码解压并且放到一个合适的位置
- 进入项目文件夹，运行 `init.sh` 脚本（对于类 Unix 系统）或 `init.bat`（对于 Windows 系统）
- 将 `example.toml` 重命名为 `config.toml`，然后按照说明进行配置。
- 运行 `main.py` 即可。

## 许可证

MIT licence.
