import flet as ft
from setup.settings import theme_mode

def sidebar(thememode: str):
    if thememode == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']

    _sidebar = ft.Container(
        content=ft.Column(
            [],
            spacing=5
        ),
        width=120,
        bgcolor=tc['BG_SIDEBAR'],
        padding=15
    )
    
    return _sidebar

# ft.Text("EXPLORER", size=12, weight="bold", color=tc['TEXT_PRIMARY']),
# ft.Text("PROJETO: NFSeDigital", size=11, color=tc['TEXT_PRIMARY']),
# ft.Divider(height=1, color="white10"),
# ft.TextButton("📂 pwNFSe (Automação)", style=ft.ButtonStyle(color=tc['ICON_COLOR'])),
# ft.TextButton("📂 dataNFSe (Parser)", style=ft.ButtonStyle(color=tc['ICON_COLOR'])),
# ft.TextButton("📂 ordens (Vínculos)", style=ft.ButtonStyle(color=tc['ICON_COLOR'])),
# ft.TextButton("📂 sapNFSe (Lançador)", style=ft.ButtonStyle(color=tc['ICON_COLOR'])),