"""
Main application shell for NFSeFlet using Flet framework.
Provides navigation between different miniapps (pwNFSe, dataNFSe, ordens, sapNFSe).
"""
import flet as ft
from flet import (
    Page, 
    AppBar, 
    Text, 
    NavigationRail, 
    NavigationRailDestination,
    Icon,
    Icons,
    Row,
    Column,
    Container,
    Tabs,
    Tab,
    IconButton,
    FloatingActionButton,
    VerticalDivider,
)

# Import miniapp modules
from apps.pwNFSe.app import pwNFSeApp
from apps.dataNFSe.app import dataNFSeApp
from apps.ordens.app import ordensApp
from apps.sapNFSe.app import sapNFSeApp

def main(page: Page):
    """Main application function."""
    page.title = "NFSeFlet - Sistema de Gestão de Notas Fiscais"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # AppBar
    page.appbar = AppBar(
        leading=Icon(Icons.RECEIPT_LONG),
        title=Text("NFSeFlet"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_BRIGHT,
        actions=[
            IconButton(Icons.SETTINGS, tooltip="Configurações"),
        ],
    )
    
    # Navigation Rail (Sidebar)
    nav_rail = NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        # leading=FloatingActionButton(icon=Icons.CREATE, text="Adicionar"),
        leading=FloatingActionButton(icon=Icons.CREATE),
        group_alignment=-0.9,
        destinations=[
            NavigationRailDestination(
                icon=Icons.DOWNLOAD_ROUNDED,
                selected_icon=Icons.DOWNLOAD,
                label="pwNFSe - Captura",
            ),
            NavigationRailDestination(
                icon=Icons.STORAGE,
                selected_icon=Icons.STORAGE,
                label="dataNFSe - Dados",
            ),
            NavigationRailDestination(
                icon=Icons.LIST_ALT,
                selected_icon=Icons.LIST_ALT,
                label="ordens - Compras",
            ),
            NavigationRailDestination(
                icon=Icons.WAREHOUSE,
                selected_icon=Icons.WAREHOUSE,
                label="sapNFSe - SAP",
            ),
        ],
        on_change=lambda e: change_tab(e.control.selected_index),
    )
    
    # Main content area
    content_area = Column(
        expand=True,
    )
    
    # Layout
    page.add(
        Row(
            [
                nav_rail,
                VerticalDivider(width=1),
                Container(content_area, expand=True, padding=20),
            ],
            expand=True,
        )
    )
    
    def change_tab(selected_index):
        """Handle navigation rail tab changes and load the appropriate miniapp."""
        content_area.controls.clear()
        
        if selected_index == 0:  # pwNFSe
            pwNFSeApp(page)
            # Since pwNFSeApp modifies the page directly, we need to get its content
            # For now, we'll show a placeholder
            content_area.controls.append(
                Text("pwNFSe - Módulo de Captura", size=20, weight=ft.FontWeight.BOLD)
            )
        elif selected_index == 1:  # dataNFSe
            dataNFSeApp(page)
            content_area.controls.append(
                Text("dataNFSe - Módulo de Dados", size=20, weight=ft.FontWeight.BOLD)
            )
        elif selected_index == 2:  # ordens
            ordensApp(page)
            content_area.controls.append(
                Text("ordens - Módulo de Vínculo de Compras", size=20, weight=ft.FontWeight.BOLD)
            )
        elif selected_index == 3:  # sapNFSe
            sapNFSeApp(page)
            content_area.controls.append(
                Text("sapNFSe - Módulo de Validação e Lançamento SAP", size=20, weight=ft.FontWeight.BOLD)
            )
        
        page.update()
    
    # Load default tab (pwNFSe) on startup
    change_tab(0)
    
if __name__ == "__main__":
    ft.app(target=main)