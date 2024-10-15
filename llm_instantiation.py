from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.core import Settings
from llama_index.core import PromptTemplate
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from llama_index.llms.huggingface import HuggingFaceLLM
import faiss
import numpy as np

index = faiss.read_index("vector_db.faiss")

def get_form_inputs(input_list):
    print(f"Received: {input_list}")

