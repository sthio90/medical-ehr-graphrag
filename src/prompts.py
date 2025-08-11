from langchain_core.prompts.prompt import PromptTemplate

# Cypher generation template
CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

IMPORTANT: Always use the exact relationship patterns shown in the schema. Pay special attention to:
- Patient nodes connect to Admission nodes via HAS_ADMISSION relationship
- Admission nodes connect to RadiologyReport nodes via INCLUDES_RADIOLOGY_REPORT relationship
- Admission nodes connect to DischargeNote nodes via INCLUDES_DISCHARGE_NOTE relationship

CRITICAL DATA AVAILABILITY CONSTRAINTS:
- Allergies are NOT stored in the structured database (not in Diagnosis, Medication, or any other nodes)
- Social history (smoking, alcohol, drugs) is NOT stored in the structured database
- Family history is NOT stored in the structured database
- Vital signs trends and detailed clinical observations are NOT stored in the structured database

If a question asks about allergies, social history, family history, or other data not in the structured database, return this exact query:
MATCH (p:Patient) WHERE p.subject_id = 'PLACEHOLDER' RETURN 'Data not available in structured database' AS message

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

IMPORTANT: Always use the exact relationship patterns shown in the schema. Pay special attention to:
- Patient nodes connect to Admission nodes via HAS_ADMISSION relationship
- Admission nodes connect to RadiologyReport nodes via INCLUDES_RADIOLOGY_REPORT relationship
- Patient nodes may also connect to RadiologyReport nodes directly via HAS_RADIOLOGY_REPORT relationship
- Admission nodes connect to DischargeNote nodes via INCLUDES_DISCHARGE_NOTE relationship

# Update the examples section with a more comprehensive radiology query:
Examples: Here are a few examples of generated Cypher statements for particular questions:
# How many patients have diabetes?
MATCH (p:Patient)-[:HAS_ADMISSION]->(a:Admission)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
WHERE d.long_title CONTAINS 'diabetes'
RETURN COUNT(DISTINCT p) AS number_of_patients_with_diabetes

# Does the patient have any documented allergies? (Allergies NOT in structured database)
MATCH (p:Patient) WHERE p.subject_id = '12345' RETURN 'Data not available in structured database' AS message

# Get all radiology reports for patient 10300608
MATCH (p:Patient)
WHERE p.subject_id: '10300608'
OPTIONAL MATCH (p)-[:HAS_ADMISSION]->(a:Admission)-[:INCLUDES_RADIOLOGY_REPORT]->(r1:RadiologyReport)
OPTIONAL MATCH (p)-[:HAS_RADIOLOGY_REPORT]->(r2:RadiologyReport)
WITH p, COLLECT(DISTINCT r1) + COLLECT(DISTINCT r2) AS reports
UNWIND reports AS r
RETURN DISTINCT r.note_id, r.text

# Give me a summary of patient 11649167.
MATCH (p:Patient)-[:HAS_ADMISSION]->(a:Admission)
WHERE p.subject_id = '10300608'
WITH p, a
OPTIONAL MATCH (a)-[r1:HAS_MEDICATION]->(m:Medication)
WHERE a.hadm_id = m.hadm_id
OPTIONAL MATCH (a)-[r2:HAS_DIAGNOSIS]->(d:Diagnosis)
WHERE a.hadm_id = d.hadm_id
OPTIONAL MATCH (a)-[r3:HAS_PROCEDURE]->(pr:Procedure)
WHERE a.hadm_id = pr.hadm_id
RETURN p, a, m, d, pr;

# CRITICAL PROPERTY MAPPING - Properties are NOT duplicated between node types:
# Patient node properties ONLY: anchor_age, anchor_year, anchor_year_group, dod, gender, subject_id
# Admission node properties ONLY: admission_location, admission_type, admit_provider_id, admittime, deathtime, dischtime, edouttime, edregtime, hadm_id, hospital_expire_flag, insurance, language, marital_status, race

# RULE: marital_status, insurance, race, language are ONLY available on Admission nodes - NEVER use p.marital_status
# RULE: anchor_year_group, anchor_age, anchor_year, gender, dod are ONLY available on Patient nodes - NEVER use a.anchor_year_group

# Example: Get marital status and anchor year group for patient 14037695 during admission 20844156
MATCH (p:Patient {{subject_id: '14037695'}})-[:HAS_ADMISSION]->(a:Admission {{hadm_id: '20844156'}})
RETURN a.marital_status, p.anchor_year_group

# More examples of correct property usage:
# For patient demographics that exist only on Patient nodes:
MATCH (p:Patient {{subject_id: '12345'}})
RETURN p.gender, p.anchor_age, p.anchor_year_group

# For admission demographics that exist only on Admission nodes:
MATCH (p:Patient {{subject_id: '12345'}})-[:HAS_ADMISSION]->(a:Admission {{hadm_id: '67890'}})
RETURN a.marital_status, a.insurance, a.race, a.language, p.gender, p.anchor_year_group

# Example: Get admission type and first procedure for a specific patient and admission
MATCH (p:Patient {{subject_id: '19801500'}})-[:HAS_ADMISSION]->(a:Admission {{hadm_id: '29382666'}})
OPTIONAL MATCH (a)-[:HAS_PROCEDURE]->(pr:Procedure)
WITH a, pr ORDER BY pr.seq_num, pr.chartdate
RETURN a.admission_type, COLLECT(pr.long_title)[0] AS first_procedure_title

# Example: Get procedures ordered by sequence number
MATCH (p:Patient {{subject_id: '12345'}})-[:HAS_ADMISSION]->(a:Admission {{hadm_id: '67890'}})
OPTIONAL MATCH (a)-[:HAS_PROCEDURE]->(pr:Procedure)
RETURN a.admission_type, pr.long_title, pr.seq_num ORDER BY pr.seq_num

# Example: Get procedure details including both description and ICD code
MATCH (p:Patient {{subject_id: '19801500'}})-[:HAS_ADMISSION]->(a:Admission {{hadm_id: '29382666'}})
OPTIONAL MATCH (a)-[:HAS_PROCEDURE]->(pr:Procedure)
WITH a, pr ORDER BY pr.seq_num, pr.chartdate
RETURN a.admission_type, 
       COLLECT(pr.long_title)[0] AS first_procedure_description,
       COLLECT(pr.icd_code)[0] AS first_procedure_code


The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

# Simplified medical QA prompt
MEDICAL_QA_TEMPLATE = """You are a medical database expert. 
Remember that subject_id values represent unique patients. 
Remember hadm_id represents unique admissions for a patient to the hospital.
Question: {question}
Result: {context}
Provide a clear and comprehensive medical interpretation. 
Do not provide recommendations:"""

MEDICAL_QA_PROMPT = PromptTemplate(
    template=MEDICAL_QA_TEMPLATE,
    input_variables=["question", "context"]
)

# Hybrid QA template that incorporates both graph and vector search results
HYBRID_QA_TEMPLATE = """
You are a helpful medical assistant that answers questions based on EHR (Electronic Health Record) data.
You have access to structured data from a graph database and unstructured text from clinical notes.

IMPORTANT DATA AVAILABILITY RULES:
The structured graph database contains: Patient demographics, Admissions, Diagnoses (ICD codes), Medications, Procedures, Lab results, and basic clinical data.
The structured graph database does NOT contain: Allergies, social history (smoking, alcohol), family history, detailed clinical observations, vital signs trends, or narrative clinical assessments.

PRIORITY RULES:
1. DATA TYPE ASSESSMENT: First determine if the question asks about data that exists in the structured database.
2. STRUCTURED DATA AUTHORITY: For data types that exist in structured form (demographics, diagnoses, medications, procedures, labs), prioritize structured data as authoritative unless queries are on radiology reports, discharge summaries or notes then refer to them more so.
3. CLINICAL NOTES PRIMARY: For data types NOT in structured form (allergies, social history, family history, clinical observations), rely primarily on clinical notes.
4. COMPLEMENTARY INTEGRATION: Use both sources when they provide complementary information.
5. CONFLICT RESOLUTION: If there's a conflict between structured data and clinical notes for the same data type, prioritize structured data and note the discrepancy.
6. HUMAN-READABLE DESCRIPTIONS: When medical procedures, diagnoses, or medications are available, always prefer the human-readable description (long_title, long_text) over codes (icd_code, ndc_code, etc.).

SPECIFIC DATA TYPE GUIDANCE:
- Allergies: Rely on clinical notes (not stored in structured database)
- Social history (smoking, alcohol, drugs): Rely on clinical notes
- Family history: Rely on clinical notes  
- Vital signs and trends: Rely on clinical notes
- Clinical observations and assessments: Rely on clinical notes
- Demographics, diagnoses, medications, procedures: Prioritize structured data

Question: {question}

Structured data from graph database:
{graph_context}

Relevant medical notes from vector search:
{vector_context}

Answer the question following these steps:
1. Determine what type of data the question is asking about
2. If asking about data NOT typically in structured databases (allergies, social history, etc.), focus primarily on clinical notes
3. If asking about structured data types, use structured data as primary source with clinical notes for context
4. For procedures, extract and use the "long_title" field to describe what was performed
5. Always cite your sources and indicate which information comes from structured data vs. clinical notes
6. If structured data returns empty/null results for data that should exist (like a failed query), acknowledge this and rely on clinical notes
"""

HYBRID_QA_PROMPT = PromptTemplate(
    template=HYBRID_QA_TEMPLATE,
    input_variables=["question", "graph_context", "vector_context"]
)