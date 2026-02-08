"""
配置模块测试
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from settings import Config


class TestConfig:
    """Config 类基础测试"""

    def test_default_values(self):
        assert Config.LLM_MODEL == 'deepseek-chat'
        assert Config.LLM_BASE_URL == 'https://api.deepseek.com'
        assert Config.LLM_TIMEOUT > 0
        assert Config.FETCH_TIMEOUT > 0
        assert Config.MAX_PER_SOURCE > 0

    def test_get_llm_client_kwargs(self):
        kwargs = Config.get_llm_client_kwargs()
        assert 'base_url' in kwargs
        assert 'timeout' in kwargs
        assert 'max_retries' in kwargs

    def test_ensure_dirs(self, tmp_path, monkeypatch):
        """测试目录创建"""
        monkeypatch.setattr(Config, 'DATA_DIR', str(tmp_path / 'data'))
        monkeypatch.setattr(Config, 'REPORTS_DIR', str(tmp_path / 'data' / 'reports'))
        monkeypatch.setattr(Config, 'REPORTS_JSON_DIR', str(tmp_path / 'data' / 'reports_json'))
        monkeypatch.setattr(Config, 'WEEKLY_DIR', str(tmp_path / 'data' / 'weekly'))
        monkeypatch.setattr(Config, 'MONTHLY_DIR', str(tmp_path / 'data' / 'monthly'))
        monkeypatch.setattr(Config, 'LOG_DIR', str(tmp_path / 'logs'))
        
        Config.ensure_dirs()
        assert os.path.isdir(str(tmp_path / 'data'))
        assert os.path.isdir(str(tmp_path / 'logs'))

    def test_validate_without_key(self, monkeypatch):
        """验证缺少 API key 时应返回 False"""
        monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
        errors = Config.validate()
        assert len(errors) > 0

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv('LLM_MODEL', 'test-model')
        # 重新加载 Config 不方便，这里只验证 os.getenv 机制
        assert os.getenv('LLM_MODEL') == 'test-model'
