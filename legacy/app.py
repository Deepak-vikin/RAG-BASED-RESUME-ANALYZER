import streamlit as st
import os
from rag_engine import *

st.set_page_config(page_title="Resume RAG Bot")
st.title("📄 Resume Analyzer")

uploaded_files = st.file_uploader(
    "Upload Resume PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    os.makedirs("resumes", exist_ok=True)

    pdf_paths = []
    for file in uploaded_files:
        path = f"resumes/{file.name}"
        with open(path, "wb") as f:
            f.write(file.read())
        pdf_paths.append(path)

    with st.spinner("Indexing resumes..."):
        docs = load_resumes(pdf_paths)
        chunks = split_documents(docs)
        vectorstore = create_vector_store(chunks)
        qa_chain = build_qa_chain(vectorstore)

    st.success("Resumes indexed successfully!")

query = st.text_input("Ask about candidates:")

if query:
    with st.spinner("Searching resumes..."):
        response = qa_chain(query)

    st.subheader("Answer")
    st.write(response["result"])

    st.subheader("Matched Resume Sources")
    for doc in response["source_documents"]:
        st.markdown(f"- **{doc.metadata.get('source')}**")
