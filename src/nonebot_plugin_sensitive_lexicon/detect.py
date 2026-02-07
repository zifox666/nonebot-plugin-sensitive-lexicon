"""
高性能敏感词检测模块
使用 Aho-Corasick 自动机算法，适用于大规模关键词库的快速匹配
"""

from pathlib import Path
from collections import deque

from nonebot import logger


class AhoCorasickNode:
    """AC自动机节点"""

    def __init__(self):
        self.children = {}  # 子节点字典
        self.fail = None  # 失败指针
        self.output = []  # 输出（匹配到的关键词列表）


class AhoCorasick:
    """Aho-Corasick 自动机实现"""

    def __init__(self):
        self.root = AhoCorasickNode()
        self._keyword_count = 0

    def add_keyword(self, keyword: str):
        """添加关键词到AC自动机"""
        if not keyword:
            return

        node = self.root
        for char in keyword:
            if char not in node.children:
                node.children[char] = AhoCorasickNode()
            node = node.children[char]

        # 记录该节点对应的关键词
        if keyword not in node.output:
            node.output.append(keyword)
            self._keyword_count += 1

    def build(self):
        """构建失败指针（KMP的失败函数思想）"""
        queue = deque()

        # 初始化第一层节点的失败指针指向根节点
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        # BFS构建失败指针
        while queue:
            current = queue.popleft()

            for char, child in current.children.items():
                queue.append(child)

                # 寻找失败指针
                fail_node = current.fail
                while fail_node is not None:
                    if char in fail_node.children:
                        child.fail = fail_node.children[char]
                        # 合并输出
                        child.output.extend(child.fail.output)
                        break
                    if fail_node == self.root:
                        child.fail = self.root
                        break
                    fail_node = fail_node.fail

    def search(self, text: str) -> list[tuple[int, int, str]]:
        """
        在文本中搜索所有匹配的关键词

        Args:
            text: 待检测文本

        Returns:
            List[Tuple[int, int, str]]: 匹配列表，每个元素为(起始位置, 结束位置, 关键词)
        """
        results = []
        node = self.root

        for i, char in enumerate(text):
            # 沿着失败指针寻找匹配
            while node != self.root and char not in node.children:
                node = node.fail

            if char in node.children:
                node = node.children[char]

                # 如果该节点有输出，说明匹配到关键词
                for keyword in node.output:
                    start_pos = i - len(keyword) + 1
                    end_pos = i + 1
                    results.append((start_pos, end_pos, keyword))

        return results

    @property
    def keyword_count(self) -> int:
        """获取关键词数量"""
        return self._keyword_count


class SensitiveWordDetector:
    """敏感词检测器"""

    def __init__(self, keyword_file: Path | None = None):
        """
        初始化检测器

        Args:
            keyword_file: 关键词文件路径，如果为None则使用默认路径
        """
        self.ac_automaton = AhoCorasick()
        self._keyword_file = keyword_file or self._get_default_keyword_file()
        self._loaded = False

    def _get_default_keyword_file(self) -> Path:
        """获取默认关键词文件路径"""
        return Path(__file__).parent / "关键词.txt"

    def load_keywords(self, encoding: str = "utf-8") -> int:
        """
        从文件加载关键词

        Args:
            encoding: 文件编码，默认utf-8

        Returns:
            int: 加载的关键词数量
        """
        if not self._keyword_file.exists():
            logger.error(f"关键词文件不存在: {self._keyword_file}")
            return 0

        logger.info(f"开始加载关键词文件: {self._keyword_file}")

        try:
            with open(self._keyword_file, encoding=encoding) as f:
                for line in f:
                    keyword = line.strip()
                    if keyword and not keyword.startswith("#"):  # 支持注释
                        self.ac_automaton.add_keyword(keyword)

            # 构建AC自动机
            self.ac_automaton.build()
            self._loaded = True

            count = self.ac_automaton.keyword_count
            logger.success(f"关键词加载完成，共 {count} 个关键词")
            return count

        except Exception as e:
            logger.error(f"加载关键词文件失败: {e}")
            return 0

    def detect(self, text: str) -> list[tuple[int, int, str]]:
        """
        检测文本中的敏感词

        Args:
            text: 待检测文本

        Returns:
            List[Tuple[int, int, str]]: 匹配列表，每个元素为(起始位置, 结束位置, 关键词)
        """
        if not self._loaded:
            logger.warning("关键词尚未加载，正在自动加载...")
            self.load_keywords()

        if not text:
            return []

        return self.ac_automaton.search(text)

    def contains_sensitive_word(self, text: str) -> bool:
        """
        判断文本是否包含敏感词

        Args:
            text: 待检测文本

        Returns:
            bool: 是否包含敏感词
        """
        results = self.detect(text)
        return len(results) > 0

    def get_sensitive_words(self, text: str) -> set[str]:
        """
        获取文本中包含的所有敏感词（去重）

        Args:
            text: 待检测文本

        Returns:
            Set[str]: 敏感词集合
        """
        results = self.detect(text)
        return {keyword for _, _, keyword in results}

    def replace_sensitive_words(self, text: str, replacement: str = "*") -> str:
        """
        替换文本中的敏感词

        Args:
            text: 待处理文本
            replacement: 替换字符，默认为 *

        Returns:
            str: 替换后的文本
        """
        results = self.detect(text)

        if not results:
            return text

        # 按位置从后往前替换，避免位置偏移
        results.sort(key=lambda x: x[0], reverse=True)

        text_list = list(text)
        for start, end, keyword in results:
            # 用相同长度的替换字符替换
            text_list[start:end] = [replacement] * (end - start)

        return "".join(text_list)

    def highlight_sensitive_words(self, text: str,
                                  prefix: str = "【",
                                  suffix: str = "】") -> str:
        """
        高亮显示文本中的敏感词

        Args:
            text: 待处理文本
            prefix: 前缀标记
            suffix: 后缀标记

        Returns:
            str: 标记后的文本
        """
        results = self.detect(text)

        if not results:
            return text

        # 按位置从后往前处理，避免位置偏移
        results.sort(key=lambda x: x[0], reverse=True)

        text_list = list(text)
        for start, end, _ in results:
            text_list[start:end] = [prefix, *text_list[start:end], suffix]

        return "".join(text_list)


# 全局检测器实例（单例模式）
_detector_instance: SensitiveWordDetector | None = None


def get_detector() -> SensitiveWordDetector:
    """
    获取全局检测器实例（单例模式）

    Returns:
        SensitiveWordDetector: 检测器实例
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SensitiveWordDetector()
        _detector_instance.load_keywords()
    return _detector_instance


# 便捷函数
async def detect_sensitive_words(text: str) -> list[tuple[int, int, str]]:
    """检测文本中的敏感词"""
    return get_detector().detect(text)


async def contains_sensitive_word(text: str) -> bool:
    """判断文本是否包含敏感词"""
    return get_detector().contains_sensitive_word(text)


async def get_sensitive_words(text: str) -> set[str]:
    """获取文本中包含的所有敏感词"""
    return get_detector().get_sensitive_words(text)


async def replace_sensitive_words(text: str, replacement: str = "*") -> str:
    """替换文本中的敏感词"""
    return get_detector().replace_sensitive_words(text, replacement)


async def highlight_sensitive_words(text: str, prefix: str = "【", suffix: str = "】")\
        -> str:
    """高亮显示文本中的敏感词"""
    return get_detector().highlight_sensitive_words(text, prefix, suffix)

