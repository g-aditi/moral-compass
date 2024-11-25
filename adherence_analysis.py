from transformers import pipeline
import torch
import os
from form_responses import form_questions, form_answers
from rag_helper import load_doc2vec_model, read_faiss_index, retrieve_context, safe_filename, make_dir_file

doc2vec_model = load_doc2vec_model()
index = read_faiss_index()

torch.cuda.empty_cache()

adherence_model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
pipe = pipeline(
        "text-generation",
        model=adherence_model_id,
        model_kwargs={"torch_dtype": torch.float16},
        device="cuda",
)

adherence_system_context_from_faiss = retrieve_context(doc2vec_model=doc2vec_model,
                                                       query="Belmont Report, IRB Guidelines, How should an IRB function?, Adherence",
                                                       faiss_index=index)

filename = safe_filename(form_answers[0])
filetype = 'adherence-analysis'
adherence_output_filepath = make_dir_file(filename, filetype)

with open(adherence_output_filepath, "w") as adherence_file:
  for question, answer in zip(form_questions, form_answers):
    user_context_from_faiss = retrieve_context(question)
    nett_input = f"Context: {user_context_from_faiss}\n\nQuestion: {question}\n\nAnswer: {answer}"

    messages = [
        {
            "role": "system",
            "content": f'''You are the preliminary step to an Institutional Review Board of an organization. 
                        Guided by the values in {adherence_system_context_from_faiss}, analyze the answers to the question
                        and provide some feedback on their adherence to the content. Say 'No additional comments' 
                        if you don't have anything to say. Do not answer any questions, just analyze the answers based on
                        whether or not they match the requirements of the IRB. Do not analyse whether or not the IRB is right.
                        Only analyze the answer to the given question, and nothing the answer is supposed to cater to outside the question.
                        If possible, keep your replies within 200 words.'''
        },
        {
            "role": "user", 
            "content": nett_input
        },
    ]

    outputs = pipe(
        messages,
        max_new_tokens=512,
        do_sample=True,
    )

    assistant_response = outputs[0]["generated_text"]

    adherence_file.write(f"Question: {question}\n")
    adherence_file.write(f"Answer: {answer}\n")
    adherence_file.write(f"LLM Response: {assistant_response[2].get('content')}\n\n")

torch.cuda.empty_cache()
