import flet as ft

def main(page: ft.Page):
    page.title = "Gestor de NFSe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    # Componente de texto central para mostrar a mudança de página
    conteudo_central = ft.Text("Selecione uma opção no menu superior", size=25, weight="bold")

    # Função para mudar o conteúdo ao clicar no menu
    def mudar_aba(e):
        opcao = e.control.data
        conteudo_central.value = f"Página: {opcao}"
        page.update()

    menu_itens = [
        ft.TextButton("Download NFSe", data="Download NFSe", on_click=mudar_aba),
        ft.TextButton("Verificar Notas", data="Verificar Notas", on_click=mudar_aba),
        ft.TextButton("Visualizar Nota", data="Visualizar Nota", on_click=mudar_aba),
        ft.TextButton("Processar Banco Dados", data="Processar Banco Dados", on_click=mudar_aba),
    ]

    # Criação do Menu Superior (AppBar)
    page.appbar = ft.AppBar(
        title=ft.Text("Sistema NFSe"),
        bgcolor=ft.Colors.SURFACE_VARIANT,
        actions=menu_itens,
    )

    # Adiciona o conteúdo na tela
    page.add(ft.Center(content=conteudo_central))


# Executar o App
if __name__ == "__main__":
    ft.app(target=main)
