import streamlit as st
import tempfile

# Banco JSON
from json_db import init_db, load_db

# PDFs e RAG
from src.pdf_loader import load_and_index_pdfs
from src.rag import process_query
from financeiro import extrair_transacoes_do_texto, salvar_transacoes_extraidas

# Serviços financeiros (pasta com acento "ç" e acento no 'ó')
from serviços.pix import enviar_pix
from serviços.pagamentos import pagar_boleto
from serviços.recargas import fazer_recarga
from serviços.emprestimos import contratar_emprestimo


# -----------------------------------------------------
# Inicializar banco ao iniciar o app
# -----------------------------------------------------
init_db()

st.set_page_config(page_title="Hub Financeiro Inteligente", layout="wide")
st.title("💸 Hub Financeiro Inteligente — PDFs + RAG + Simulação")


# -----------------------------------------------------
# ADICIONAR SALDO DE TESTE
# -----------------------------------------------------
if st.sidebar.button("💰 Adicionar saldo de teste (+ R$ 2.000)"):
    from json_db import load_db, save_db
    db = load_db()
    db["saldo"] += 2000
    save_db(db)
    st.sidebar.success("Saldo de teste adicionado!")
    st.experimental_rerun()


# -----------------------------------------------------
# ESTADO GLOBAL
# -----------------------------------------------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = []


# -----------------------------------------------------
# MENU LATERAL
# -----------------------------------------------------
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Enviar PDF", "Fazer Pergunta (RAG)", "PIX", "Pagamentos", "Recargas", "Empréstimos"]
)


# -----------------------------------------------------
# BOTÃO DE RESET GERAL
# -----------------------------------------------------
if st.sidebar.button("🔄 Resetar Sistema (Limpar tudo)"):
    from json_db import save_db
    save_db({"saldo": 0.0, "transacoes": []})
    st.sidebar.success("Sistema resetado com sucesso!")
    st.experimental_rerun()


# -----------------------------------------------------
# D A S H B O A R D
# -----------------------------------------------------
if menu == "Dashboard":
    st.header("📊 Dashboard Financeiro Inteligente")

    data = load_db()
    transacoes = data["transacoes"]

    st.metric("Saldo atual", f"R$ {data['saldo']:.2f}")
    st.markdown("---")

    # ... restante do código do dashboard ...


# -----------------------------------------------------
# ENVIAR PDF
# -----------------------------------------------------
elif menu == "Enviar PDF":
    st.header("📁 Enviar PDFs de extratos, faturas ou comprovantes")

    uploaded = st.file_uploader("Envie PDFs", type=["pdf"], accept_multiple_files=True)

    if uploaded:
        from langchain_community.document_loaders import PyPDFLoader

        st.session_state.pdf_bytes = [u.getvalue() for u in uploaded]

        with st.spinner("Lendo e indexando PDFs..."):
            st.session_state.vectorstore = load_and_index_pdfs(st.session_state.pdf_bytes)

        st.success("PDFs carregados com sucesso!")
        st.subheader("🔍 Extraindo transações dos PDFs...")

        for u in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(u.getvalue())
                tmp.flush()

                loader = PyPDFLoader(tmp.name)
                paginas = loader.load()

                texto = "\n".join([p.page_content for p in paginas])

                st.write("📄 Texto extraído:", texto[:1000])

                trans = extrair_transacoes_do_texto(texto)

                st.write("🔍 Transações encontradas:", trans)

                salvar_transacoes_extraidas(trans)

        st.success("Transações adicionadas ao banco!")


# -----------------------------------------------------
# PERGUNTA (RAG)
# -----------------------------------------------------
elif menu == "Fazer Pergunta (RAG)":
    st.header("🧠 Pergunte algo sobre os PDFs")

    pergunta = st.text_input("Digite sua pergunta:")

    if st.button("Enviar"):
        if not st.session_state.vectorstore:
            st.error("Nenhum PDF carregado ainda.")
        else:
            resposta, fontes = process_query(pergunta, st.session_state.vectorstore)
            st.markdown("### Resposta")
            st.write(resposta)

            st.markdown("### Fontes utilizadas")
            for f in fontes:
                st.write(f["texto"])


# -----------------------------------------------------
# PIX
# -----------------------------------------------------
elif menu == "PIX":
    st.header("⚡ Fazer PIX")

    chave = st.text_input("Chave PIX")
    valor = st.number_input("Valor", min_value=1.0)

    if st.button("Enviar PIX"):
        ok, msg = enviar_pix(chave, valor)
        st.success(msg) if ok else st.error(msg)


# -----------------------------------------------------
# PAGAMENTOS
# -----------------------------------------------------
elif menu == "Pagamentos":
    st.header("💳 Pagamento de Boleto")

    codigo = st.text_input("Código do boleto")
    valor = st.number_input("Valor", min_value=1.0)

    if st.button("Pagar"):
        ok, msg = pagar_boleto(codigo, valor)
        st.success(msg) if ok else st.error(msg)


# -----------------------------------------------------
# RECARGAS
# -----------------------------------------------------
elif menu == "Recargas":
    st.header("📱 Recarga de celular")

    numero = st.text_input("Número")
    operadora = st.selectbox("Operadora", ["Vivo", "Claro", "TIM", "Oi"])
    valor = st.number_input("Valor", min_value=1.0)

    if st.button("Recarregar"):
        ok, msg = fazer_recarga(numero, operadora, valor)
        st.success(msg) if ok else st.error(msg)


# -----------------------------------------------------
# EMPRÉSTIMOS
# -----------------------------------------------------
elif menu == "Empréstimos":
    st.header("🏦 Simulação de Empréstimo")

    valor = st.number_input("Valor desejado", min_value=100.0)

    if st.button("Contratar"):
        ok, total = contratar_emprestimo(valor)
        if ok:
            st.success(f"Empréstimo aprovado! Total final: R$ {total}")
        else:
            st.error(total)
