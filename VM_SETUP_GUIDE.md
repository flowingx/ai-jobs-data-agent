# Linux VM 部署指南（VMware）

## 1. VMware 共享文件夹（模型文件）

**Windows 端操作：**
1. VMware → 虚拟机设置 → 选项 → 共享文件夹 → 添加
2. 选择 `F:\资料\大三\数据库\shushu-internship-tool\data_agent_project\models` 作为共享目录
3. 命名为 `shared_models`

**Linux 端挂载：**
```bash
# 查看共享目录
ls /mnt/hgfs/shared_models/

# 如果 /mnt/hgfs 为空，手动挂载
sudo vmware-hgfsclient
sudo mkdir -p /mnt/hgfs/shared_models
sudo mount -t fuse.vmhgfs-fuse .host:/shared_models /mnt/hgfs/shared_models -o allow_other
```

## 2. Linux 基础环境

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git build-essential cmake

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip git gcc gcc-c++ cmake make
```

## 3. 克隆项目

```bash
cd ~
git clone https://github.com/flowingx/shushu-internship-tool.git
cd shushu-internship-tool
```

## 4. Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
cd data_agent_project
pip install -r requirements.txt
```

## 5. 安装 llama.cpp（Linux）

```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build --config Release -j$(nproc)

# llama-server 编译在 build/bin/llama-server
# 建议软链到 PATH
sudo ln -s ~/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
```

验证：
```bash
llama-server --version
```

## 6. 模型文件

```bash
# 从 VMware 共享目录复制到项目
cp /mnt/hgfs/shared_models/Qwen3-4B-Q4_K_M.gguf ~/shushu-internship-tool/data_agent_project/models/

# 验证
ls -lh ~/shushu-internship-tool/data_agent_project/models/
# 应显示 ~2.5G 的 Qwen3-4B-Q4_K_M.gguf
```

> 如果共享目录不可用，也可以用 `scp` 从 Windows 传输：
> ```bash
> # 在 Windows PowerShell 中
> scp "F:\资料\大三\数据库\shushu-internship-tool\data_agent_project\models\Qwen3-4B-Q4_K_M.gguf" user@vm-ip:~/shushu-internship-tool/data_agent_project/models/
> ```

## 7. 生成数据库

```bash
cd ~/shushu-internship-tool/data_agent_project
source ../.venv/bin/activate
python scripts/generate_job_data.py
```

## 8. 生成可视化图表

```bash
python scripts/visualize.py
```

> **Linux 中文字体问题：** matplotlib 可能报字体缺失，安装中文字体：
> ```bash
> sudo apt install -y fonts-wqy-zenhei
> # 或手动安装 SimHei 到 ~/.fonts/ 然后
> fc-cache -fv
> ```

## 9. 启动 LLM 服务

**方案 A：有 GPU 的机器**
```bash
llama-server \
  -m ~/shushu-internship-tool/data_agent_project/models/Qwen3-4B-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 99 \
  --ctx-size 4096
```

**方案 B：纯 CPU（虚拟机无 GPU）**
```bash
llama-server \
  -m ~/shushu-internship-tool/data_agent_project/models/Qwen3-4B-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  --ctx-size 4096 \
  -t 4
```

> `-t 4` 表示 4 个 CPU 线程，按你 VM 分配的核心数调整。纯 CPU 推理会慢，但能跑。

## 10. 测试 Agent

**新开一个终端：**
```bash
cd ~/shushu-internship-tool/data_agent_project
source ../.venv/bin/activate
python scripts/data_agent.py --question "哪些技能最热门？"
```

## 11. 启动 Streamlit Web 界面

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

浏览器访问 `http://VM-IP:8501`

## 12. 快速启动脚本

把以下内容保存为 `start_all.sh`，一键启动所有服务：

```bash
#!/bin/bash
cd "$(dirname "$0")"
source ../.venv/bin/activate

echo "=== 启动 llama-server ==="
llama-server \
  -m models/Qwen3-4B-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  --ctx-size 4096 -t 4 &
LLAMA_PID=$!

echo "等待 LLM 服务就绪..."
for i in $(seq 1 30); do
  curl -s http://localhost:8080/health > /dev/null 2>&1 && break
  sleep 2
done

echo "=== 启动 Streamlit ==="
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo "服务已启动:"
echo "  LLM:   http://localhost:8080"
echo "  Web:   http://localhost:8501"
echo "按 Ctrl+C 停止"

trap "kill $LLAMA_PID $STREAMLIT_PID 2>/dev/null" EXIT
wait
```

```bash
chmod +x start_all.sh
./start_all.sh
```

## 注意事项

| 项目 | 说明 |
|------|------|
| **VM 内存** | 建议分配 8GB+，Qwen3-4B 纯 CPU 需要约 4-5GB RAM |
| **磁盘** | 模型文件 2.5GB，确保 VM 磁盘剩余 5GB+ |
| **GPU** | VMware 虚拟机无法直通 GPU（除非 ESXi + 直通），纯 CPU 跑 4B 模型可用但慢 |
| **防火墙** | `sudo ufw allow 8080/tcp && sudo ufw allow 8501/tcp` |
| **中文编码** | Linux 原生 UTF-8，不需要 `chcp 65001` |
