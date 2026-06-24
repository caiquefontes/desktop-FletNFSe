"""
ordens App - Vínculo de Compras
Responsável por importar pedidos de compra e vincular notas fiscais.
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
    FilePicker,
    FilePickerUploadEvent,
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
)
import os
import csv
from models.models import PedidoCompra, NFSe, initialize_database

# Initialize database
# r = initialize_database()

def ordensApp(page: Page):
    """Main function for ordens app."""
    
    # File picker for CSV/Excel selection
    file_picker = FilePicker()
    page.overlay.append(file_picker)
    
    def selecionar_arquivo(e):
        """Open file picker to select import file."""
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv", "xlsx", "xls"],
            dialog_title="Selecionar arquivo de Pedidos de Compra"
        )
    
    def process_import_file(e):
        """Process imported file (CSV or Excel)."""
        if not e.files:
            return
            
        file_path = e.files[0].path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Disable button during process
        import_btn.disabled = True
        page.update()
        
        # Show progress
        progress_ring.visible = True
        status_text.value = f"Processando arquivo {os.path.basename(file_path)}..."
        page.update()
        
        try:
            if file_ext == ".csv":
                pedidos = process_csv_file(file_path)
            elif file_ext in [".xlsx", ".xls"]:
                # For simplicity, we'll treat Excel as CSV in this example
                # In a real implementation, you'd use pandas or openpyxl
                pedidos = process_csv_file(file_path)  # Placeholder
            else:
                raise ValueError("Formato de arquivo não suportado")
            
            # Store imported pedidos
            pedidos_importados.extend(pedidos)
            
            # Update UI
            log_message(f"✓ Importados {len(pedidos)} pedidos de compra")
            atualizar_tabela_pedidos()
            status_text.value = "Importação concluída!"
            
        except Exception as ex:
            log_message(f"✗ Erro ao processar arquivo: {str(ex)}")
            status_text.value = "Erro na importação"
        
        finally:
            # Reset UI
            import_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def process_csv_file(file_path):
        """Process CSV file and extract purchase order data."""
        pedidos = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                # Try to detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        # Extract fields (adjust column names as needed)
                        numero_pedido = row.get('NumeroPedido') or row.get('numero_pedido') or row.get('Pedido') or ''
                        cnpj_fornecedor = row.get('CNPJFornecedor') or row.get('cnpj_fornecedor') or row.get('FornecedorCNPJ') or ''
                        valor_total = row.get('ValorTotal') or row.get('valor_total') or row.get('Valor') or '0'
                        data_pedido = row.get('DataPedido') or row.get('data_pedido') or row.get('Data') or ''
                        descricao = row.get('Descricao') or row.get('descricao') or row.get('Observacao') or ''
                        
                        if not numero_pedido:
                            continue  # Skip rows without pedido number
                        
                        # Clean and convert data
                        cnpj_fornecedor = ''.join(filter(str.isdigit, cnpj_fornecedor))  # Keep only digits
                        try:
                            valor_total = float(str(valor_total).replace('.', '').replace(',', '.'))
                        except ValueError:
                            valor_total = 0.0
                        
                        try:
                            # Try different date formats
                            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                                try:
                                    data_pedido_obj = datetime.strptime(data_pedido.strip(), fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                data_pedido_obj = None
                        except Exception:
                            data_pedido_obj = None
                        
                        # Create or update PedidoCompra record
                        pedido, created = PedidoCompra.get_or_create(
                            numero_pedido=numero_pedido.strip(),
                            defaults={
                                'cnpj_fornecedor': cnpj_fornecedor,
                                'valor_total': valor_total,
                                'data_pedido': data_pedido_obj.date() if data_pedido_obj else None,
                                'descricao': descricao.strip(),
                            }
                        )
                        
                        if not created:
                            # Update existing record
                            pedido.cnpj_fornecedor = cnpj_fornecedor
                            pedido.valor_total = valor_total
                            pedido.data_pedido = data_pedido_obj.date() if data_pedido_obj else pedido.data_pedido
                            pedido.descricao = descricao.strip()
                            pedido.save()
                        
                        pedidos.append(pedido)
                        
                    except Exception as ex:
                        log_message(f"⚠ Erro na linha {row_num}: {str(ex)}")
                        continue
                        
        except Exception as ex:
            raise Exception(f"Erro ao ler arquivo CSV: {str(ex)}")
        
        return pedidos
    
    def carregar_nfse_disponiveis(e):
        """Load NFSe records available for linking."""
        # Disable button during process
        load_nfse_btn.disabled = True
        page.update()
        
        status_text.value = "Carregando notas fiscais disponíveis..."
        progress_ring.visible = True
        page.update()
        
        try:
            # Get NFSe that are not yet linked to a pedido
            nfse_disponiveis.clear()
            nfse_records = NFSe.select().where(
                (NFSe.status == 'processado') & 
                (NFSe.pedidos.is_null(True))  # No linked pedidos
            ).order_by(NFSe.data_emissao.desc()).limit(200)
            
            for record in nfse_records:
                nfse_disponiveis.append(record)
            
            atualizar_tabela_nfse()
            status_text.value = f"Carregadas {len(nfse_disponiveis)} notas fiscais disponíveis"
            log_message(f"✓ Carregadas {len(nfse_disponiveis)} NFSe para vinculação")
            
        except Exception as ex:
            status_text.value = f"Erro ao carregar NFSe: {str(ex)}"
            log_message(f"✗ Erro ao carregar NFSe: {str(ex)}")
        
        finally:
            # Reset UI
            load_nfse_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def vincular_pedido_nfse(e):
        """Link selected pedido to selected NFSe."""
        # This would be implemented with actual selection logic
        # For now, just show a message
        log_message("Funcionalidade de vinculação em desenvolvimento")
        status_text.value = "Vinculação em desenvolvimento"
        page.update()
    
    def sugerir_vinculos_automaticos(e):
        """Suggest automatic links based on value or supplier matching."""
        # Disable button during process
        sugerir_btn.disabled = True
        page.update()
        
        status_text.value = "Analisando sugestões de vinculação..."
        progress_ring.visible = True
        page.update()
        
        try:
            # Simple matching by value (within 0.01 tolerance) or CNPJ
            sugestoes = []
            
            for pedido in pedidos_importados:
                if pedido.nfse is None:  # Only unbilled pedidos
                    for nfse in nfse_disponiveis:
                        match = False
                        motivo = ""
                        
                        # Match by CNPJ
                        if (pedido.cnpj_fornecedor and nfse.cnpj_emitente and 
                            pedido.cnpj_fornecedor == nfse.cnpj_emitente):
                            match = True
                            motivo = "CNPJ do fornecedor"
                        
                        # Match by value (within 1 cent tolerance)
                        elif abs(pedido.valor_total - nfse.valor_total) < 0.01:
                            match = True
                            motivo = "Valor idêntico"
                        
                        if match:
                            sugestoes.append({
                                'pedido': pedido,
                                'nfse': nfse,
                                'motivo': motivo
                            })
            
            # Display suggestions
            if sugestoes:
                log_message(f"✓ Encontradas {len(sugestoes)} sugestões de vinculação")
                for sug in sugestoes[:5]:  # Show first 5
                    log_message(f"  Pedido {sug['pedido'].numero_pedido} ↔ NFSe {sug['nfse'].numero_nfse} ({sug['motivo']})")
                if len(sugestoes) > 5:
                    log_message(f"  ... e mais {len(sugestoes) - 5} sugestões")
            else:
                log_message("⚠ Nenhuma sugestão de vinculação encontrada")
                
            status_text.value = f"Análise concluída: {len(sugestoes)} sugestões encontradas"
            
        except Exception as ex:
            status_text.value = f"Erro na análise: {str(ex)}"
            log_message(f"✗ Erro na análise de sugestões: {str(ex)}")
        
        finally:
            # Reset UI
            sugerir_btn.disabled = False
            progress_ring.visible = False
            page.update()
    
    def log_message(message):
        """Add message to log area."""
        log_area.controls.append(Text(message))
        # Keep only last 30 messages
        if len(log_area.controls) > 30:
            log_area.controls.pop(0)
        page.update()
    
    def atualizar_tabela_pedidos():
        """Update the purchase orders table."""
        tabela_pedidos.rows.clear()
        
        for pedido in pedidos_importados[-50:]:  # Show last 50
            tabela_pedidos.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(pedido.numero_pedido or '')),
                        DataCell(Text(pedido.cnpj_fornecedor or '')),
                        DataCell(Text(f"R$ {pedido.valor_total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))),
                        DataCell(Text(pedido.data_pedido.strftime('%d/%m/%Y') if pedido.data_pedido else '')),
                        DataCell(Text(pedido.descricao[:30] + '...' if len(pedido.descricao or '') > 30 else pedido.descricao or '')),
                        DataCell(Text("Vinculado" if pedido.nfse else "Disponível")),
                    ]
                )
            )
        page.update()
    
    def atualizar_tabela_nfse():
        """Update the available NFSe table."""
        tabela_nfse_disponivel.rows.clear()
        
        for nfse in nfse_disponiveis[-50:]:  # Show last 50
            tabela_nfse_disponivel.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(nfse.numero_nfse or '')),
                        DataCell(Text(nfse.cnpj_emitente or '')),
                        DataCell(Text(nfse.cnpj_tomador or '')),
                        DataCell(Text(f"R$ {nfse.valor_total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))),
                        DataCell(Text(nfse.data_emissao.strftime('%d/%m/%Y') if nfse.data_emissao else '')),
                        DataCell(Text("Disponível")),
                    ]
                )
            )
        page.update()
    
    # App UI Components
    title = Text("ordens - Vínculo de Compras", size=20, weight=ft.FontWeight.BOLD)
    
    # Import section
    import_section = Column([
        Text("Importação de Pedidos de Compra", size=16, weight=ft.FontWeight.W_500),
        Row([
            ElevatedButton(
                text="Selecionar Arquivo (CSV/Excel)",
                icon=Icons.UPLOAD_FILE,
                on_click=selecionar_arquivo,
            ),
            ElevatedButton(
                text="Importar Pedidos",
                icon=Icons.FILE_DOWNLOAD,
                on_click=lambda e: process_import_file(e) if hasattr(e, 'files') else None,
                disabled=True,  # Will be enabled after file selection
            ),
        ]),
    ])
    
    # Action buttons
    action_buttons = Row([
        load_nfse_btn := ElevatedButton(
            text="Carregar NFSe Disponíveis",
            icon=Icons.STORAGE,
            on_click=carregar_nfse_disponiveis,
        ),
        sugerir_btn := ElevatedButton(
            text="Sugerir Vínculos Automáticos",
            icon=Icons.AUTO_AWESOME,
            on_click=sugerir_vinculos_automaticos,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE,
                color=ft.Colors.WHITE,
            ),
        ),
        ElevatedButton(
            text="Vincular Selecionados",
            icon=Icons.LINK,
            on_click=vincular_pedido_nfse,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
            ),
        ),
    ], wrap=True, spacing=10)
    
    # Progress and status
    progress_ring = ProgressRing(width=20, height=20, visible=False)
    status_text = Text("Pronto para importar pedidos de compra", size=14)
    
    # Action row with buttons and status
    action_row = Row([
        Column([
            import_section,
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
    
    # Tables section
    tables_section = Column([
        Text("Pedidos de Compra Importados:", size=16, weight=ft.FontWeight.W_500),
        Container(
            content=DataTable(
                columns=[
                    DataColumn(Text("Numero")),
                    DataColumn(Text("CNPJ Fornecedor")),
                    DataColumn(Text("Valor")),
                    DataColumn(Text("Data")),
                    DataColumn(Text("Descrição")),
                    DataColumn(Text("Status")),
                ],
                rows=[],  # Will be populated dynamically
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.border_radius.all(5),
                vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.border_radius.all(5),
            padding=5,
            height=200,
        ),
        Text("Notas Fiscais Disponíveis para Vinculação:", size=16, weight=ft.FontWeight.W_500),
        Container(
            content=DataTable(
                columns=[
                    DataColumn(Text("Numero")),
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
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.border_radius.all(5),
            padding=5,
            height=200,
        ),
    ])
    
    # Layout
    page.clean()
    page.add(
        AppBar(
            leading=Icon(Icons.LIST_ALT),
            title=Text("ordens - Vínculo de Compras"),
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
            tables_section,
        ], 
        scroll=ft.ScrollMode.AUTO,
        padding=20,
        expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=ordensApp)