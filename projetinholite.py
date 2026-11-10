import sys
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt


class DatabaseManager:
    """Gerencia a conexão e operações com o banco de dados SQLite."""

    def __init__(self, db_name="gastos_qt.db"):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()

    def adicionar_gasto(self, descricao: str, valor: float, categoria: str) -> bool:
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO gastos (descricao, valor, categoria, data) VALUES (?, ?, ?, ?)",
                    (descricao, valor, categoria, data_atual)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def obter_gastos(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descricao, valor, categoria, data FROM gastos ORDER BY id DESC")
            return cursor.fetchall()

    def remover_gasto(self, gasto_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
            conn.commit()
            return cursor.rowcount > 0


class FinanceApp(QMainWindow):
    """Janela Principal da aplicação PySide6."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()

        self.setWindowTitle("Controle de Gastos Pessoais - PySide6")
        self.resize(750, 550)

        self._setup_ui()
        self.carregar_dados()


    def _setup_ui(self):
        # Widget Central e Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Formulário de Cadastro (QGroupBox + QHBoxLayout)
        form_box = QGroupBox(" Cadastrar Novo Gasto ")
        form_layout = QHBoxLayout()

        self.input_descricao = QLineEdit()
        self.input_descricao.setPlaceholderText("Descrição (ex: Almoço)")

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("Valor R$ (ex: 45.90)")

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems([
            "Alimentação", "Transporte", "Lazer", "Moradia", "Saúde", "Outros"
        ])

        btn_adicionar = QPushButton("➕ Adicionar")
        btn_adicionar.clicked.connect(self.adicionar_gasto)

        form_layout.addWidget(QLabel("Descrição:"))
        form_layout.addWidget(self.input_descricao)
        form_layout.addWidget(QLabel("Valor:"))
        form_layout.addWidget(self.input_valor)
        form_layout.addWidget(QLabel("Categoria:"))
        form_layout.addWidget(self.combo_categoria)
        form_layout.addWidget(btn_adicionar)

        form_box.setLayout(form_layout)
        main_layout.addWidget(form_box)

        # 2. Tabela de Lançamentos (QTableWidget)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["ID", "Data", "Descrição", "Categoria", "Valor (R$)"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.tabela)

        # 3. Rodapé com Ações e Totalizador
        footer_layout = QHBoxLayout()

        btn_remover = QPushButton("🗑️ Remover Selecionado")
        btn_remover.clicked.connect(self.remover_gasto_selecionado)
        footer_layout.addWidget(btn_remover)

        footer_layout.addStretch()

        self.lbl_total = QLabel("Total Acumulado: R$ 0.00")
        self.lbl_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #2C3E50;")
        footer_layout.addWidget(self.lbl_total)

        main_layout.addLayout(footer_layout)

    def adicionar_gasto(self):
        descricao = self.input_descricao.text().strip()
        valor_str = self.input_valor.text().strip().replace(",", ".")
        categoria = self.combo_categoria.currentText()

        if not descricao:
            QMessageBox.warning(self, "Campo Vazio", "Por favor, informe a descrição do gasto.")
            return

        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Informe um valor numérico válido maior que zero.")
            return

        if self.db.adicionar_gasto(descricao, valor, categoria):
            self.input_descricao.clear()
            self.input_valor.clear()
            self.carregar_dados()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar o gasto no banco de dados.")

    def carregar_dados(self):
        gastos = self.db.obter_gastos()
        self.tabela.setRowCount(0)
        total_geral = 0.0

        for row_idx, (gasto_id, desc, valor, cat, data) in enumerate(gastos):
            self.tabela.insertRow(row_idx)
            
            # Preenchendo as colunas da tabela
            item_id = QTableWidgetItem(str(gasto_id))
            item_id.setTextAlignment(Qt.AlignCenter)
            
            self.tabela.setItem(row_idx, 0, item_id)
            self.tabela.setItem(row_idx, 1, QTableWidgetItem(data))
            self.tabela.setItem(row_idx, 2, QTableWidgetItem(desc))
            self.tabela.setItem(row_idx, 3, QTableWidgetItem(cat))
            
            item_valor = QTableWidgetItem(f"R$ {valor:.2f}")
            item_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(row_idx, 4, item_valor)

            total_geral += valor

        self.lbl_total.setText(f"Total Acumulado: R$ {total_geral:.2f}")

    def remover_gasto_selecionado(self):
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma linha da tabela para remover.")
            return

        gasto_id = int(self.tabela.item(linha_selecionada, 0).text())
        confirmacao = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente remover o gasto #{gasto_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacao == QMessageBox.Yes:
            if self.db.remover_gasto(gasto_id):
                self.carregar_dados()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir gasto do banco.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceApp()
    window.show()
    sys.exit(app.exec())

    