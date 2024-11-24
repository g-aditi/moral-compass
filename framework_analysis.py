from transformers import pipeline
import torch
import os
from form_responses import form_questions, form_answers
from rag_helper import load_doc2vec_model, read_faiss_index, retrieve_context, safe_filename, make_dir_file

doc2vec_model = load_doc2vec_model()
index = read_faiss_index()

torch.cuda.empty_cache()

framework_model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
pipe = pipeline(
        "text-generation",
        model=framework_model_id,
        model_kwargs={"torch_dtype": torch.float16},
        device="cuda",
    )

framework_system_context_from_faiss = retrieve_context(doc2vec_model=doc2vec_model,
                                                       query="Utilitarian, Deontology, Fairness, \
                                                              Virtue Ethics, Ethical Frameworks, Consequentialism \
                                                              Trolley Problems, Ethical Dilemmas",
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

"""

full_form_responses = '\n'.join(ans for ans in [form_answers[0], form_answers[1]])
# print(full_form_responses)

with open(framework_output_filepath, "w") as framework_file:
    nett_input = f"Context: {full_form_responses}"

    messages = [
        {
            "role": "system",
            "content": f'''You are the preliminary step to an Institutional Review Board of an organization. 
                        Guided by the values in {framework_system_context_from_faiss}, analyze the answers to the question
                        and provide some feedback on their position with respect to various ethical frameworks. Mainly, focus your
                        analysis on the answer to IRB: 2. I also want you to analyze the proposed research, its areas and 
                        methods apart from focusing on the participants and their ethical rights. Here are some you can consider using in 
                        your analysis: Consequentialism, Deontology, Utilitarianism, Virtue Ethics, Ethical Relativism, Social Contract 
                        Theory, Care Ethics, Feminist Ethics, Justice, Fairness. 
                        Follow this template: 
                            Title of Project:
                            Summary of Project:

                            Ethical Framework(s) in Accordance: 
                            Basis for Accordance of Framework(s):

                            Ethical Framework(s) in Violation:
                            Basis of Violation of Framework(s):

                            Suggested Middle-Ground Ethical Framework(s):
                            Basis for Suggestion(s):
                        Also identify potential  ethical dilemmas or trolley problems in the paper. You are to give only valid, relevant,
                        and important feedback - not feedback just for the sake of it. Equal focus is to be placed on both the participant
                        ethical protection and the ethical framework compliance of the study itself.
                        '''
        },
        {
            "role": "user", 
            "content": nett_input
        },
    ]

    outputs = pipe(
        messages,
        max_new_tokens=1028,
        do_sample=True,
    )

    assistant_response = outputs[0]["generated_text"]
    framework_file.write(f"{assistant_response[2].get('content')}\n\n")
    print("Response generated")

torch.cuda.empty_cache()
