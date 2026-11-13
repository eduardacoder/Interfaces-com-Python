import sqlite3
from datetime import datetime

import streamlit as st


DB_NAME = "gastos.db"
CATEGORIAS = ["Alimentação", "Transporte", "Lazer", "Moradia", "Outros"]


def conectar():
    return sqlite3.connect(DB_NAME)


def init_db():
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                data TEXT NOT NULL
            )
            """
        )


def obter_gastos():
    with conectar() as conn:
        return conn.execute(
            """
            SELECT id, descricao, valor, categoria, data
            FROM gastos
            ORDER BY id DESC
            """
        ).fetchall()


init_db()
st.set_page_config(page_title="Controle de Gastos", page_icon="💰")
st.title("Controle de Gastos Pessoais")

with st.form("adicionar_gasto", clear_on_submit=True):
    st.subheader("Cadastrar novo gasto")
    descricao = st.text_input("Descrição", placeholder="Ex.: Almoço")
    valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoria", CATEGORIAS)
    adicionar = st.form_submit_button("Adicionar gasto")

if adicionar:
    descricao = descricao.strip()
    if not descricao:
        st.error("Informe a descrição do gasto.")
    else:
        try:
            with conectar() as conn:
                conn.execute(
                    """
                    INSERT INTO gastos (descricao, valor, categoria, data)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        descricao,
                        valor,
                        categoria,
                        datetime.now().strftime("%d/%m/%Y"),
                    ),
                )
        except sqlite3.Error as error:
            st.error(f"Não foi possível salvar o gasto: {error}")
        else:
            st.rerun()

try:
    gastos = obter_gastos()
except sqlite3.Error as error:
    st.error(f"Não foi possível carregar os gastos: {error}")
    st.stop()

total = sum(gasto[2] for gasto in gastos)
st.metric("Total", f"R$ {total:.2f}")
st.subheader("Histórico")

if gastos:
    st.dataframe(
        [
            {
                "ID": gasto_id,
                "Data": data,
                "Descrição": descricao,
                "Categoria": categoria,
                "Valor (R$)": f"{valor:.2f}",
            }
            for gasto_id, descricao, valor, categoria, data in gastos
        ],
        use_container_width=True,
        hide_index=True,
    )

    opcoes = {
        gasto_id: f"#{gasto_id} — {descricao} (R$ {valor:.2f})"
        for gasto_id, descricao, valor, _, _ in gastos
    }
    selecionado = st.selectbox(
        "Selecione um gasto para excluir",
        options=list(opcoes),
        format_func=opcoes.get,
    )
    if st.button("Excluir gasto selecionado"):
        try:
            with conectar() as conn:
                cursor = conn.execute("DELETE FROM gastos WHERE id = ?", (selecionado,))
        except sqlite3.Error as error:
            st.error(f"Não foi possível excluir o gasto: {error}")
        else:
            if cursor.rowcount:
                st.rerun()
            else:
                st.error("O gasto selecionado não foi encontrado.")
else:
    st.info("Nenhum gasto cadastrado.")
