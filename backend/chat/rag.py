import csv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from PyPDF2 import PdfReader
from typing import List, Dict, Tuple
from pathlib import Path

class RAGSystem:
    """RAG (Retrieval-Augmented Generation) system for chat"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0  # important for RAG
        )
        self.llm_streaming = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            streaming=True,
        )
        self.vector_store = None
        self.retriever = None
        self._initialize_knowledge_base()

    # -------------------------
    # Knowledge base setup
    # -------------------------
    def _initialize_knowledge_base(self):
        documents = self._load_knowledge_documents()

        if not documents:
            dummy_doc = Document(
                page_content="This is a demo RAG system.",
                metadata={"source": "demo", "page": 1}
            )
            self.vector_store = FAISS.from_documents(
                [dummy_doc], self.embeddings
            )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = splitter.split_documents(documents)

            self.vector_store = FAISS.from_documents(
                chunks, self.embeddings
            )

        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

    def _load_knowledge_documents(self) -> List[Document]:
        documents = []
        kb_path = Path(__file__).parent.parent / "knowledge_base"
        kb_path.mkdir(exist_ok=True)

        for file_path in kb_path.iterdir():
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            try:
                if ext == ".pdf":
                    documents.extend(self._load_pdf(file_path))
                elif ext in {".txt", ".md"}:
                    documents.extend(self._load_text_like_file(file_path))
                elif ext == ".docx":
                    documents.extend(self._load_docx(file_path))
                elif ext == ".csv":
                    documents.extend(self._load_csv(file_path))
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")

        return documents

    def _load_pdf(self, pdf_file: Path) -> List[Document]:
        docs = []
        reader = PdfReader(pdf_file)
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": pdf_file.name, "page": page_num},
                    )
                )
        return docs

    def _load_text_like_file(self, file_path: Path) -> List[Document]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            return []
        return [
            Document(
                page_content=text,
                metadata={"source": file_path.name, "page": 1},
            )
        ]

    def _load_docx(self, file_path: Path) -> List[Document]:
        # Import lazily so the rest of the app still runs if python-docx is missing.
        from docx import Document as DocxDocument

        docx = DocxDocument(file_path)
        text_parts = [p.text.strip() for p in docx.paragraphs if p.text and p.text.strip()]
        full_text = "\n".join(text_parts)
        if not full_text:
            return []
        return [
            Document(
                page_content=full_text,
                metadata={"source": file_path.name, "page": 1},
            )
        ]

    def _load_csv(self, file_path: Path) -> List[Document]:
        docs = []
        with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return docs

        headers = rows[0]
        data_rows = rows[1:] if len(rows) > 1 else []

        for row_num, row in enumerate(data_rows, start=2):
            cells = []
            for idx, value in enumerate(row):
                header = headers[idx] if idx < len(headers) else f"column_{idx + 1}"
                cells.append(f"{header}: {value}")

            row_text = "\n".join(cells).strip()
            if row_text:
                docs.append(
                    Document(
                        page_content=row_text,
                        metadata={"source": file_path.name, "page": row_num},
                    )
                )

        # Fallback for header-only CSV
        if not docs:
            header_text = ", ".join(headers).strip()
            if header_text:
                docs.append(
                    Document(
                        page_content=f"CSV headers: {header_text}",
                        metadata={"source": file_path.name, "page": 1},
                    )
                )

        return docs

    # -------------------------
    # Chat
    # -------------------------
    def chat(
        self,
        user_message: str,
        chat_history: List[Dict]
    ) -> Tuple[str, List[str]]:

        formatted_history = "\n".join(
            f"{m['type'].capitalize()}: {m['content']}"
            for m in chat_history[-4:]
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are a helpful AI assistant.
Answer ONLY using the provided document context.
If the answer is not present, say:
"I don't have information about this in the provided documents."

Conversation history:
{chat_history}

Document context:
{context}

User question:
{input}

Answer clearly and concisely.
"""
        )

        document_chain = create_stuff_documents_chain(
            self.llm,
            prompt
        )

        retrieval_chain = create_retrieval_chain(
            self.retriever,
            document_chain
        )

        try:
            result = retrieval_chain.invoke(
                {
                    "input": user_message,
                    "chat_history": formatted_history
                }
            )

            answer = result["answer"]
            context_docs = result["context"]

            sources = self._extract_sources(context_docs)

            return answer, sources

        except Exception as e:
            print("RAG error:", e)
            return "Sorry, something went wrong.", []

    def chat_stream(
        self,
        user_message: str,
        chat_history: List[Dict],
    ):
        """
        Stream the RAG response token-by-token.
        Yields (content_chunk, None) for text, then (None, sources) at the end.
        """
        formatted_history = "\n".join(
            f"{m['type'].capitalize()}: {m['content']}"
            for m in chat_history[-4:]
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are a helpful AI assistant.
Answer ONLY using the provided document context.
If the answer is not present, say:
"I don't have information about this in the provided documents."

Conversation history:
{chat_history}

Document context:
{context}

User question:
{input}

Answer clearly and concisely.
"""
        )

        document_chain = create_stuff_documents_chain(
            self.llm_streaming,
            prompt,
        )

        try:
            # Get context first (no streaming)
            documents = self.retriever.invoke(user_message)
            sources = self._extract_sources(documents)

            inputs = {
                "input": user_message,
                "chat_history": formatted_history,
                "context": documents,
            }

            for chunk in document_chain.stream(inputs):
                if isinstance(chunk, dict) and "answer" in chunk:
                    part = chunk["answer"]
                elif hasattr(chunk, "content"):
                    part = chunk.content
                else:
                    part = str(chunk) if chunk else ""
                if part:
                    yield ("chunk", part)

            yield ("done", sources)

        except Exception as e:
            print("RAG stream error:", e)
            yield ("chunk", "Sorry, something went wrong.")
            yield ("done", [])

    # -------------------------
    # Source citation
    # -------------------------
    def _extract_sources(
        self,
        docs: List[Document]
    ) -> List[str]:

        citations = []
        seen = set()

        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            citation = f"{source} - Page {page}"

            if citation not in seen:
                citations.append(citation)
                seen.add(citation)

        return citations


# -------------------------
# Singleton instance
# -------------------------
_rag_instance = None


def get_rag_system() -> RAGSystem:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance