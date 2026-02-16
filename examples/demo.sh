#!/bin/bash
# 演示脚本 - 展示如何使用Infinity AI框架

set -e

echo "======================================"
echo "Infinity AI - 演示脚本"
echo "======================================"
echo ""

# 检查是否安装
if ! command -v infinity-ai &> /dev/null; then
    echo "❌ Infinity AI未安装"
    echo "请先运行: pip install -e ."
    exit 1
fi

# 检查API密钥
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 未设置ANTHROPIC_API_KEY环境变量"
    echo "请先设置: export ANTHROPIC_API_KEY='your-key'"
    exit 1
fi

echo "✅ Infinity AI已安装"
echo "✅ API密钥已设置"
echo ""

# 创建演示项目
DEMO_DIR="demo-counter-app"
echo "📁 创建演示项目: $DEMO_DIR"
mkdir -p $DEMO_DIR
cd $DEMO_DIR

# 创建需求文件
cat > requirements.txt << EOF
创建一个简单的计数器Web应用：
- 显示当前计数（初始值为0）
- 有"增加"按钮，每次点击计数+1
- 有"减少"按钮，每次点击计数-1
- 有"重置"按钮，将计数归零
- 使用localStorage保存计数
- 简洁现代的UI设计
EOF

echo "✅ 需求文件已创建"
echo ""
echo "📄 需求内容:"
cat requirements.txt
echo ""

# 初始化项目
echo "======================================"
echo "步骤1: 初始化项目"
echo "======================================"
infinity-ai init --requirements requirements.txt

echo ""
echo "✅ 项目已初始化"
echo ""

# 查看状态
echo "======================================"
echo "步骤2: 查看项目状态"
echo "======================================"
infinity-ai status

echo ""
echo "======================================"
echo "✅ 演示完成！"
echo "======================================"
echo ""
echo "接下来你可以："
echo "1. 查看功能列表: cat feature_list.json"
echo "2. 查看进度文件: cat claude-progress.txt"
echo "3. 运行Agent: infinity-ai run --mode single"
echo "4. 查看状态: infinity-ai status"
echo ""
echo "完整文档请查看 README.md"