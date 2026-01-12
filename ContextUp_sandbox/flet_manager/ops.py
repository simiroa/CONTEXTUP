from pathlib import Path
from typing import Any

from bootstrap import ROOT_DIR, ensure_src_path
from safe_mode import Action, SafeModeGuard, SafeResult

ensure_src_path()

from core.settings import load_settings, save_settings


class SafeOps:
    def __init__(self, root_dir: Path | None, guard: SafeModeGuard):
        self.root_dir = Path(root_dir) if root_dir else ROOT_DIR
        self.guard = guard
        self._settings_cache: dict[str, Any] | None = None

    def read_settings(self) -> dict[str, Any]:
        self._settings_cache = load_settings()
        return self._settings_cache

    def read_menu_items(self) -> list[dict[str, Any]]:
        from manager.mgr_core.config import ConfigManager

        manager = ConfigManager(self.root_dir)
        return manager.load_config(force_reload=False)

    def save_settings(self, settings: dict[str, Any] | None = None) -> SafeResult:
        def _save():
            target = settings or self._settings_cache or self.read_settings()
            return save_settings(target)

        return self.guard.run(Action.FILE_WRITE, _save)

    def save_menu_config(
        self, items: list[dict[str, Any]], settings: dict[str, Any] | None = None
    ) -> SafeResult:
        def _save():
            from manager.mgr_core.config import ConfigManager

            manager = ConfigManager(self.root_dir)
            target_settings = settings or self._settings_cache or self.read_settings()
            return manager.save_config(items, target_settings)

        return self.guard.run(Action.FILE_WRITE, _save)

    def apply_registry(self) -> SafeResult:
        def _apply():
            from core.config import MenuConfig
            from core.registry import RegistryManager

            menu_config = MenuConfig()
            registry = RegistryManager(menu_config)
            registry.config.load()
            registry.unregister_all()
            registry.register_all()
            return True

        return self.guard.run(Action.REGISTRY, _apply)

    def start_tray(self) -> SafeResult:
        def _start():
            from manager.mgr_core.process import TrayProcessManager

            settings = self._settings_cache or self.read_settings()
            manager = TrayProcessManager(self.root_dir, settings)
            ok, msg = manager.start()
            return {"ok": ok, "message": msg}

        return self.guard.run(Action.PROCESS, _start)

    def stop_tray(self) -> SafeResult:
        def _stop():
            from manager.mgr_core.process import TrayProcessManager

            settings = self._settings_cache or self.read_settings()
            manager = TrayProcessManager(self.root_dir, settings)
            ok, msg = manager.stop()
            return {"ok": ok, "message": msg}

        return self.guard.run(Action.PROCESS, _stop)

    def update_system_libs(self) -> SafeResult:
        def _update():
            from manager.mgr_core.packages import PackageManager

            manager = PackageManager(self.root_dir)
            manager.update_system_libs()
            return True

        return self.guard.run(Action.PACKAGE, _update)
