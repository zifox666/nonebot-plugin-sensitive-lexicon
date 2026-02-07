<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-sensitive-lexicon ✨
[![LICENSE](https://img.shields.io/github/license/zifox666/nonebot-plugin-sensitive-lexicon.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-sensitive-lexicon.svg)](https://pypi.python.org/pypi/nonebot-plugin-sensitive-lexicon)
[![python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/zifox666/nonebot-plugin-sensitive-lexicon/master.svg)](https://results.pre-commit.ci/latest/github/zifox666/nonebot-plugin-sensitive-lexicon/master)

</div>

## 📖 介绍

通过 [违禁词词库](https://github.com/konsheng/Sensitive-lexicon/) 审核群消息, 触犯规则后自动禁言或踢出, 可选禁止重新加群

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-sensitive-lexicon --upgrade

</details>

<details open>
<summary>Docker 安装</summary>

如果你已经拉取项目到了本地 可以直接使用 `docker compose up -d`

或者直接拉取 （注意创建 .env 和 data 目录）

```bash
docker run -d `
  --name sensitive-lexicon-bot `
  --restart unless-stopped `
  -p 8170:8170 `
  -v ./data:/app/data `
  --env-file .env `
  ghcr.io/zifox666/nonebot-plugin-sensitive-lexicon:latest
```

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项  | 必填 | 默认值 |    说明     |
| :-----: |:--:|:---:|:---------:|
| KICK_COUNT | 否  |  5  | 触犯几次规则后踢人 |
| MUTE_DAY | 否  |  1  | 首次触发禁言天数  |
|REJECT_ADD_REQUEST|否|False| 踢出后禁止重新加群 |

## 🎉 使用
### 指令表
| 指令  | 权限  | 需要@ | 范围 |   说明   |
|:---:|:---:| :---: |:--:|:------:|
| esl | 管理员 |  否   | 群聊 | 开关本群审核 |

