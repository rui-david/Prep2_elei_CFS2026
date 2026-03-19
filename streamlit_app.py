import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Eleições do Clube Futebol os Sanjoanenses 2026", layout="centered")

# CORES
st.markdown("""
<style>
.stButton>button {
    background-color: #004AAD;
    color: white;
    border-radius: 8px;
    height: 3em;
}
h1 {
    color: #004AAD;
}
</style>
""", unsafe_allow_html=True)

# LOGO + TITULO
col1, col2 = st.columns([1,3])
with col1:
    st.image("logo.png", width=80)
with col2:
    st.markdown("<h1>Eleições do Clube Futebol os Sanjoanenses 2026</h1>", unsafe_allow_html=True)

# -------------------------
# BASE DE DADOS
# -------------------------
conn = sqlite3.connect("dados.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    numero_documento TEXT UNIQUE,
    nome TEXT,
    senha TEXT,
    tipo TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votos (
    numero_documento TEXT,
    candidato TEXT
)
""")

conn.commit()

# -------------------------
# FUNÇÕES
# -------------------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_documentos_validos():
    df = pd.read_excel("dados.xlsx")
    return df["numero_documento"].astype(str).tolist()

def criar_usuario(doc, nome, senha, tipo="user"):
    try:
        cursor.execute(
            "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
            (doc, nome, hash_senha(senha), tipo)
        )
        conn.commit()
        return True
    except:
        return False

def login(doc, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE numero_documento=? AND senha=?",
        (doc, hash_senha(senha))
    )
    return cursor.fetchone()

def votar(doc, candidato):
    cursor.execute("SELECT * FROM votos WHERE numero_documento=?", (doc,))
    if cursor.fetchone():
        return False
    cursor.execute("INSERT INTO votos VALUES (?, ?)", (doc, candidato))
    conn.commit()
    return True

# -------------------------
# ADMIN PADRÃO
# -------------------------
cursor.execute("SELECT * FROM usuarios WHERE tipo='admin'")
if not cursor.fetchone():
    criar_usuario("admin", "Administrador", "admin123", "admin")

# -------------------------
# MENU
# -------------------------
menu = ["Login", "Registrar"]
escolha = st.sidebar.selectbox("Menu", menu)

# -------------------------
# LOGIN
# -------------------------
if escolha == "Login":
    st.subheader("Login")

    doc = st.text_input("Número de Documento")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = login(doc, senha)

        if user:
            st.success(f"Bem-vindo, {user[1]}")

            # ---------------- ADMIN ----------------
            if user[3] == "admin":
                st.subheader("Painel do Administrador")

                df = pd.read_sql_query("SELECT * FROM votos", conn)

                if not df.empty:
                    resultado = df["candidato"].value_counts()
                    percentagem = round((resultado / resultado.sum()) * 100, 2)

                    st.write("Resultados:")
                    st.table(percentagem)

                    st.bar_chart(resultado)
                else:
                    st.info("Nenhum voto ainda.")

            # ---------------- USUÁRIO ----------------
            else:
                st.subheader("Votação")

                candidato = st.selectbox("Escolha candidato", ["Lista A", "Lista B", "Lista C"])

                if st.button("Votar"):
                    if votar(doc, candidato):
                        st.success("Voto registado com sucesso!")
                    else:
                        st.warning("Já votaste!")

        else:
            st.error("Dados inválidos")

# -------------------------
# REGISTRO
# -------------------------
elif escolha == "Registrar":
    st.subheader("Criar Conta")

    doc = st.text_input("Número de Documento")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    confirmar = st.text_input("Confirmar Senha", type="password")

    if st.button("Registrar"):
        docs_validos = carregar_documentos_validos()

        if doc not in docs_validos:
            st.error("Documento não autorizado!")
        elif senha != confirmar:
            st.warning("Senhas não coincidem")
        elif criar_usuario(doc, nome, senha):
            st.success("Conta criada com sucesso")
        else:
            st.error("Já existe")
