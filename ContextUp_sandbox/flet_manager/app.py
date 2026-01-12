from pathlib import Path
import flet as ft

from bootstrap import ROOT_DIR, ensure_src_path

ensure_src_path()

from manager.mgr_core.config import ConfigManager


def load_menu_items(root_dir: Path) -> tuple[list[dict], str | None]:
    try:
        manager = ConfigManager(root_dir)
        return manager.load_config(force_reload=False), None
    except Exception as exc:
        return [], str(exc)


def build_menu_rows(items: list[dict]) -> list[ft.DataRow]:
    rows = []
    for item in items:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(item.get("id", "")), size=11)),
                    ft.DataCell(ft.Text(str(item.get("name", "")), size=11, overflow=ft.TextOverflow.ELLIPSIS)),
                    ft.DataCell(ft.Text(str(item.get("category", "")), size=11)),
                    ft.DataCell(ft.Text("Yes" if item.get("enabled", True) else "No", size=11)),
                    ft.DataCell(ft.Text("Yes" if item.get("gui", False) else "No", size=11)),
                    ft.DataCell(ft.Text("Yes" if item.get("show_in_tray", False) else "No", size=11)),
                ]
            )
        )
    return rows


def build_dummy_panel(title: str, body: list[ft.Control]) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [ft.Text(title, size=14, weight=ft.FontWeight.BOLD)] + body,
            spacing=8,
        ),
        padding=12,
        border=ft.border.all(1, ft.colors.GREY_700),
        border_radius=8,
    )


def main(page: ft.Page) -> None:
    page.title = "ContextUp Flet Manager (Sandbox Dummy)"
    page.padding = 16

    root_text = ft.Text(value=f"Root: {Path(ROOT_DIR)}", size=12)
    dummy_text = ft.Text(value="Dummy mode ON. UI is read-only.", size=12, color=ft.colors.AMBER_400)

    menu_summary = ft.Text(size=12)
    menu_error = ft.Text(size=12, color=ft.colors.RED_400, visible=False)
    menu_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Category")),
            ft.DataColumn(ft.Text("Enabled")),
            ft.DataColumn(ft.Text("GUI")),
            ft.DataColumn(ft.Text("Tray")),
        ],
        rows=[],
    )

    def refresh_menu() -> None:
        items, error = load_menu_items(Path(ROOT_DIR))
        enabled_count = sum(1 for item in items if item.get("enabled", True))
        categories = sorted({item.get("category", "") for item in items if item.get("category")})
        menu_summary.value = f"Items: {len(items)} | Enabled: {enabled_count} | Categories: {len(categories)}"
        menu_table.rows = build_menu_rows(items)
        menu_error.visible = bool(error)
        menu_error.value = f"Load error: {error}" if error else ""
        page.update()

    dashboard_tab = ft.Tab(
        text="Dashboard",
        content=ft.Column(
            [
                build_dummy_panel(
                    "Status",
                    [
                        ft.Text("Install tier: Dummy"),
                        ft.Text("Update status: Dummy"),
                        ft.ElevatedButton("Check updates", disabled=True),
                        ft.ElevatedButton("Restart Explorer", disabled=True),
                    ],
                ),
                build_dummy_panel(
                    "Appearance",
                    [
                        ft.Dropdown(label="Theme", options=[ft.dropdown.Option("Dark")], disabled=True),
                        ft.Dropdown(label="Language", options=[ft.dropdown.Option("en")], disabled=True),
                        ft.Switch(label="Start tray on login", value=False, disabled=True),
                    ],
                ),
                build_dummy_panel(
                    "Danger Zone",
                    [
                        ft.ElevatedButton("Export userdata", disabled=True),
                        ft.ElevatedButton("Import userdata", disabled=True),
                        ft.ElevatedButton("Factory reset", disabled=True),
                    ],
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    menu_tab = ft.Tab(
        text="Menu Editor",
        content=ft.Column(
            [
                ft.Text("Menu items (parsed)", size=14, weight=ft.FontWeight.BOLD),
                menu_summary,
                menu_error,
                ft.Container(
                    content=menu_table,
                    padding=8,
                    border=ft.border.all(1, ft.colors.GREY_700),
                    border_radius=6,
                ),
                ft.Text("Editing controls are disabled in dummy mode.", size=12, color=ft.colors.GREY_500),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    categories_tab = ft.Tab(
        text="Categories",
        content=ft.Column(
            [
                build_dummy_panel(
                    "Category Management",
                    [
                        ft.TextField(label="New category", disabled=True),
                        ft.ElevatedButton("Add category", disabled=True),
                        ft.ElevatedButton("Save changes", disabled=True),
                    ],
                )
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    deps_tab = ft.Tab(
        text="Dependencies",
        content=ft.Column(
            [
                build_dummy_panel(
                    "Connectivity",
                    [
                        ft.TextField(label="Python path", disabled=True),
                        ft.TextField(label="FFmpeg path", disabled=True),
                        ft.TextField(label="Blender path", disabled=True),
                        ft.ElevatedButton("Auto-detect", disabled=True),
                    ],
                ),
                build_dummy_panel(
                    "Packages",
                    [
                        ft.Text("Dependency status: Dummy"),
                        ft.ElevatedButton("Install missing", disabled=True),
                        ft.ElevatedButton("Update system libs", disabled=True),
                    ],
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    logs_tab = ft.Tab(
        text="Logs",
        content=ft.Column(
            [
                build_dummy_panel(
                    "Log Viewer",
                    [
                        ft.Text("Logs are not loaded in dummy mode."),
                        ft.ElevatedButton("Refresh logs", disabled=True),
                    ],
                )
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    page.add(
        ft.Column(
            [
                ft.Text("ContextUp Manager (Flet) - Dummy UI", size=20, weight=ft.FontWeight.BOLD),
                root_text,
                dummy_text,
                ft.Divider(),
                ft.Tabs(
                    tabs=[dashboard_tab, menu_tab, categories_tab, deps_tab, logs_tab],
                    expand=True,
                ),
            ],
            spacing=12,
        )
    )

    refresh_menu()


if __name__ == "__main__":
    ft.app(target=main)
