import flet as ft
from setup.settings import theme_mode

def tab(thememode: str):
    if thememode == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']

    tabs = ft.Container(
        content=ft.Row([

        ], spacing=5),
        height=75,
        bgcolor=tc['BG_SIDEBAR']
    )
    return tabs

# ft.Container(
#     content=ft.Text("main.py", size=12),
#     bgcolor=BG_EDITOR,
#     padding=ft.Padding.symmetric(vertical=15, horizontal=10),
#     border=ft.Border.only(top=ft.BorderSide(2, ACCENT_COLOR))
# ),
# ft.Container(content=ft.Text("config.json", size=12, color="gray"), padding=1),