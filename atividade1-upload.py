from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import urllib.parse
import webbrowser

# 1. Banco de Dados SQLite Nativo
def init_db():
    with sqlite3.connect("gastos.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

# 2. Servidor Web Nativo
class FinanceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        # Buscar dados no SQLite
        with sqlite3.connect("gastos.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descricao, valor, categoria, data FROM gastos ORDER BY id DESC")
            gastos = cursor.fetchall()
            cursor.execute("SELECT SUM(valor) FROM gastos")
            total = cursor.fetchone()[0] or 0.0

        # Montar a Tabela em HTML
        linhas = ""
        for g in gastos:
            linhas += f"""
            <tr>
                <td>#{g[0]}</td>
                <td>{g[4]}</td>
                <td>{g[1]}</td>
                <td>{g[3]}</td>
                <td>R$ {g[2]:.2f}</td>
                <td><a href="/deletar?id={g[0]}" style="color:red; text-decoration:none;">❌ Excluir</a></td>
            </tr>
            """

        # Página Web Completa (HTML + CSS incorporados)
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>Controle de Gastos</title>
            <style>
                body {{ font-family: sans-serif; background: #f4f6f9; margin: 40px; }}
                .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                h2 {{ color: #2c3e50; margin-top: 0; }}
                input, select, button {{ padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 4px; }}
                button {{ background: #27ae60; color: white; border: none; cursor: pointer; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ border-bottom: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background: #34495e; color: white; }}
                .total {{ font-size: 18px; font-weight: bold; color: #e74c3c; float: right; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>💰 Controle de Gastos Pessoais</h2>
                <form action="/adicionar" method="POST">
                    <input type="text" name="descricao" placeholder="Descrição (ex: Almoço)" required>
                    <input type="number" step="0.01" name="valor" placeholder="Valor (R$)" required>
                    <select name="categoria">
                        <option>Alimentação</option>
                        <option>Transporte</option>
                        <option>Lazer</option>
                        <option>Moradia</option>
                        <option>Outros</option>
                    </select>
                    <button type="submit">➕ Adicionar Gasto</button>
                </form>
            </div>

            <div class="card">
                <span class="total">Total: R$ {total:.2f}</span>
                <h2>📋 Histórico</h2>
                <table>
                    <tr>
                        <th>ID</th><th>Data</th><th>Descrição</th><th>Categoria</th><th>Valor</th><th>Ação</th>
                    </tr>
                    {linhas if linhas else '<tr><td colspan="6">Nenhum gasto cadastrado.</td></tr>'}
                </table>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        dados = urllib.parse.parse_qs(post_data)

        descricao = dados.get('descricao', [''])[0].strip()
        valor_str = dados.get('valor', ['0'])[0]
        categoria = dados.get('categoria', ['Outros'])[0]

        from datetime import datetime
        data_atual = datetime.now().strftime("%d/%m/%Y")

        try:
            valor = float(valor_str)
            if valor > 0 and descricao:
                with sqlite3.connect("gastos.db") as conn:
                    conn.execute(
                        "INSERT INTO gastos (descricao, valor, categoria, data) VALUES (?, ?, ?, ?)",
                        (descricao, valor, categoria, data_atual)
                    )
                    conn.commit()
        except ValueError:
            pass

        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

# Rota de deleção simples
FinanceHandler.do_GET_old = FinanceHandler.do_GET
def handle_routes(self):
    if self.path.startswith('/deletar'):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        gasto_id = params.get('id', [None])[0]
        if gasto_id:
            with sqlite3.connect("gastos.db") as conn:
                conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
                conn.commit()
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()
    else:
        FinanceHandler.do_GET_old(self)

FinanceHandler.do_GET = handle_routes

if __name__ == "__main__":
    PORT = 8080
    print(f"Servidor rodando em http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    server = HTTPServer(('localhost', PORT), FinanceHandler)
    server.serve_forever()