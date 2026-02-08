"""
processor 模块的单元测试
重点测试 JSON 提取、索引解析等纯函数
"""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from processor import NLPProcessor


class TestExtractJson:
    """测试 _extract_json 方法"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前创建 NLPProcessor（不需要真实 API key）"""
        os.environ.setdefault('DEEPSEEK_API_KEY', 'test-key')
        self.processor = NLPProcessor()

    def test_normal_json_array(self):
        text = '[{"index": 1, "summary": "测试"}]'
        result = self.processor._extract_json(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]['index'] == 1

    def test_json_with_surrounding_text(self):
        text = '''以下是分析结果：
[{"index": 1, "summary": "美联储维持利率"}]
以上就是分析。'''
        result = self.processor._extract_json(text)
        assert result is not None
        assert len(result) == 1

    def test_json_with_markdown_code_block(self):
        text = '''```json
[{"index": 1, "summary": "test"}]
```'''
        result = self.processor._extract_json(text)
        assert result is not None
        assert len(result) == 1

    def test_truncated_json_recovery(self):
        """测试被截断的 JSON 恢复"""
        text = '[{"index": 1, "summary": "完整"}, {"index": 2, "summ'
        result = self.processor._extract_json(text)
        # 应该至少能恢复第一个完整对象
        assert result is not None
        assert len(result) >= 1
        assert result[0]['index'] == 1

    def test_empty_input(self):
        assert self.processor._extract_json('') is None
        assert self.processor._extract_json('no json here') is None

    def test_multiple_objects(self):
        text = '''[
  {"index": 1, "summary": "A", "sentiment": 0.5},
  {"index": 2, "summary": "B", "sentiment": -0.3},
  {"index": 3, "summary": "C", "sentiment": 0.0}
]'''
        result = self.processor._extract_json(text)
        assert result is not None
        assert len(result) == 3


class TestParseIndices:
    """测试 _parse_indices 方法"""

    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ.setdefault('DEEPSEEK_API_KEY', 'test-key')
        self.processor = NLPProcessor()

    def test_normal_list(self):
        indices = self.processor._parse_indices('[1, 3, 5]', 10)
        assert indices == [1, 3, 5]

    def test_out_of_range(self):
        indices = self.processor._parse_indices('[1, 100, 3]', 10)
        assert 100 not in indices
        assert 1 in indices
        assert 3 in indices

    def test_max_20(self):
        raw = json.dumps(list(range(1, 30)))
        indices = self.processor._parse_indices(raw, 30)
        assert len(indices) <= 20

    def test_with_surrounding_text(self):
        raw = '以下是筛选结果：\n[1, 2, 3]\n以上。'
        indices = self.processor._parse_indices(raw, 10)
        assert indices == [1, 2, 3]

    def test_empty_list(self):
        indices = self.processor._parse_indices('[]', 10)
        assert indices == []

    def test_string_indices(self):
        """模型有时返回字符串形式的数字"""
        indices = self.processor._parse_indices('["1", "3", "5"]', 10)
        assert indices == [1, 3, 5]
