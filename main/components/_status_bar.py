import flet as ft
from setup.settings import theme_mode

def statusbar(thememode: str):
    if thememode == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']

    status_bar = ft.Container(
        content=ft.Row(
            [],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        height=25,
        bgcolor=tc['ACCENT_COLOR']
    )

    return status_bar