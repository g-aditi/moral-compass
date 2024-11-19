import os
from nltk.tokenize import word_tokenize
import torch
import faiss
from transformers import pipeline
from gensim.models.doc2vec import Doc2Vec
from vectordb_storage import documents_text

def load_doc2vec_model():
    doc2vec_model = Doc2Vec.load("doc2vec_model.model")
    return doc2vec_model

def read_faiss_index():
    index = faiss.read_index("vector_db.faiss")
    return index

model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
pipe = pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.float16},
    device="cuda",
)

def retrieve_context(doc2vec_model, query, faiss_index, top_k=3):
    query_tokens = word_tokenize(query.lower())
    query_vector = doc2vec_model.infer_vector(query_tokens).astype('float32').reshape(1, -1)
    
    distances, indices = faiss_index.search(query_vector, top_k)
    
    relevant_docs = []
    for idx in indices[0]:
        relevant_docs.append(documents_text[idx])
    
    return " ".join(relevant_docs)

def safe_filename(s):
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s)

def make_dir_file(filename, filetype):
    llm_analyses_dir = './llm_analyses'
    os.makedirs(llm_analyses_dir, exist_ok=True)
    os.makedirs(f'{llm_analyses_dir}/{filename}', exist_ok=True)
    output_filepath = os.path.join(f'{llm_analyses_dir}/{filename}', f"{filetype}.txt")
    return output_filepath

