
import sqlite3
from datetime import date
from pathlib import Path

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Meu Assistente de Tarefas",
    page_icon="✅",
    layout="wide",
)

# Banco local: adequado para testes iniciais.
DB_PATH = Path("tarefas.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                categoria TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                vencimento TEXT NOT NULL,
                concluida INTEGER DEFAULT 0
            )
        """)


def adicionar_tarefa(titulo, descricao, categoria,
                     prioridade, vencimento):
    with conectar() as conn:
        conn.execute("""
            INSERT INTO tarefas
            (titulo, descricao, categoria, prioridade,
             vencimento, concluida)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (
            titulo, descricao, categoria,
            prioridade, vencimento.isoformat()
        ))


def carregar_tarefas():
    with conectar() as conn:
        return pd.read_sql_query(
            "SELECT * FROM tarefas ORDER BY vencimento, id",
            conn,
        )


def atualizar_status(id_tarefa, concluida):
    with conectar() as conn:
        conn.execute(
            "UPDATE tarefas SET concluida = ? WHERE id = ?",
            (int(concluida), int(id_tarefa)),
        )


def excluir_tarefa(id_tarefa):
    with conectar() as conn:
        conn.execute(
            "DELETE FROM tarefas WHERE id = ?",
            (int(id_tarefa),),
        )


inicializar_banco()

st.title("✅ Meu Assistente Pessoal")
st.write("Organize suas tarefas, prazos e prioridades.")

tarefas = carregar_tarefas()
hoje = date.today().isoformat()

pendentes = tarefas[tarefas["concluida"] == 0]
concluidas = tarefas[tarefas["concluida"] == 1]
atrasadas = pendentes[pendentes["vencimento"] < hoje]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(tarefas))
c2.metric("Pendentes", len(pendentes))
c3.metric("Concluídas", len(concluidas))
c4.metric("Atrasadas", len(atrasadas))

st.divider()
st.subheader("➕ Nova tarefa")

with st.form("nova_tarefa", clear_on_submit=True):
    titulo = st.text_input("Nome da tarefa")
    descricao = st.text_area("Descrição")
    categoria = st.selectbox(
        "Categoria",
        ["Pessoal", "Trabalho", "Estudos", "Casa", "Outros"],
    )
    prioridade = st.selectbox(
        "Prioridade", ["Alta", "Média", "Baixa"]
    )
    vencimento = st.date_input(
        "Prazo", value=date.today()
    )

    enviar = st.form_submit_button("Salvar tarefa")

    if enviar:
        if not titulo.strip():
            st.error("Informe o nome da tarefa.")
        else:
            adicionar_tarefa(
                titulo.strip(), descricao, categoria,
                prioridade, vencimento,
            )
            st.success("Tarefa cadastrada!")
            st.rerun()

st.divider()
st.subheader("📋 Minhas tarefas")

f1, f2 = st.columns(2)

with f1:
    filtro_status = st.selectbox(
        "Mostrar",
        ["Todas", "Pendentes", "Concluídas", "Atrasadas"],
    )

with f2:
    categorias = ["Todas"] + sorted(
        tarefas["categoria"].dropna().unique().tolist()
    )
    filtro_categoria = st.selectbox("Categoria", categorias)

visualizar = tarefas.copy()

if filtro_status == "Pendentes":
    visualizar = visualizar[visualizar["concluida"] == 0]
elif filtro_status == "Concluídas":
    visualizar = visualizar[visualizar["concluida"] == 1]
elif filtro_status == "Atrasadas":
    visualizar = visualizar[
        (visualizar["concluida"] == 0)
        & (visualizar["vencimento"] < hoje)
    ]

if filtro_categoria != "Todas":
    visualizar = visualizar[
        visualizar["categoria"] == filtro_categoria
    ]

if visualizar.empty:
    st.info("Nenhuma tarefa encontrada.")
else:
    for _, tarefa in visualizar.iterrows():
        id_tarefa = int(tarefa["id"])
        feita = bool(tarefa["concluida"])
        vencida = not feita and tarefa["vencimento"] < hoje

        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 2, 1])

            with col1:
                st.markdown(
                    f"**{'✅' if feita else '⬜'} {tarefa['titulo']}**"
                )
                if tarefa["descricao"]:
                    st.write(tarefa["descricao"])

                st.caption(
                    f"{tarefa['categoria']} · "
                    f"Prioridade: {tarefa['prioridade']} · "
                    f"Prazo: {tarefa['vencimento']}"
                )
                if vencida:
                    st.warning("Prazo vencido!")

            with col2:
                novo_status = st.checkbox(
                    "Concluída",
                    value=feita,
                    key=f"status_{id_tarefa}",
                )
                if novo_status != feita:
                    atualizar_status(id_tarefa, novo_status)
                    st.rerun()

            with col3:
                if st.button(
                    "Excluir",
                    key=f"excluir_{id_tarefa}",
                ):
                    excluir_tarefa(id_tarefa)
                    st.rerun()

st.caption("Meu Assistente Pessoal · Versão 1.0")
