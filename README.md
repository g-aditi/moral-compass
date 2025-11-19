# Moral Compass: AI-Powered Ethical Analysis  

> "Because ethics should evolve as fast as technology."


## Overview
**Moral Compass** is an AI-assisted ethical analysis tool designed to support researchers and Institutional Review Boards (IRBs) in identifying ethical risks in research protocols.  
The system goes beyond compliance checklists by combining large language model reasoning with retrieval-augmented generation (RAG) over officially published ethical frameworks, including:

- NIST AI Risk Management Framework (AI RMF 1.0)  
- Menlo Report and Belmont Report  
- ASU IRB guidelines for human-subjects research  

The result is a structured, transparent, and context-aware evaluation that helps researchers recognize gray-area ethical issues early in their design process.


## Motivation
Traditional IRB reviews focus primarily on legal compliance and institutional liability, which can overlook subtle ethical dilemmas - especially in AI-driven or interdisciplinary research. *Moral Compass* aims to bridge this gap by:

- Providing framework-based ethical feedback on proposed studies  
- Highlighting potential violations of ethical principles  
- Offering balanced recommendations instead of rigid prescriptions  
- Reducing IRB workload while improving researcher understanding  


## System Architecture
The pipeline consists of four key stages:

1. **Document Vectorization**  
   - 21 ethical guideline documents are embedded using Doc2Vec.  
   - Indexed using a FAISS vector database for efficient retrieval.  

2. **Form Interface**  
   - An interactive multi-step web form replicates ASU’s HRP 503A form for Social Behavioral Protocols.  

3. **RAG Engine and LLM Analysis**  
   - Retrieves relevant ethical context and feeds it to LLaMA-3.1-8B-Instruct.  
   - Generates a comprehensive ethical analysis PDF for review.  

4. **User Feedback Study**  
   - 22 participants evaluated the tool’s clarity, usefulness, and privacy perception.


## Key Findings
From the user study:

- About 80% of participants found the tool aligned with IRB guidelines.  
- 70% reported higher confidence in addressing ethical concerns.  
- Top-rated aspects included ease of use (28%) and value addition to ethical understanding (26%).  
- Around 40% expressed minor concerns about data privacy and security.


## Limitations and Future Work

**Current Challenges**
- Limited participant diversity and no live deployment due to resource constraints.  
- Static knowledge base requiring manual updates when guidelines change.  

**Planned Enhancements**
- Automated updates for new ethical standards.  
- Conversational interface for critical ethical reasoning.  
- Real-time interactive analysis and summary generation.


## Technology Stack

| Component | Technology |
|------------|-------------|
| Backend | Python 3, Flask |
| Frontend | HTML, CSS, JavaScript |
| LLM | LLaMA 3.1, Doc2Vec |
| Vector Database | FAISS |


## Installation and Usage

Clone the repository
```bash
git clone https://github.com/g-aditi/moral-compass.git
cd moral-compass
```
Create a virtual environment and install dependencies
```bash
pip install -r requirements.txt
```

Run the Flask app
```bash
python app.py
```

Access the tool in your browser
```bash
http://127.0.0.1:5000
```

