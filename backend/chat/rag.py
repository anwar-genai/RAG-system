import csv
import hashlib
import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.callbacks import get_openai_callback
from openai import APIConnectionError, APITimeoutError
from PyPDF2 import PdfReader
from typing import List, Dict, Tuple, Any
from pathlib import Path

NO_ANSWER_FALLBACK = "I don't have information about this in the provided documents."
UPSTREAM_ERROR_MSG = "Couldn't reach the AI provider. Check your network or VPN and try again."
GENERIC_ERROR_MSG = "Something went wrong generating a response. Please try again."


class UpstreamUnavailable(Exception):
    """Raised when the LLM/embedding provider is unreachable (network / proxy)."""

def _openai_kwargs() -> dict:
    """Return extra kwargs for OpenAI clients (e.g. proxy support via OPENAI_PROXY env var).

    Sets a connect timeout so a blocked api.openai.com fails fast (~5s) instead of
    holding each request for the full OS TCP retry window (~60s)."""
    import httpx
    timeout = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
    proxy = os.environ.get("OPENAI_PROXY", "").strip()
    if proxy:
        return {
            "http_client": httpx.Client(proxy=proxy, timeout=timeout),
            "http_async_client": httpx.AsyncClient(proxy=proxy, timeout=timeout),
        }
    return {
        "http_client": httpx.Client(timeout=timeout),
        "http_async_client": httpx.AsyncClient(timeout=timeout),
    }

class RAGSystem:
    """RAG (Retrieval-Augmented Generation) system for chat"""

    def __init__(self):
        kwargs = _openai_kwargs()
        # max_retries=0 + explicit timeout so a blocked upstream errors out in
        # ~5-10s instead of the SDK's default 3-attempt × OS-TCP-retry chain
        # (which can be 60-180s on Windows).
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            max_retries=0,
            timeout=10.0,
            **kwargs,
        )
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            max_retries=0,
            timeout=30.0,
            **kwargs,
        )
        self.llm_streaming = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            streaming=True,
            max_retries=0,
            timeout=30.0,
            **kwargs,
        )
        self.kb_path = Path(__file__).parent.parent / "knowledge_base"
        self.vector_store_dir = Path(__file__).parent.parent / "vector_store"
        self.vector_store_path = self.vector_store_dir / "faiss_index"
        self.manifest_path = self.vector_store_dir / "manifest.json"
        self.vector_store = None
        self.retriever = None
        self.failed_files: List[Tuple[str, str]] = []
        self._initialize_knowledge_base()

    # -------------------------
    # Knowledge base setup
    # -------------------------
    def _initialize_knowledge_base(self):
        self.kb_path.mkdir(exist_ok=True)
        self.vector_store_dir.mkdir(exist_ok=True)
        current_manifest = self._build_kb_manifest()

        if self._can_use_cached_index(current_manifest):
            self.vector_store = FAISS.load_local(
                str(self.vector_store_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            print("Loaded cached vector store from disk.")
        else:
            print("Rebuilding vector store (knowledge base changed or cache missing).")
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

            self.vector_store.save_local(str(self.vector_store_path))
            self._write_manifest(current_manifest)
            print("Vector store saved to disk.")

        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

    def _load_knowledge_documents(self) -> List[Document]:
        documents = []
        self.failed_files: List[Tuple[str, str]] = []

        for file_path in self.kb_path.iterdir():
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            supported = {".pdf", ".txt", ".md", ".docx", ".csv"}
            if ext not in supported:
                continue

            try:
                if ext == ".pdf":
                    loaded = self._load_pdf(file_path)
                elif ext in {".txt", ".md"}:
                    loaded = self._load_text_like_file(file_path)
                elif ext == ".docx":
                    loaded = self._load_docx(file_path)
                elif ext == ".csv":
                    loaded = self._load_csv(file_path)
                else:
                    loaded = []
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
                self.failed_files.append((file_path.name, f"{type(e).__name__}: {e}"))
                continue

            if not loaded:
                # File parsed without error but produced no extractable text — flag it
                # so callers can mark the DB row as failed rather than "indexed".
                self.failed_files.append((file_path.name, "no extractable text"))
                continue

            documents.extend(loaded)

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

    def _build_kb_manifest(self) -> Dict[str, Any]:
        files = []
        supported_exts = {".pdf", ".txt", ".md", ".docx", ".csv"}

        for file_path in sorted(self.kb_path.iterdir(), key=lambda p: p.name.lower()):
            if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
                continue

            files.append(
                {
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "sha256": self._file_sha256(file_path),
                }
            )

        combined_hash = hashlib.sha256(
            json.dumps(files, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {"version": 1, "files": files, "combined_hash": combined_hash}

    def _file_sha256(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _can_use_cached_index(self, current_manifest: Dict[str, Any]) -> bool:
        if not self.vector_store_path.exists() or not self.manifest_path.exists():
            return False

        try:
            saved_manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return False

        return saved_manifest.get("combined_hash") == current_manifest.get("combined_hash")

    def _write_manifest(self, manifest: Dict[str, Any]) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

    # -------------------------
    # Chat
    # -------------------------
    def chat(
        self,
        user_message: str,
        chat_history: List[Dict]
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """Returns (answer, sources, usage). `usage` is {tokens_in, tokens_out, cost_usd}
        — captures LLM call only; embedding cost is tracked separately if needed."""

        formatted_history = "\n".join(
            f"{m['type'].capitalize()}: {m['content']}"
            for m in chat_history[-4:]
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are a helpful AI assistant.
Answer ONLY using the provided document context.
If the answer is not present, respond with EXACTLY this sentence and nothing else:
I don't have information about this in the provided documents.

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
            with get_openai_callback() as cb:
                result = retrieval_chain.invoke(
                    {
                        "input": user_message,
                        "chat_history": formatted_history
                    }
                )

            answer = result["answer"]
            context_docs = result["context"]

            sources = [] if self._is_no_answer(answer) else self._extract_sources(context_docs)
            usage = {
                "tokens_in": cb.prompt_tokens,
                "tokens_out": cb.completion_tokens,
                "cost_usd": round(cb.total_cost, 6),
            }

            return answer, sources, usage

        except (APITimeoutError, APIConnectionError) as e:
            import traceback
            traceback.print_exc()
            raise UpstreamUnavailable(UPSTREAM_ERROR_MSG) from e

    def generate_title(self, user_message: str, assistant_reply: str) -> str:
        """Produce a short (<=6 word) title from the first exchange.
        Returns empty string on any failure — caller falls back to message preview."""
        prompt = (
            "Summarize this conversation in a short descriptive title of 3-6 words. "
            "Return ONLY the title, no quotes, no punctuation at the end.\n\n"
            f"User: {user_message[:500]}\n"
            f"Assistant: {assistant_reply[:500]}"
        )
        try:
            resp = self.llm.invoke(prompt)
            text = (resp.content if hasattr(resp, 'content') else str(resp)).strip()
            # Strip quotes/trailing punctuation defensively
            text = text.strip('"\'').rstrip('.').strip()
            return text[:60]
        except Exception:
            return ""

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
If the answer is not present, respond with EXACTLY this sentence and nothing else:
I don't have information about this in the provided documents.

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

            answer_parts = []
            with get_openai_callback() as cb:
                for chunk in document_chain.stream(inputs):
                    if isinstance(chunk, dict) and "answer" in chunk:
                        part = chunk["answer"]
                    elif hasattr(chunk, "content"):
                        part = chunk.content
                    else:
                        part = str(chunk) if chunk else ""
                    if part:
                        answer_parts.append(part)
                        yield ("chunk", part)

            usage = {
                "tokens_in": cb.prompt_tokens,
                "tokens_out": cb.completion_tokens,
                "cost_usd": round(cb.total_cost, 6),
            }
            yield ("usage", usage)

            final_answer = "".join(answer_parts)
            final_sources = [] if self._is_no_answer(final_answer) else sources
            yield ("done", final_sources)

        except (APITimeoutError, APIConnectionError):
            import traceback
            traceback.print_exc()
            yield ("error", UPSTREAM_ERROR_MSG)
        except Exception:
            import traceback
            traceback.print_exc()
            yield ("error", GENERIC_ERROR_MSG)

    # -------------------------
    # Source citation
    # -------------------------
    @staticmethod
    def _is_no_answer(answer: str) -> bool:
        if not answer:
            return True
        normalized = answer.strip().rstrip(".").strip().lower()
        return normalized == NO_ANSWER_FALLBACK.strip().rstrip(".").strip().lower()

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


def reload_rag_system() -> RAGSystem:
    """Force rebuild/load of the singleton RAG instance."""
    global _rag_instance
    _rag_instance = RAGSystem()
    return _rag_instance