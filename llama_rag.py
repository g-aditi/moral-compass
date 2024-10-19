import transformers
from transformers import pipeline
import torch
import faiss
import numpy as np
from gensim.models.doc2vec import Doc2Vec
from nltk.tokenize import word_tokenize
import nltk
import os
from vectordb_storage import documents_text
from form_responses import form_questions, form_answers

doc2vec_model = Doc2Vec.load("doc2vec_model.model")

index = faiss.read_index("vector_db.faiss")

def retrieve_context(query, top_k=3):
    query_tokens = word_tokenize(query.lower())
    query_vector = doc2vec_model.infer_vector(query_tokens).astype('float32').reshape(1, -1)
    
    distances, indices = index.search(query_vector, top_k)
    
    relevant_docs = []
    for idx in indices[0]:
        relevant_docs.append(documents_text[idx])
    
    return " ".join(relevant_docs)

model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
pipe = pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device="cuda",
)
system_context_from_faiss = retrieve_context("Belmont Report, IRB Guidelines, How should an IRB function?")

def safe_filename(s):
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s)

filename = safe_filename(form_answers[0])
llm_analyses_dir = './llm_analyses'
os.makedirs(llm_analyses_dir, exist_ok=True)
output_filepath = os.path.join(llm_analyses_dir, f"{filename}-llm-analysis.txt")

with open(output_filepath, "w") as file:
  for question, answer in zip(form_questions, form_answers):
    user_context_from_faiss = retrieve_context(question)
    nett_input = f"Context: {user_context_from_faiss}\n\nQuestion: {question}\n\nAnswer: {answer}"

    messages = [
        {
            "role": "system",
            "content": f'''You are the preliminary step to an Institutional Review Board of an organization. 
                        Guided by the values in {system_context_from_faiss}, analyze the answers to each question
                        and provide some feedback on their adherence to further context. Say 'No additional comments' 
                        if you don't have anything to say. Do not answer any questions, just analyze the answers based on
                        whether or not they match the requirements of the IRB.
                        If possible, keep your replies within 250 words.'''
        },
        {
            "role": "user", 
            "content": nett_input
        },
    ]

    outputs = pipe(
        messages,
        max_new_tokens=518,
        do_sample=True,
    )

    assistant_response = outputs[0]["generated_text"]
    # print(assistant_response[2].get('content'))

    file.write(f"Question: {question}\n")
    file.write(f"Answer: {answer}\n")
    file.write(f"LLM Response: {assistant_response[2].get('content')}\n\n")
