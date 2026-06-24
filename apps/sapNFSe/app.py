"""
sapNFSe App - Validação & Lançamento
Responsável pela validação de dados e lançamento no SAP.
"""

import flet as ft
from flet import (
    Page,
    AppBar,
    Text,
    IconButton,
    Icons,
    Column,
    Row,
    Container,
    ElevatedButton,
    ProgressRing,
    ListView,
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    PopupMenuButton,
    PopupMenuItem,
    Dropdown,
    dropdown,
    TextField,
    Checkbox,
    Switch,
    Slider,
)
from models.models import SapLancamento, NFSe, initialize_database
import datetime

# Initialize database
# initialize_database()

def sapNFSeApp(page: Page):
    """Main function for sapNFSe app."""
    
    # State variables
    lancamentos_pendentes = []  # List of pending SAP lancamentos
    
    def carregar_lancamentos_pendentes(e):
        """Load NFSe records pending SAP launch."""
        # Disable button during process
        carregar_btn.disabled = True
        page.update()
        
        status_text.value = "Carregando lançamentos pendentes..."
        progress_ring.visible = True
        page.update()
        
        try:
            # Get NFSe that are processed but not yet launched to SAP
            lancamentos_pendentes.clear()
            
            # Find NFSe with status 'processado' that don't have successful SAP lancamentos
            nfse_processadas = NFSe.select().where(NFSe.status == 'processado')
            
            for nfse in nfse_processadas:
                # Check if this NFSe already has a successful SAP lancamento
                lancamento_sucesso = SapLancamento.select().where(
                    (SapLancamento.nfse == nfse) & 
                    (SapLancamento.status == 'sucesso')
                ).exists()
                
                if not lancamento_sucesso:
                    lancamentos_pendentes.append(nfse)
            
            atualizar_tabela_lancamentos()
            status_text.value = f"Carregados {len(lancamentos_pendentes)} lançamentos pendentes"
            log_message(f"✓ Carregados {len(lancamentos_pendentes)} NFSe para lançamento no SAP")
            
        except Exception as ex:
            status_text.value = f"Erro ao carregar lançamentos: {str(ex)}"
            log_message(f"✗ Erro ao carregar lançamentos: {str(ex)}")
        
        finally:
            # Reset UI
            carregar_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def validar_dados_nfse(nfse):
        """Validate NFSe data before SAP launch."""
        errors = []
        warnings = []
        
        # Check required fields
        if not nfse.numero_nfse:
            errors.append("Numero da NFSe não informado")
        
        if not nfse.cnpj_emitente:
            errors.append("CNPJ do emitente não informado")
        
        if not nfse.cnpj_tomador:
            errors.append("CNPJ do tomador não informado")
        
        if nfse.valor_total <= 0:
            errors.append("Valor total deve ser maior que zero")
        
        if not nfse.data_emissao:
            errors.append("Data de emissão não informada")
        
        # Additional validations
        if len(nfse.cnpj_emitente) != 14:
            warnings.append("CNPJ do emitente deve ter 14 dígitos")
        
        if len(nfse.cnpj_tomador) != 14:
            warnings.append("CNPJ do tomador deve ter 14 dígitos")
        
        return errors, warnings
    
    def lancar_no_sap(e):
        """Launch selected NFSe to SAP."""
        # This would be implemented with actual SAP integration
        # For now, just simulate the process
        
        lancar_btn.disabled = True
        page.update()
        
        status_text.value = "Iniciando lançamento no SAP..."
        progress_ring.visible = True
        page.update()
        
        try:
            # Get selected NFSe from checkboxes (simplified - in real app would get from selected rows)
            nfse_a_lancar = []  # This would be populated from UI selection
            
            # For demo, let's launch the first pending NFSe
            if lancamentos_pendentes:
                nfse = lancamentos_pendentes[0]
                nfse_a_lancar.append(nfse)
                
                # Validate data
                errors, warnings = validar_dados_nfse(nfse)
                
                if errors:
                    raise Exception(f"Dados inválidos: {'; '.join(errors)}")
                
                if warnings:
                    log_message(f"⚠ Avisos de validação: {'; '.join(warnings)}")
                
                # Simulate SAP launch process
                import time
                time.sleep(2)  # Simulate network delay
                
                # Create SAP lancamento record
                lancamento = SapLancamento.create(
                    nfse=nfse,
                    numero_documento_sap=f"SAP{nfse.numero_nfse or '000000'}",
                    data_lancamento=datetime.date.today(),
                    valor_lancado=nfse.valor_total,
                    usuario_lancamento="Sistema",
                    status='sucesso',
                    observacao="Lançamento simulado via interface"
                )
                
                # Update NFSe status
                nfse.status = 'processado'
                nfse.save()
                
                log_message(f"✓ NFSe {nfse.numero_nfse} lançada no SAP com sucesso (Doc: {lancamento.numero_documento_sap})")
                status_text.value = "Lançamento concluído com sucesso!"
                
                # Refresh the list
                carregar_lancamentos_pendentes(None)
            else:
                status_text.value = "Nenhum lançamento pendente selecionado"
                log_message("⚠ Nenhum lançamento pendente selecionado")
        
        except Exception as ex:
            status_text.value = f"Erro no lançamento: {str(ex)}"
            log_message(f"✗ Erro no lançamento: {str(ex)}")
            
            # Create error lancamento record for tracking
            if 'nfse' in locals():
                SapLancamento.create(
                    nfse=nfse,
                    numero_documento_sap="ERRO",
                    data_lancamento=datetime.date.today(),
                    valor_lancado=nfse.valor_total,
                    usuario_lancamento="Sistema",
                    status='erro',
                    observacao=str(ex)
                )
        
        finally:
            # Reset UI
            lancar_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def lancar_todos_pendentes(e):
        """Launch all pending NFSe to SAP."""
        lancar_todos_btn.disabled = True
        page.update()
        
        status_text.value = "Iniciamento lançamento em lote..."
        progress_ring.visible = True
        page.update()
        
        try:
            if not lancamentos_pendentes:
                raise Exception("Nenhum lançamento pendente encontrado")
            
            sucessos = 0
            erros = 0
            
            for nfse in lancamentos_pendentes[:]:  # Copy list to avoid modification during iteration
                try:
                    # Validate data
                    errors, warnings = validar_dados_nfse(nfse)
                    
                    if errors:
                        raise Exception(f"Dados inválidos: {'; '.join(errors)}")
                    
                    # Simulate SAP launch
                    import time
                    time.sleep(0.5)  # Simulate network delay per item
                    
                    # Create SAP lancamento record
                    lancamento = SapLancamento.create(
                        nfse=nfse,
                        numero_documento_sap=f"SAP{nfse.numero_nfse or '000000'}",
                        data_lancamento=datetime.date.today(),
                        valor_lancado=nfse.valor_total,
                        usuario_lancamento="Sistema",
                        status='sucesso',
                        observacao="Lançamento em lote simulado"
                    )
                    
                    # Update NFSe status
                    nfse.status = 'processado'
                    nfse.save()
                    
                    sucessos += 1
                    log_message(f"✓ NFSe {nfse.numero_nfse} lançada com sucesso")
                    
                except Exception as ex:
                    erros += 1
                    log_message(f"✗ Erro na NFSe {nfse.numero_nfse or 'N/A'}: {str(ex)}")
                    
                    # Create error lancamento record
                    SapLancamento.create(
                        nfse=nfse,
                        numero_documento_sap="ERRO",
                        data_lancamento=datetime.date.today(),
                        valor_lancado=nfse.valor_total,
                        usuario_lancamento="Sistema",
                        status='erro',
                        observacao=str(ex)
                    )
            
            status_text.value = f"Lote concluído: {sucessos} sucessos, {erros} erros"
            log_message(f"✓ Lote concluído: {sucessos} lançamentos com sucesso, {erros} com erro")
            
            # Refresh the list
            carregar_lancamentos_pendentes(None)
            
        except Exception as ex:
            status_text.value = f"Erro no lote: {str(ex)}"
            log_message(f"✗ Erro no lançamento em lote: {str(ex)}")
        
        finally:
            # Reset UI
            lancar_todos_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def log_message(message):
        """Add message to log area."""
        log_area.controls.append(Text(message))
        # Keep only last 30 messages
        if len(log_area.controls) > 30:
            log_area.controls.pop(0)
        page.update()
    
    def atualizar_tabela_lancamentos():
        """Update the pending launches table."""
        tabela_lancamentos.rows.clear()
        
        for nfse in lancamentos_pendentes[-50:]:  # Show last 50
            tabela_lancamentos.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(nfse.numero_nfse or '')),
                        DataCell(Text(nfse.cnpj_emitente or '')),
                        DataCell(Text(nfse.cnpj_tomador or '')),
                        DataCell(Text(f"R$ {nfse.valor_total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))),
                        DataCell(Text(nfse.data_emissao.strftime('%d/%m/%Y') if nfse.data_emissao else '')),
                        DataCell(Text("Pendente")),
                    ]
                )
            )
        page.update()
    
    def limpar_log(e):
        """Clear the log area."""
        log_area.controls.clear()
        status_text.value = "Log limpo"
        page.update()
    
    # App UI Components
    title = Text("sapNFSe - Validação e Lançamento no SAP", size=20, weight=ft.FontWeight.BOLD)
    
    # Action buttons
    action_buttons = Row([
        carregar_btn := ElevatedButton(
            text="Carregar Pendentes",
            icon=Icons.REFRESH,
            on_click=carregar_lancamentos_pendentes,
        ),
        lancar_btn := ElevatedButton(
            text="Lançar Selecionado",
            icon=Icons.PLAY_ARROW,
            on_click=lancar_no_sap,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
            ),
        ),
        lancar_todos_btn := ElevatedButton(
            text="Lançar Todos Pendentes",
            icon=Icons.PLAY_LIST,
            on_click=lancar_todos_pendentes,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
            ),
        ),
        ElevatedButton(
            text="Limpar Log",
            icon=Icons.CLEAR_ALL,
            on_click=limpar_log,
        ),
    ], wrap=True, spacing=10)
    
    # Progress and status
    progress_ring = ProgressRing(width=20, height=20, visible=False)
    status_text = Text("Pronto para carregar lançamentos pendentes", size=14)
    
    # Action row with buttons and status
    action_row = Row([
        Column([
            action_buttons,
        ], expand=True),
        Column([
            progress_ring,
            status_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.END),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START)
    
    # Log area
    log_area = ListView(
        expand=True,
        spacing=5,
        padding=10,
        auto_scroll=True,
    )
    
    # Table for pending lancamentos
    tabela_lancamentos = DataTable(
        columns=[
            DataColumn(Text("Numero NFSe")),
            DataColumn(Text("CNPJ Emitente")),
            DataColumn(Text("CNPJ Tomador")),
            DataColumn(Text("Valor")),
            DataColumn(Text("Data Emissão")),
            DataColumn(Text("Status")),
        ],
        rows=[],  # Will be populated dynamically
        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=ft.border_radius.all(5),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
    )
    
    # Layout
    page.clean()
    page.add(
        AppBar(
            leading=Icon(Icons.WAREHOUSE),
            title=Text("sapNFSe - SAP"),
            center_title=False,
            bgcolor=ft.Colors.SURFACE_VARIANT,
        ),
        Column([
            title,
            action_row,
            Text("Log de Operações:", size=16, weight=ft.FontWeight.W_500),
            Container(
                content=log_area,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.border_radius.all(5),
                padding=10,
                height=120,
            ),
            Text("Lançamentos Pendentes no SAP:", size=16, weight=ft.FontWeight.W_500),
            Container(
                content=tabela_lancamentos,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.border_radius.all(5),
                padding=10,
                expand=True,
            ),
        ], 
        scroll=ft.ScrollMode.AUTO,
        padding=20,
        expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=sapNFSeApp)