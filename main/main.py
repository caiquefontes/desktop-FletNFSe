# ----- solution for relative imports
import sys
from pathlib import Path
script_dir = Path(__file__).parent.parent
sys.path.append(str(script_dir))

# ---- code
import flet as ft
from setup.settings import theme_mode
from components._bar import bar, navrail
from components._sidebar import sidebar
from components._tabs import tab
from components._status_bar import statusbar

def main(page: ft.Page):
    page.title = "NFSeDigital"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1100
    page.window_height = 700
    page.padding = 0
    page.spacing = 0
    
    if str(page.theme_mode.name) == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']
    # -----------------------------------------------------------------------

    # --- COMPONENTES ---
    # bars = bar(thememode=str(page.theme_mode.name))
    navrails = navrail(thememode=str(page.theme_mode.name))
    # sidebars = sidebar(thememode=str(page.theme_mode.name))
    # tabs = tab(thememode=str(page.theme_mode.name))
    statusbars = statusbar(thememode=str(page.theme_mode.name))
    # add apps
    areas = ft.Container(
        content=ft.Column([
            # tabs,
            ft.Container(content='', expand=True, bgcolor=tc['BG_EDITOR'])
        ], spacing=0),
        expand=True,
        bgcolor=tc['BG_EDITOR']
    )

    # --- LAYOUT FINAL ---
    main_layout = ft.Column([
        statusbars,
        ft.Row([
            navrails,
            areas
        ], expand=True, spacing=0),
        statusbars
    ], expand=True, spacing=0)

    page.add(main_layout)

ft.app(target=main)