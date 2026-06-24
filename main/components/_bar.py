import flet as ft
from setup.settings import theme_mode

def bar(thememode: str):

    if thememode == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']

    _bar = ft.Container(
        content=ft.Column([
            ft.IconButton(ft.Icons.COPY_ALL_OUTLINED, icon_color=tc['ICON_COLOR'], tooltip="Download NFSe"),
            ft.IconButton(ft.Icons.SEARCH, icon_color=tc['ICON_COLOR'], tooltip="Processar Arquivos"),
            ft.IconButton(ft.Icons.PLAY_ARROW_ROUNDED, icon_color=tc['ICON_COLOR'], tooltip="Ordens Compras"),
            ft.IconButton(ft.Icons.EXTENSION_OUTLINED, icon_color=tc['ICON_COLOR'], tooltip="SAP - Lançar"),
        ], spacing=15),
            width=75,
            bgcolor=tc['BG_BAR'],
            padding=ft.Padding(top=10, left=20, right=5, bottom=5),
    )
    return _bar

def navrail(thememode: str):
    if thememode == 'DARK':
        tc = theme_mode['DARK']
    else:
        tc = theme_mode['LIGHT']
    
    is_extended = False

    destinations = [
        ft.NavigationRailDestination(icon=ft.Icons.COPY_ALL_OUTLINED, label="Download NFSe"),
        ft.NavigationRailDestination(icon=ft.Icons.SEARCH, label="Processar Arquivos"),
        ft.NavigationRailDestination(icon=ft.Icons.PLAY_ARROW_ROUNDED, label="Ordens Compras"),
        ft.NavigationRailDestination(icon=ft.Icons.EXTENSION_OUTLINED, label="SAP - Lançar"),
    ]

    toggle_btn = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT if is_extended else ft.Icons.CHEVRON_LEFT,
        tooltip="Expandir/Recolher",
        icon_size=24,
    )

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,  # Mostra labels quando expandido    
        min_width=75,                # Largura recolhida
        min_extended_width=240,      # Largura expandida
        group_alignment=-0.9,        # Alinha itens ao topo
        destinations=destinations,
        extended=is_extended,
        leading=toggle_btn,          # Botão fica acima dos itens
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        on_change=lambda e: print(f"Item selecionado: {e.control.selected_index}"),
    )
    rail.label_type = ft.NavigationRailLabelType.SELECTED if not is_extended else ft.NavigationRailLabelType.ALL
    def toggle_rail(e):
        nonlocal is_extended
        is_extended = not is_extended
    
        # 1. Alterna o modo expandido/recolhido
        rail.extended = is_extended
    
        # 2. Força o comportamento correto dos labels
        rail.label_type = (
            ft.NavigationRailLabelType.ALL if is_extended 
            else ft.NavigationRailLabelType.NONE
        )
    
        # 3. Atualiza ícone do botão
        toggle_btn.icon = ft.Icons.CHEVRON_LEFT if is_extended else ft.Icons.CHEVRON_RIGHT
        # ft.Page.update()

    toggle_btn.on_click = toggle_rail

    return rail
