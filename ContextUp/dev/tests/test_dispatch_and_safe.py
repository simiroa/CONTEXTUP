import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from core.config import MenuConfig
from core import menu
from utils.files import get_safe_path
from utils import batch_runner


def test_config_dispatch_alignment():
    cfg = MenuConfig("config/menu_config.json")
    handlers = menu.build_handler_map()

    missing = []
    for item in cfg.items:
        if item.get("status") != "COMPLETE" or not item.get("enabled", True):
            continue
        if item.get("command"):
            continue
        if item["id"] not in handlers:
            missing.append(item["id"])

    assert not missing, f"Handlers missing for ids: {missing}"


def test_get_safe_path_generates_unique_names(tmp_path):
    original = tmp_path / "file.txt"
    original.write_text("a")
    candidate = get_safe_path(original)
    assert candidate != original
    assert candidate.name.startswith("file_")
    assert not candidate.exists()


def test_batch_runner_single_leader(tmp_path, monkeypatch):
    # Force temp dir for lock files to our tmp_path
    monkeypatch.setenv("TMP", str(tmp_path))
    target = tmp_path / "a.txt"
    target.write_text("data")
    result = batch_runner.collect_batch_context("test_item", str(target), timeout=0.01)
    assert result and target.resolve() in result
