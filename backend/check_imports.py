#!/usr/bin/env python
import sys

# Try different import paths
print("Testing import paths for create_retrieval_chain...")

paths_to_try = [
    ("langchain", "create_retrieval_chain"),
    ("langchain.chains", "create_retrieval_chain"),
    ("langchain.chains.retrieval", "create_retrieval_chain"),
    ("langchain_core", "create_retrieval_chain"),
    ("langchain_core.chains", "create_retrieval_chain"),
    ("langchain_core.runnables", "create_retrieval_chain"),
]

for module_name, func_name in paths_to_try:
    try:
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        print(f"✓ Found: from {module_name} import {func_name}")
    except (ImportError, AttributeError) as e:
        print(f"✗ Not found: from {module_name} import {func_name}")

print("\nTesting import paths for create_stuff_documents_chain...")

paths_to_try2 = [
    ("langchain", "create_stuff_documents_chain"),
    ("langchain.chains", "create_stuff_documents_chain"),
    ("langchain.chains.combine_documents", "create_stuff_documents_chain"),
    ("langchain.chains.combine_documents.stuff", "create_stuff_documents_chain"),
    ("langchain_core", "create_stuff_documents_chain"),
    ("langchain_core.chains", "create_stuff_documents_chain"),
    ("langchain_core.runnables", "create_stuff_documents_chain"),
]

for module_name, func_name in paths_to_try2:
    try:
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        print(f"✓ Found: from {module_name} import {func_name}")
    except (ImportError, AttributeError) as e:
        print(f"✗ Not found: from {module_name} import {func_name}")
