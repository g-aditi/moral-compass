form_questions = [
    "IRB: 1. Protocol Title",
    '''
        IRB: 2. Background and Objectives
            2.1 List the specific aims or research questions in 300 words or less.
            2.2 Refer to findings relevant to the risks and benefits to participants in the proposed research.
            2.3 Identify any past studies by ID number that are related to this study. If the work was done elsewhere,
            indicate the location.
    ''',
    '''
        IRB: 3. Data Use - What are the intended uses of the data generated from this project?
            Examples include: Dissertation, thesis, undergraduate project, publication/journal article,
            conferences/presentations, results released to agency, organization, employer, or school. If other, then
            describe.
    ''',
    '''
        IRB: 4. Inclusion and Exclusion Criteria
            4.1 List criteria that define who will be included or excluded in your final sample.
            Indicate if each of the following special (vulnerable/protected) populations is included or excluded:
            ▪ Minors (under 18)
            ▪ Adults who are unable to consent (impaired decision-making capacity)
            ▪ Prisoners
            ▪ Economically or educationally disadvantaged individuals
            4.2 If not obvious, what is the rationale for the exclusion of special populations?
            4.3 What procedures will be used to determine inclusion/exclusion of special populations?
    ''',
    '''
        IRB: 5. Number of Participants
            Indicate the total number of individuals you expect to recruit and enroll. For secondary data analyses, the
            response should reflect the number of cases in the dataset.
    ''',
    '''
        IRB: 6. Recruitment Methods
            6.1 Identify who will be doing the recruitment and consenting of participants.
            6.2 Identify when, where, and how potential participants will be identified, recruited, and consented.
            6.3 Name materials that will be used (e.g., recruitment materials such as emails, flyers, advertisements,
            etc.) Please upload each recruitment material as a separate document, Name the document:
            recruitment_methods_email/flyer/advertisement_dd-mm-yyyy
            6.4 Describe the procedures relevant to using materials (e.g., consent form).
    ''',
    '''
        IRB: 7. Study Procedures
            7.1 List research procedure step by step (e.g., interventions, surveys, focus groups, observations, lab
            procedures, secondary data collection, accessing student or other records for research purposes,
            and follow-ups). Upload one attachment, dated, with all the materials relevant to this section. Name
            the document: supporting documents dd-mm-yyyy
            7.2 For each procedure listed, describe who will be conducting it, where it will be performed, how long
            is participation in each procedure, and how/what data will be collected in each procedure.
            7.3 Report the total period and span of time for the procedures (if applicable the timeline for follow ups).
            7.4 For secondary data analyses, identify if it is a public dataset (please include a weblink where the data
            will be accessed from, if applicable). If not, describe the contents of the dataset, how it will be accessed,
            and attach data use agreement(s) if relevant.
    ''',
    '''
        IRB: 8. Compensation
            8.1 Report the amount and timing of any compensation or credit to participants.
            8.2 Identify the source of the funds to compensate participants.
            8.3 Justify that the compensation to participants to indicate it is reasonable and/or how the compensation
            amount was determined.
            8.4 Describe the procedures for distributing the compensation or assigning the credit to participants.
    ''',
    '''
        IRB: 9. Risk to Participants
            List the reasonably foreseeable risks, discomforts, or inconveniences related to participation in the
            research.
    ''',
    '''
        IRB: 10. Potential Direct Benefits to Participants
            List the potential direct benefits to research participants. If there are risks noted in 9 (above), articulated
            benefits should outweigh such risks. These benefits are not to society or others not considered
            participants in the proposed research. Indicate if there is no direct benefit. A direct benefit comes as a
            direct result of the subject’s participation in the research. An indirect benefit may be incidental to the
            subject’s participation. Do not include compensation as a benefit.
    ''',
    '''
        IRB: 11. Privacy and Confidentiality
            Indicate the steps that will be taken to protect the participant’s privacy.
            11.1 Identify who will have access to the data.
            11.2 Identify where, how, and how long data will be stored (e.g. ASU secure server, ASU cloud storage,
            filing cabinets).
            11.3 Describe the procedures for sharing, managing and destroying data.
            11.4 Describe any special measures to protect any extremely sensitive data (e.g. password protection,
            encryption, certificates of confidentiality, separation of identifiers and data, secured storage, etc.).
            11.5 Describe how any audio or video recordings will be managed, secured, and/or de-identified.
            11.6 Describe how will any signed consent, assent, and/or parental permission forms be secured and how
            long they will be maintained. These forms should separate from the rest of the study data.
            11.7 Describe how any data will be de-identified, linked or tracked (e.g. master-list, contact list,
            reproducible participant ID, randomized ID, etc.). Outline the specific procedures and processes that
            will be followed.
            11.8 Describe any and all identifying or contact information that will be collected for any reason during the
            course of the study and how it will be secured or protected. This includes contact information collected
            for follow-up, compensation, linking data, or recruitment.
            11.9 For studies accessing existing data sets, clearly describe whether or not the data requires a Data Use
            Agreement or any other contracts/agreements to access it for research purposes.
            11.10 For any data that may be covered under FERPA (student grades, etc.) additional information and
            requirements is available at https://researchintegrity.asu.edu/human-subjects/special-considerations.
            11.11 If your study is sponsored by HHS: NIH, you will need to comply with the revised 2023 NIH Data
            Management and Sharing policy. Additional information and requirements are available at
            https://libguides.asu.edu/NIH-2023. Please be aware, per 2023 NIH DMS policy, DMS plan is required
            at the time of proposal submission.
    ''',
    '''
        IRB: 12. Consent
            Describe the procedures that will be used to obtain consent or assent (and/or parental permission).
            12.1 Who will be responsible for consenting participants?
            12.2 Where will the consent process take place?
            12.3 How will the consent be obtained (e.g., verbal, digital signature)?
            12.4 If your study is sponsored by HHS: NIH, you will need to comply with the revised 2023 NIH Data
            Management and Sharing policy. Additional information and requirements are available at
            https://libguides.asu.edu/NIH-2023. To comply with this policy, the informed consent should explain
            how data will be managed and shared. This sharing should be consistent with the DMS plan.
    ''',
    '''
        IRB: 13. Site(s) or locations where research will be conducted.
            List the sites or locations where interactions with participants will occur-
            • Identify where research procedures will be performed.
            • For research conducted outside of the ASU describe:
            o Site-specific regulations or customs affecting the research.
            o Local scientific and ethical review structures in place.
            • For research conducted outside of the United States/United States Territories describe:
            • Safeguards to ensure participants are protected.
            • For information on international research, review the content [here].
            For research conducted with secondary data (archived data):
            • List what data will be collected and from where.
            • Describe whether or not the data requires a Data Use Agreement or any other
            contracts/agreements to access it for research purposes.
            • For any data that may be covered under FERPA (student grades, etc.) additional information and
            requirements is available [here].
            • For any data that may be covered under FERPA (student grades, homework assignments,
            student ID numbers etc.), additional information and requirements is available [here].
    ''',
    '''
        IRB: 14. Human Subjects Certification from Training.
            Provide the names of the members of the research team.
            ASU affiliated individuals do not need attach Certificates. Non-ASU investigators and research team
            members anticipated to manage data and/or interact
            with participants, need to provide the most recent CITI training for human participants available at
            www.citiprogram.org. Certificates are valid for 4 years.
    ''',
    '''
        IRB 15. Conflicts of Interest
            15.1 Do any of the team members have a financial interest in any entity involved in the project(s)
            under this IRB study?
            Financial interest: The receipt or expectation of anything of pecuniary (money) or proprietary (ownership)
            value from a non-ASU entity (domestic or foreign, private or public). Examples of possible interests (not
            limited to):

            • Compensation of any amount including (not limited to) consultant fees, payments for services,
            honoraria, royalties, or other income.
            • Ownership interest of any value including (not limited to) stocks and stock options, private equity, or
            other ownership interests.
            • Venture capital financing.
            • Intellectual property interests of any value including (not limited to) patents, trademarks, copyrights,
            and licensing agreements.
            • Board or executive relationship, regardless of compensation.
            • Reimbursed or sponsored travel by an entity other than a federal, state, or local government
            agency, higher-education institution or affiliated research institute, academic teaching hospital, or
            medical center.
            15.2 Who holds the interest? The individual involved in the research, or relative of this individual. Disclose
            financial interests in ERA MyDisclosures module.
    '''
]

form_answers = [
    '''AI Ethics Interview Framework: Enhancing Ethical Decision-Making in AI Development.''',
    '''This project aims to develop an AI Ethics Interview Framework designed to assess the ethical considerations of AI systems 
        in development. The specific research questions include: How do AI developers prioritize ethical considerations during the 
        design process? What challenges do they face in implementing ethical guidelines? How can structured interviews enhance 
        understanding of these challenges? By addressing these questions, the project seeks to create a comprehensive framework 
        that can guide developers in aligning their AI projects with ethical standards.
        
        Participants may experience minimal risks, such as discomfort when discussing ethical dilemmas. However, the potential benefits 
        include contributing to the advancement of ethical practices in AI development, which can lead to safer and more responsible AI 
        systems. Additionally, participants will receive insights into current ethical frameworks and the opportunity to influence 
        future AI governance.
        
        Previous studies relevant to this research include ID #2034, which examined ethical considerations in AI decision-making processes 
        at Stanford University, and ID #4015, focusing on AI ethics training in tech firms conducted at MIT. These studies underscore 
        the need for ongoing research in AI ethics and provide a foundation for the current project.''',
        '''The data generated from this project will be used for a publication in a peer-reviewed journal, presentations at conferences, 
        and as part of a dissertation on ethical frameworks in AI development.''',
        '''Participants will include adults aged 18 and over who have experience in AI development and ethics. Excluded populations will 
        consist of minors, adults unable to consent, prisoners, and economically or educationally disadvantaged individuals.
        Excluding these special populations is essential to ensure informed consent and protect vulnerable individuals from potential 
        ethical dilemmas. Inclusion criteria will be determined through pre-screening questionnaires assessing participants' professional 
        background and capacity to provide informed consent.''',
        '''We expect to recruit and enroll a total of 50 participants for the study.''',
        '''Recruitment will be conducted by the research team, which includes faculty and graduate students experienced in ethical 
        research practices.
        Potential participants will be identified through professional networks and AI-related conferences, with recruitment occurring 
        via email invitations and social media posts.
        Recruitment materials will include an informational flyer and consent form, which will clearly outline the study’s purpose, 
        procedures, and participant rights.''',
        '''The study will involve several key steps: (1) initial recruitment via email and social media, (2) screening for eligibility 
        using a pre-screening questionnaire, (3) obtaining informed consent, (4) conducting structured interviews with participants, 
        (5) collecting qualitative data through audio recordings, and (6) analyzing the data for ethical themes. All supporting materials 
        relevant to this section are uploaded as "supporting_documents_22-10-2024."
        The research team will conduct the interviews via video conferencing platforms, allowing flexibility for participants' locations. 
        Each interview will last approximately 60 minutes, during which participants will discuss their experiences and perspectives on 
        ethical practices in AI development. Data collection will involve audio recordings and written notes, ensuring accurate capture 
        of participant insights.
        The total duration for participant involvement is expected to be around two months, including recruitment, interviews, and data 
        analysis. Follow-ups may occur for clarification of responses or additional insights, scheduled within two weeks post-interview.
        As this study focuses on primary data collection through interviews, no secondary public datasets will be used. The dataset will 
        consist of interview transcripts and audio recordings stored securely, accessible only to the research team. Data use agreements 
        will be established to ensure confidentiality and ethical handling of participant information.''',
        '''Participants will receive $50 compensation after completing the interview, funded by the research grant, distributed via 
        electronic payment methods.''',
        '''Participants may experience discomfort when discussing sensitive ethical issues, potential emotional distress from recalling 
        challenging situations in AI development, and concerns about confidentiality. Additionally, participants may encounter time 
        constraints due to their professional commitments, which could lead to inconvenience when scheduling interviews or completing 
        pre-screening questionnaires.''',
        '''Participants may gain insights into ethical considerations in AI development, enhancing their understanding of best practices. 
        They will have the opportunity to contribute to the advancement of ethical frameworks in the field, potentially improving their 
        professional practices and fostering a greater commitment to responsible AI development in their organizations.''',
        '''To protect participants' privacy, access to data will be restricted to the research team only. Data will be stored on ASU's 
        secure server for a minimum of five years, with audio recordings encrypted and de-identified. Signed consent forms will be kept 
        separate, secured in locked files. Identifying information, including contact details for follow-up, will be protected and 
        de-identified using randomized IDs. No existing datasets requiring a Data Use Agreement will be accessed, ensuring compliance 
        with all privacy regulations.''',
        '''The research team, including trained faculty and graduate students, will be responsible for obtaining consent from participants. 
        The consent process will occur via video conferencing prior to the interview. Consent will be obtained through digital signatures 
        on a secure platform, ensuring participants understand data management and sharing in line with the 2023 NIH Data Management and 
        Sharing policy.''',
        '''Research procedures will be conducted via video conferencing, allowing interactions with participants in their preferred 
        locations. No site-specific regulations or local review structures apply, as all activities will adhere to ASU's ethical 
        standards and guidelines for remote research.''',
        '''The research team includes Dr. Jane Smith, Prof. John Doe, and graduate student Alex Lee, all of whom are ASU affiliates.''',
        '''None of the team members have a financial interest in any entity involved in the project under this IRB study.'''
]

def get_form_inputs(input_list):
    print(f"Received form responses")
    form_answers = input_list
    print(form_answers)
