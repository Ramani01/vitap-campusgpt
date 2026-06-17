import os
import json

# Adjust dataset directory based on where the script is executed
cwd = os.getcwd()
if os.path.basename(cwd) == "dataset":
    dataset_dir = "."
else:
    dataset_dir = "dataset"

os.makedirs(dataset_dir, exist_ok=True)

datasets = {
    "regulations.jsonl": [
        {"instruction":"Where can I find the Act and Statutes of VIT-AP University?","response":"The Act and Statutes are available on the university website via the public self-disclosure links."},
        {"instruction":"How do I access the official university statutes?","response":"The Act and Statutes are available on the university website via the public self-disclosure links."},
        {"instruction":"Is there a link to read the VIT-AP Act and Statutes?","response":"The Act and Statutes are available on the university website via the public self-disclosure links."},
        {"instruction":"Where are the foundational Act and Statutes of the university published?","response":"The Act and Statutes are available on the university website via the public self-disclosure links."},
        {"instruction":"What is the university's official policy on fee refunds?","response":"If a candidate withdraws from the programme, the refund of fees will be made as per the norms of the UGC."},
        {"instruction":"How does the fee refund process work if I withdraw?","response":"If a candidate withdraws from the programme, the refund of fees will be made as per the norms of the UGC."},
        {"instruction":"Will I get my money back if I cancel my admission?","response":"If a candidate withdraws from the programme, the refund of fees will be made as per the norms of the UGC."},
        {"instruction":"Are fee refunds governed by any specific guidelines?","response":"If a candidate withdraws from the programme, the refund of fees will be made as per the norms of the UGC."},
        {"instruction":"Does the university have facilities for differently-abled students?","response":"Yes, the university provides a barrier-free environment and specific facilities for differently-abled individuals."},
        {"instruction":"Are there accommodations for handicapped or differently-abled people?","response":"Yes, the university provides a barrier-free environment and specific facilities for differently-abled individuals."},
        {"instruction":"Is the campus accessible for students with disabilities?","response":"Yes, the university provides a barrier-free environment and specific facilities for differently-abled individuals."},
        {"instruction":"What does the university's vision statement say?","response":"The vision is to transform higher education and contribute to the improvement of life itself by application of knowledge."},
        {"instruction":"What is the official vision of VIT-AP?","response":"The vision is to transform higher education and contribute to the improvement of life itself by application of knowledge."},
        {"instruction":"Can you tell me the university's vision?","response":"The vision is to transform higher education and contribute to the improvement of life itself by application of knowledge."},
        {"instruction":"What is the university motto?","response":"The motto of the university is 'Apply Knowledge, Improve Life!'"},
        {"instruction":"What catchphrase or motto does VIT-AP use?","response":"The motto of the university is 'Apply Knowledge, Improve Life!'"},
        {"instruction":"What is the official university motto?","response":"The motto of the university is 'Apply Knowledge, Improve Life!'"},
        {"instruction":"What are the core values of VIT-AP?","response":"Core values include a Student-Centered Environment, Transformative Leadership, Teamwork, Striving for Excellence, Respect and Inclusion, Sustainability, Creativity, Accountability, and Integrity."},
        {"instruction":"Which principles form the core values of the institution?","response":"Core values include a Student-Centered Environment, Transformative Leadership, Teamwork, Striving for Excellence, Respect and Inclusion, Sustainability, Creativity, Accountability, and Integrity."},
        {"instruction":"What ethics and values does the university promote?","response":"Core values include a Student-Centered Environment, Transformative Leadership, Teamwork, Striving for Excellence, Respect and Inclusion, Sustainability, Creativity, Accountability, and Integrity."},
        {"instruction":"Does the university have an Equal Opportunity Cell?","response":"Yes, the university maintains an Equal Opportunity Cell and a Socio-Economically Disadvantaged Group Cell (SEDG)."},
        {"instruction":"Is there a dedicated cell for socio-economically disadvantaged groups?","response":"Yes, the university maintains an Equal Opportunity Cell and a Socio-Economically Disadvantaged Group Cell (SEDG)."},
        {"instruction":"What administrative body supports marginalized students?","response":"Yes, the university maintains an Equal Opportunity Cell and a Socio-Economically Disadvantaged Group Cell (SEDG)."}
    ],

    "hostel.jsonl": [
        {"instruction":"What is the curfew time for hostellers?","response":"On class days, all hostellers must be inside the hostel by 7:30 PM."},
        {"instruction":"By what time do hostel students need to be inside?","response":"On class days, all hostellers must be inside the hostel by 7:30 PM."},
        {"instruction":"What is the attendance timing for hostellers?","response":"On class days, all hostellers must be inside the hostel by 7:30 PM."},
        {"instruction":"When should hostel students return on working days?","response":"On class days, all hostellers must be inside the hostel by 7:30 PM."},
        {"instruction":"Are hostel students allowed to stay with local guardians?","response":"A hosteller may avail leave and go to their approved local guardian's place with proper prior intimation to the authorities."},
        {"instruction":"Can a hosteller visit their local guardian for the weekend?","response":"A hosteller may avail leave and go to their approved local guardian's place with proper prior intimation to the authorities."},
        {"instruction":"What is the leave policy for visiting a local guardian?","response":"A hosteller may avail leave and go to their approved local guardian's place with proper prior intimation to the authorities."},
        {"instruction":"What value stamp paper is needed for the student and hostel affidavit?","response":"The affidavit must be signed separately by the student, parent, and hostel on a Rs. 20/- Non-Judicial Stamp Paper and notarized."},
        {"instruction":"What is the required stamp paper denomination for admission affidavits?","response":"The affidavit must be signed separately by the student, parent, and hostel on a Rs. 20/- Non-Judicial Stamp Paper and notarized."},
        {"instruction":"Do I need a Rs. 20 stamp paper for the hostel affidavit?","response":"The affidavit must be signed separately by the student, parent, and hostel on a Rs. 20/- Non-Judicial Stamp Paper and notarized."},
        {"instruction":"Is a medical certificate required for admission to the hostel?","response":"Yes, students must submit a Certificate of Physical Fitness certified by an authorized physician."},
        {"instruction":"Do I need to prove my physical fitness before joining?","response":"Yes, students must submit a Certificate of Physical Fitness certified by an authorized physician."},
        {"instruction":"What health documents are mandatory for admission?","response":"Yes, students must submit a Certificate of Physical Fitness certified by an authorized physician."}
    ],

    "admissions.jsonl": [
        {"instruction":"How are B.Tech admissions decided?","response":"Admission is based purely on the ranks secured in the VITEEE Computer Based Test."},
        {"instruction":"What is the main criteria for getting into B.Tech?","response":"Admission is based purely on the ranks secured in the VITEEE Computer Based Test."},
        {"instruction":"Does the university use 12th marks for B.Tech admission?","response":"Admission is based purely on the ranks secured in the VITEEE Computer Based Test."},
        {"instruction":"How does VIT equate different VITEEE exam forms?","response":"The statistical procedure of Equipercentile Equating is used to adjust scores and identify equivalent percentile ranks."},
        {"instruction":"What statistical method normalizes the VITEEE scores?","response":"The statistical procedure of Equipercentile Equating is used to adjust scores and identify equivalent percentile ranks."},
        {"instruction":"Is the VITEEE scoring normalized across sessions?","response":"The statistical procedure of Equipercentile Equating is used to adjust scores and identify equivalent percentile ranks."},
        {"instruction":"Is there negative marking in the VIT entrance exams?","response":"No, there are no negative marks for wrong answers."},
        {"instruction":"Will I lose marks for guessing incorrectly on the VITEEE?","response":"No, there are no negative marks for wrong answers."},
        {"instruction":"Does the VITMEE have a penalty for wrong answers?","response":"No, there are no negative marks for wrong answers."},
        {"instruction":"What is the deadline to submit final UG documents for M.Sc. admission?","response":"The documents should be submitted before 15 August 2026, failing which admission will be cancelled."},
        {"instruction":"By what date must PG students submit their provisional degree certificate?","response":"The documents should be submitted before 15 August 2026, failing which admission will be cancelled."},
        {"instruction":"What happens if I don't submit my final M.Sc. documents by August 15?","response":"The documents should be submitted before 15 August 2026, failing which admission will be cancelled."},
        {"instruction":"What is the eligibility for the Direct Ph.D. program?","response":"Graduates must have an outstanding academic record with a minimum of 75% marks or a CGPA of 7.5 on a 10-point scale in their Bachelor's degree."},
        {"instruction":"Can I do a Ph.D. directly after my B.Tech?","response":"Graduates must have an outstanding academic record with a minimum of 75% marks or a CGPA of 7.5 on a 10-point scale in their Bachelor's degree."},
        {"instruction":"What CGPA is required for Direct Ph.D. admission?","response":"Graduates must have an outstanding academic record with a minimum of 75% marks or a CGPA of 7.5 on a 10-point scale in their Bachelor's degree."},
        {"instruction":"What is the stipend for a GATE-qualified Chancellor Fellow in the second year?","response":"A GATE-qualified Chancellor Fellow receives ₹ 50,000 per month in their second and third years."},
        {"instruction":"How much does a 2nd year GATE-qualified Ph.D. student get paid?","response":"A GATE-qualified Chancellor Fellow receives ₹ 50,000 per month in their second and third years."},
        {"instruction":"What is the Chancellor Fellowship stipend amount?","response":"A GATE-qualified Chancellor Fellow receives ₹ 50,000 per month in their second and third years."},
        {"instruction":"Do SC/ST students need a specific certificate for admission?","response":"Yes, they must provide a Community Certificate recognized under the Constitution and signed by a competent authority."},
        {"instruction":"What caste document is required for SC/ST quotas?","response":"Yes, they must provide a Community Certificate recognized under the Constitution and signed by a competent authority."},
        {"instruction":"Is a community certificate mandatory for scheduled castes?","response":"Yes, they must provide a Community Certificate recognized under the Constitution and signed by a competent authority."},
        {"instruction":"What are the eligibility requirements for foreign candidates applying to BSc, BBA, or B.Com?","response":"For foreign candidates, the minimum marks for eligibility in BSc, BBA, and B.Com are 50% marks or its equivalent grade in their school final examination, and they must have studied English in high school or at an English-medium school. This information comes from the admission policy document (VIT-AP-ADMISSION-POLICY.pdf)."},
        {"instruction":"What is the minimum marks for eligibility in BSc, BBA, or B.Com for a foreign student?","response":"The minimum marks for eligibility in BSc, BBA, or B.Com are 50% marks or its equivalent grade. This information comes from VIT-AP-ADMISSION-POLICY.pdf."}
    ],

    "ethics.jsonl": [
        {"instruction":"What constitutes sexual harassment according to the university?","response":"Sexual misconduct includes unwanted physical contact, persistent unwelcome comments, and sending obscene messages or pictures on social media."},
        {"instruction":"How does the code of ethics define sexual misconduct?","response":"Sexual misconduct includes unwanted physical contact, persistent unwelcome comments, and sending obscene messages or pictures on social media."},
        {"instruction":"Are inappropriate social media messages considered sexual harassment?","response":"Sexual misconduct includes unwanted physical contact, persistent unwelcome comments, and sending obscene messages or pictures on social media."},
        {"instruction":"What is the penalty for ragging?","response":"Ragging is an illegal activity liable for imprisonment for two years with a fine up to Rs. 10,000, and expulsion from the University."},
        {"instruction":"Can a student be expelled for ragging?","response":"Ragging is an illegal activity liable for imprisonment for two years with a fine up to Rs. 10,000, and expulsion from the University."},
        {"instruction":"What legal consequences face students who participate in ragging?","response":"Ragging is an illegal activity liable for imprisonment for two years with a fine up to Rs. 10,000, and expulsion from the University."},
        {"instruction":"Are mobile phones allowed during exams?","response":"No, possession of cell phones or any electronic devices inside the examination hall is strictly prohibited."},
        {"instruction":"Can I keep my phone in my pocket during an examination?","response":"No, possession of cell phones or any electronic devices inside the examination hall is strictly prohibited."},
        {"instruction":"Is carrying an electronic device into the exam hall a violation?","response":"No, possession of cell phones or any electronic devices inside the examination hall is strictly prohibited."},
        {"instruction":"Who do I appeal to if I receive a disciplinary punishment?","response":"An appeal against any order of punishment can be submitted to the Registrar of the University."},
        {"instruction":"Where can I file an appeal against an ethics violation ruling?","response":"An appeal against any order of punishment can be submitted to the Registrar of the University."},
        {"instruction":"Who handles appeals for disciplinary actions?","response":"An appeal against any order of punishment can be submitted to the Registrar of the University."}
    ],

    "ipr.jsonl": [
        {"instruction":"Who holds the ownership of patents filed at the university?","response":"VIT-AP University acts as the sole owner of all Intellectual Property Rights generated using its resources."},
        {"instruction":"Does the inventor own the patent or does the university?","response":"VIT-AP University acts as the sole owner of all Intellectual Property Rights generated using its resources."},
        {"instruction":"Who is the legal owner of IPR generated on campus?","response":"VIT-AP University acts as the sole owner of all Intellectual Property Rights generated using its resources."},
        {"instruction":"Who pays for the patent attorney and filing fees?","response":"All expenses, including statutory fees and patent attorney fees, are completely borne by the university's IPR Cell."},
        {"instruction":"Do students have to pay out of pocket to file a patent?","response":"All expenses, including statutory fees and patent attorney fees, are completely borne by the university's IPR Cell."},
        {"instruction":"Who covers the financial cost of intellectual property registration?","response":"All expenses, including statutory fees and patent attorney fees, are completely borne by the university's IPR Cell."},
        {"instruction":"What is the revenue sharing ratio for commercialized patents?","response":"The revenue generated from commercial exploitation of IP is shared in a 60:40 ratio between the inventor(s) and the University."},
        {"instruction":"How much money does the inventor get if a patent is sold?","response":"The revenue generated from commercial exploitation of IP is shared in a 60:40 ratio between the inventor(s) and the University."},
        {"instruction":"What percentage of IP royalties goes to the creator?","response":"The revenue generated from commercial exploitation of IP is shared in a 60:40 ratio between the inventor(s) and the University."},
        {"instruction":"What is the timeline for returning confidential information under an NDA?","response":"The receiving party must return all Confidential Information within 5 days of a written demand by the disclosing party."},
        {"instruction":"How many days do I have to return NDA documents?","response":"The receiving party must return all Confidential Information within 5 days of a written demand by the disclosing party."},
        {"instruction":"What is the timeframe to surrender confidential info upon request?","response":"The receiving party must return all Confidential Information within 5 days of a written demand by the disclosing party."},
        {"instruction":"What image views are required for a design patent application?","response":"Seven specific views in JPEG format: front, rear, left, right, top, bottom, and a top perspective view."},
        {"instruction":"How many photographs do I need for design registration?","response":"Seven specific views in JPEG format: front, rear, left, right, top, bottom, and a top perspective view."},
        {"instruction":"What format should the design invention photos be in?","response":"Seven specific views in JPEG format: front, rear, left, right, top, bottom, and a top perspective view."}
    ],

    "placements.jsonl": [
        {"instruction":"What marks are required for IT sector placements?","response":"IT sector placements require a minimum of 60% marks in undergraduate programs and in classes X and XII."},
        {"instruction":"What is the minimum percentage to sit for IT placements?","response":"IT sector placements require a minimum of 60% marks in undergraduate programs and in classes X and XII."},
        {"instruction":"Do I need 60% in 10th and 12th for campus placements?","response":"IT sector placements require a minimum of 60% marks in undergraduate programs and in classes X and XII."},
        {"instruction":"Is a gap year allowed for placements?","response":"Yes, an academic gap of a maximum of two years is permitted for placements."},
        {"instruction":"Can I sit for placements if I have a 1-year academic gap?","response":"Yes, an academic gap of a maximum of two years is permitted for placements."},
        {"instruction":"What is the maximum allowed academic gap for IT placements?","response":"Yes, an academic gap of a maximum of two years is permitted for placements."},
        {"instruction":"What is the STARS scheme?","response":"Support The Advancement of Rural Students (STARS) offers a 100% scholarship, free hostel, and food for rural AP government junior college toppers."},
        {"instruction":"Does the university offer full scholarships for rural students?","response":"Support The Advancement of Rural Students (STARS) offers a 100% scholarship, free hostel, and food for rural AP government junior college toppers."},
        {"instruction":"Who is eligible for the STARS program?","response":"Support The Advancement of Rural Students (STARS) offers a 100% scholarship, free hostel, and food for rural AP government junior college toppers."},
        {"instruction":"How does the university teach entrepreneurship?","response":"In partnership with the Wadhwani Foundation, over 7500 students are trained annually in idea validation and business venture formation."},
        {"instruction":"Are there startup training courses for students?","response":"In partnership with the Wadhwani Foundation, over 7500 students are trained annually in idea validation and business venture formation."},
        {"instruction":"Who helps the university conduct entrepreneurship training?","response":"In partnership with the Wadhwani Foundation, over 7500 students are trained annually in idea validation and business venture formation."},
        {"instruction":"What is the role of VTBIF?","response":"The VITAP TBI Foundation (VTBIF) is a Section-8 company that supports tech startups through incubation and product development."},
        {"instruction":"Which entity handles business incubation on campus?","response":"The VITAP TBI Foundation (VTBIF) is a Section-8 company that supports tech startups through incubation and product development."},
        {"instruction":"What does the university's startup incubator do?","response":"The VITAP TBI Foundation (VTBIF) is a Section-8 company that supports tech startups through incubation and product development."}
    ],

    "faculty.jsonl": [
        {"instruction":"What is the university's target Faculty-Student Ratio?","response":"The Institutional Development Plan targets achieving a Faculty-Student Ratio (FSR) of 1:15."},
        {"instruction":"What FSR does the university aim for?","response":"The Institutional Development Plan targets achieving a Faculty-Student Ratio (FSR) of 1:15."},
        {"instruction":"How many students per faculty member is the university targeting?","response":"The Institutional Development Plan targets achieving a Faculty-Student Ratio (FSR) of 1:15."},
        {"instruction":"What is the V-LAUNCH program?","response":"V-LAUNCH provides internal seed funding (up to Rs. 2.00 Lakhs) for a faculty member to collaborate with students to develop product prototypes."},
        {"instruction":"How much funding does a V-LAUNCH project receive?","response":"V-LAUNCH provides internal seed funding (up to Rs. 2.00 Lakhs) for a faculty member to collaborate with students to develop product prototypes."},
        {"instruction":"What scheme gives seed money for faculty-student prototypes?","response":"V-LAUNCH provides internal seed funding (up to Rs. 2.00 Lakhs) for a faculty member to collaborate with students to develop product prototypes."},
        {"instruction":"What is the target for external research funding?","response":"The university aims to fetch external research funding of at least 10 crores, or 2 crores per year."},
        {"instruction":"How much external funding does the university want to generate annually?","response":"The university aims to fetch external research funding of at least 10 crores, or 2 crores per year."},
        {"instruction":"What are the financial goals for research grants?","response":"The university aims to fetch external research funding of at least 10 crores, or 2 crores per year."},
        {"instruction":"How many research papers should a faculty member publish?","response":"The university targets an average of 4 publications per faculty member."},
        {"instruction":"What is the publication quota or target for professors?","response":"The university targets an average of 4 publications per faculty member."},
        {"instruction":"What is the 5-year goal for faculty research output?","response":"The university targets an average of 4 publications per faculty member."},
        {"instruction":"Are there plans to build houses for faculty on campus?","response":"Yes, the IDP includes action points to construct on-campus residential facilities for the faculty."},
        {"instruction":"Will faculty get accommodation inside the university?","response":"Yes, the IDP includes action points to construct on-campus residential facilities for the faculty."},
        {"instruction":"Does the infrastructure plan include faculty quarters?","response":"Yes, the IDP includes action points to construct on-campus residential facilities for the faculty."}
    ],

    "academics.jsonl": [
        {"instruction":"What is the DYOD program?","response":"'Design Your Own Degree' (DYOD) allows students to customize their academic path by choosing minors, specializations, and double majors."},
        {"instruction":"What does DYOD stand for in academics?","response":"'Design Your Own Degree' (DYOD) allows students to customize their academic path by choosing minors, specializations, and double majors."},
        {"instruction":"How does the university allow students to customize degrees?","response":"'Design Your Own Degree' (DYOD) allows students to customize their academic path by choosing minors, specializations, and double majors."},
        {"instruction":"Can I take a double major?","response":"'Design Your Own Degree' (DYOD) allows students to customize their academic path by choosing minors, specializations, and double majors."},
        {"instruction":"What is the Engineering Clinics course?","response":"It is a hands-on, project-based learning course where first and second-year students collaborate to build working prototypes."},
        {"instruction":"How do students get hands-on prototype experience?","response":"It is a hands-on, project-based learning course where first and second-year students collaborate to build working prototypes."},
        {"instruction":"What happens in the Engineering Clinics?","response":"It is a hands-on, project-based learning course where first and second-year students collaborate to build working prototypes."},
        {"instruction":"Does the curriculum involve industry experts?","response":"Yes, the 8th module of every subject is taught by visiting industry experts to connect classroom concepts to real-world practices."},
        {"instruction":"Are guest lectures integrated into the syllabus?","response":"Yes, the 8th module of every subject is taught by visiting industry experts to connect classroom concepts to real-world practices."},
        {"instruction":"Who teaches the 8th module of academic subjects?","response":"Yes, the 8th module of every subject is taught by visiting industry experts to connect classroom concepts to real-world practices."},
        {"instruction":"What is the question paper code for a Ph.D. in Computer Science?","response":"The question paper code for Computer Science and Engineering is CIE."},
        {"instruction":"If I apply for a Ph.D. in CSE, what is the exam code?","response":"The question paper code for Computer Science and Engineering is CIE."},
        {"instruction":"What exam code should I use for a Ph.D. in Information Technology?","response":"The question paper code for Computer Science and Engineering is CIE."},
        {"instruction":"What are the core research domains for the Deep Tech Fellowship?","response":"Domains include Generative AI, Quantum Computing, Blockchain, Space Technologies, and Precision Agriculture."},
        {"instruction":"Which fields qualify for the Chancellor's Deep Tech Fellowship?","response":"Domains include Generative AI, Quantum Computing, Blockchain, Space Technologies, and Precision Agriculture."},
        {"instruction":"What topics does the Deep Tech Ph.D. focus on?","response":"Domains include Generative AI, Quantum Computing, Blockchain, Space Technologies, and Precision Agriculture."},
        {"instruction":"What is the presentation mode for Paper 475 'Novel Federated Edge Learning'?","response":"Paper 475 is presented ONLINE in Track 1D at the AISP conference."},
        {"instruction":"Is the federated edge learning paper presented online or offline?","response":"Paper 475 is presented ONLINE in Track 1D at the AISP conference."},
        {"instruction":"Which track hosts paper 475 online?","response":"Paper 475 is presented ONLINE in Track 1D at the AISP conference."},
        {"instruction":"What is the title of Paper ID 309?","response":"The paper is titled 'Vehicle Tracking and License Plate Recognition Using YOLOv11 Integrated with OCR'."},
        {"instruction":"Which paper covers vehicle tracking using YOLOv11?","response":"The paper is titled 'Vehicle Tracking and License Plate Recognition Using YOLOv11 Integrated with OCR'."},
        {"instruction":"What topic does Paper 309 address at the conference?","response":"The paper is titled 'Vehicle Tracking and License Plate Recognition Using YOLOv11 Integrated with OCR'."}
    ]
}

for filename, records in datasets.items():
    filepath = os.path.join(dataset_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

combined_path = os.path.join(dataset_dir, "combined.jsonl")

# Order the keys so that it combines files in the exact same order
ordered_filenames = [
    "regulations.jsonl",
    "hostel.jsonl",
    "admissions.jsonl",
    "ethics.jsonl",
    "ipr.jsonl",
    "placements.jsonl",
    "faculty.jsonl",
    "academics.jsonl"
]

with open(combined_path, "w", encoding="utf-8") as outfile:
    for filename in ordered_filenames:
        filepath = os.path.join(dataset_dir, filename)

        with open(filepath, "r", encoding="utf-8") as infile:
            outfile.write(infile.read())

print("Dataset created successfully!")
print("Location:", os.path.abspath(dataset_dir))
print("Combined dataset:", os.path.abspath(combined_path))
