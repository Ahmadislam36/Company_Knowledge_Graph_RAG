from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import DOCUMENTS_PATH


def load_documents():
    """Load all Markdown documents from the documents directory."""

    loader = DirectoryLoader(
        str(DOCUMENTS_PATH),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} documents")

    return documents


def split_documents(documents):
    """Split documents into smaller chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    return chunks


if __name__ == "__main__":
    documents = load_documents()
    chunks = split_documents(documents)

    print("\n--- Sample Chunks ---\n")

    for i, chunk in enumerate(chunks[:5]):
        print(f"Chunk {i + 1}")
        print(f"Source: {chunk.metadata.get('source')}")
        print(chunk.page_content)
        print("-" * 60)