import PyPDF2
import pandas as pd
import numpy as np
import os
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
import nltk
import faiss

nltk.download('punkt')
nltk.download('punkt_tab')

def pdf_to_text(pdf_data_directory, txt_data_directory):
    if not os.path.exists(txt_data_directory):
        os.makedirs(txt_data_directory)
    for pdf_filename in os.listdir(pdf_data_directory):
        if pdf_filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_data_directory, pdf_filename)
            txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
            txt_path = os.path.join(txt_data_directory, txt_filename)
            with open(pdf_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                with open(txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(text)

pdf_data_directory = "./documents"
txt_data_directory = "./txt_documents"
pdf_to_text(pdf_data_directory, txt_data_directory)

txt_file_paths = [os.path.join(txt_data_directory, file) for file in os.listdir(txt_data_directory) if file.endswith('.txt')]

tagged_data = []

for i, txt_file_path in enumerate(txt_file_paths):
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        words = word_tokenize(text)
        words = [word.lower() for word in words]
        tagged_data.append(TaggedDocument(words, tags=['doc_' + str(i)]))

model = Doc2Vec(vector_size=20, epochs=300)
model.build_vocab(tagged_data)
model.train(tagged_data, total_examples=model.corpus_count, epochs=model.epochs)

document_vectors = [model.dv['doc_' + str(i)] for i in range(len(tagged_data))]
vector_dim = len(document_vectors[0])

index = faiss.IndexFlatL2(vector_dim)
vectors_np = np.array(document_vectors).astype('float32')

faiss.write_index(index, "vector_db.faiss")