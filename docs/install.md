# 安装、更新与撤回

本版是独立的 `pm-skills` 目录，不需要另一个 CMM-PM 仓库、绝对路径或软链接。仅支持 macOS＋Codex，Python 最低 3.13；不自动安装依赖，也不改任何全局配置。安装范围由用户请求决定。

## 安装步骤

1. 取得本版 ZIP 和随附 SHA-256。用标准 ZIP 工具解压到一个新位置，不覆盖已有文件；核对包哈希。
2. 在解压后的 `pm-skills` 目录执行 `python3 -B tools/manage_install.py verify --source .`，核对逐文件清单。该清单用于检测损坏和意外改动，不是来源真实性签名。
3. Agent 确认环境符合要求，确定当前客户端支持的目标 Skill 目录和用户允许的范围。目标须明确传入；安装工具没有默认全局目录。
4. 执行 `python3 -B tools/manage_install.py install --source . --skills-dir TARGET_SKILLS_DIRECTORY`。把目标参数换成刚确认的实际路径，避免把示例当成已存在目录。
5. 通过 Codex 的 Skill 发现接口或菜单核对 `pm skills`，再做一次讨论模式调用：只检查当前需求、不给文件做改动。安装工具返回成功只证明文件已安装，不代表客户端已加载。

用户已有同名入口时先核对来源，不静默覆盖。包或目标为软链接、文件被改动、清单不一致时会拒绝。

## 更新和回退

已有版本必须由本工具安装、有有效安装回执且没有用户修改或未知文件。更新命令为：

```text
python3 -B tools/manage_install.py update --source NEW_PACKAGE_DIRECTORY --skills-dir TARGET_SKILLS_DIRECTORY --backup-dir BACKUP_DIRECTORY
```

备份必须放在 Skill 发现目录之外。更新先完整准备新目录并保留旧版本 ZIP，再切换；暂存复制失败时旧版本继续保留。工具返回实际备份路径。

```text
python3 -B tools/manage_install.py rollback --backup ACTUAL_BACKUP_ZIP --skills-dir TARGET_SKILLS_DIRECTORY --backup-dir BACKUP_DIRECTORY
```

回退会核对备份本身，同时备份当前版本。也可以在卸载后用备份恢复。

## 卸载

```text
python3 -B tools/manage_install.py uninstall --skills-dir TARGET_SKILLS_DIRECTORY --backup-dir BACKUP_DIRECTORY
```

只对回执管理、内容未改变的 `pm-skills` 目录执行卸载，并保留备份。项目资料、其他 Skill 和未知用户文件不删除。若检查发现用户修改，先报告冲突，不能为了卸载而强行覆盖或清理。

## 从旧本机适配入口迁移

旧入口如果使用链接读取另一个源码仓库，不属于本安装工具管理的版本。本工具拒绝覆盖它。Agent 应先核对用户修改，保存原入口与链接清单，在用户授权范围内把新包安装到独立位置验证，再另行确认是否替换旧入口。不要整包安装旧合集，也不要把旧入口删除当作迁移前提。

## 没有识别或无法运行

核查实际安装路径、`SKILL.md`、版本、资源完整性、客户端发现结果及 Python 环境。Windows 原生缺少现有执行器使用的 `fcntl`，本版不提供假成功或自动改造环境的回退。缺环境时报告确切问题，不下载依赖；用户批准后才能另作准备。
