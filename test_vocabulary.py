"""测试多关键词文件加载"""
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nonebot_plugin_sensitive_lexicon.detect import SensitiveWordDetector

def test_load_multiple_files():
    detector = SensitiveWordDetector()
    count = detector.load_keywords()

    print(f"\n✅ 成功加载 {count} 个关键词")

    # 测试检测
    test_texts = [
        "这是正常文本",
        "测试敏感词",
    ]

    for text in test_texts:
        results = detector.detect(text)
        if results:
            print(f"\n文本: {text}")
            print(f"检测到: {results}")
        else:
            print(f"\n文本: {text} - 无敏感词")

if __name__ == "__main__":
    test_load_multiple_files()

