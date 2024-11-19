from transformers import pipeline
import torch
import os
from form_responses import form_questions, form_answers
from rag_helper import load_doc2vec_model, read_faiss_index, retrieve_context, safe_filename, make_dir_file

doc2vec_model = load_doc2vec_model("doc2vec_model.model")
index = read_faiss_index("vector_db.faiss")

torch.cuda.empty_cache()

framework_model_save_dir = "./framework_model"

if os.path.exists(framework_model_save_dir):
    pipe = pipeline(
        "text-generation",
        model=framework_model_save_dir,
        tokenizer=framework_model_save_dir,
        model_kwargs={"torch_dtype": torch.float16},
        device="cuda",
    )
    print(f"Model loaded from {framework_model_save_dir}")

else:
    adherence_model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    pipe = pipeline(
        "text-generation",
        model=adherence_model_id,
        model_kwargs={"torch_dtype": torch.float16},
        device="cuda",
    )

framework_system_context_from_faiss = retrieve_context(doc2vec_model=doc2vec_model,
                                                       query="Belmont Report, IRB Guidelines, How should an IRB function?, Adherence",
                                                       faiss_index=index)

filename = safe_filename(form_answers[0])
filetype = 'framework-analysis'
framework_output_filepath = make_dir_file(filename, filetype)

"""
### PLACEHOLDER ###

TBD: 
1. Prompt engineering for ethical framework analysis [yet to evaluate current prompt]
2. Enable the chat UI and create a connection with JS/FLASK/LLM POST and GET
3. Store context (chat history) in a JSON or .txt

Uncomment below to make these changes.

"""

# with open(framework_output_filepath, "w") as framework_file:
#   for question, answer in zip(form_questions, form_answers):
#     user_context_from_faiss = retrieve_context(question)
#     nett_input = f"Context: {user_context_from_faiss}\n\nQuestion: {question}\n\nAnswer: {answer}"

#     messages = [
#         {
#             "role": "system",
#             "content": f'''You are the preliminary step to an Institutional Review Board of an organization. 
#                         Guided by the values in {framework_system_context_from_faiss}, analyze the answers to the question
#                         and provide some feedback on their position with respect to various ethical frameworks. At the very least,
#                         you should cover the ethical framworks mentioned in the the system content. Also identify potential 
#                         ethical dilemmas or trolley problems in the paper.
#                         If possible, keep your replies within 200 words.'''
#         },
#         {
#             "role": "user", 
#             "content": nett_input
#         },
#     ]

#     outputs = pipe(
#         messages,
#         max_new_tokens=512,
#         do_sample=True,
#     )

#     assistant_response = outputs[0]["generated_text"]

#     framework_file.write(f"Question: {question}\n")
#     framework_file.write(f"Answer: {answer}\n")
#     framework_file.write(f"LLM Response: {assistant_response[2].get('content')}\n\n")

# pipe.model.save_pretrained(framework_model_save_dir)
# pipe.tokenizer.save_pretrained(framework_model_save_dir)

torch.cuda.empty_cache()
