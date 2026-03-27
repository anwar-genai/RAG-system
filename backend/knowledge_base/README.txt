KNOWLEDGE BASE SETUP
====================

This directory stores documents used as the knowledge base for the RAG system.

TO ADD DOCUMENTS:
1. Place supported files in this directory (.pdf, .txt, .md, .docx, .csv)
2. The RAG system will automatically load and index them
3. Restart the Django server for changes to take effect

EXAMPLE:
If you add "company_handbook.pdf" or "company_handbook.docx", the system will extract text and create embeddings.
When a user asks a question, the system will retrieve relevant passages and cite the source.

For demo purposes, you can add docs containing:
- Company policies
- Product documentation
- FAQ documents
- Technical guides
- Research papers

The system extracts text and metadata (filename, page/row number) automatically.
