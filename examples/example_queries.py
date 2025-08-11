"""
Example queries for the Medical GraphRAG system.
These queries demonstrate various types of medical information retrieval
without referencing specific patient IDs.
"""

# General medical information queries
GENERAL_QUERIES = [
    "What medications is the patient currently taking?",
    "Summarize the patient's medical history",
    "What are the patient's current diagnoses?",
    "List all allergies documented for this patient",
    "What was the reason for the patient's last admission?",
]

# Discharge-related queries
DISCHARGE_QUERIES = [
    "Summarize the patient's discharge instructions",
    "What follow-up appointments were scheduled at discharge?",
    "What medications were prescribed at discharge?",
    "What were the discharge diagnoses?",
    "What lifestyle modifications were recommended?",
]

# Radiology and imaging queries
RADIOLOGY_QUERIES = [
    "What imaging studies were performed during this admission?",
    "Summarize the findings from the chest X-ray",
    "Were there any abnormal findings on the CT scan?",
    "What did the MRI results show?",
    "Compare the current imaging with previous studies",
]

# Laboratory and test result queries
LAB_QUERIES = [
    "What were the patient's most recent lab results?",
    "Show the trend of creatinine levels over time",
    "Were there any abnormal blood test results?",
    "What were the cardiac enzyme levels?",
    "List all microbiological test results",
]

# Treatment and procedure queries
TREATMENT_QUERIES = [
    "What procedures were performed during this admission?",
    "What treatments has the patient received?",
    "Were there any complications during treatment?",
    "What was the response to the prescribed therapy?",
    "List all surgical procedures performed",
]

# Complex multi-part queries
COMPLEX_QUERIES = [
    "Compare the patient's condition at admission versus discharge",
    "What changes were made to the patient's medication regimen and why?",
    "Summarize the patient's cardiovascular status including tests and findings",
    "What risk factors does the patient have for readmission?",
    "Provide a comprehensive summary of the patient's current status",
]

def print_example_queries():
    """Print all example queries organized by category."""
    categories = [
        ("General Medical Information", GENERAL_QUERIES),
        ("Discharge-Related", DISCHARGE_QUERIES),
        ("Radiology and Imaging", RADIOLOGY_QUERIES),
        ("Laboratory and Test Results", LAB_QUERIES),
        ("Treatment and Procedures", TREATMENT_QUERIES),
        ("Complex Multi-Part Queries", COMPLEX_QUERIES),
    ]
    
    for category_name, queries in categories:
        print(f"\n{category_name}:")
        print("-" * len(category_name))
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query}")

if __name__ == "__main__":
    print("Medical GraphRAG - Example Queries")
    print("=" * 50)
    print("\nThese example queries demonstrate the types of questions")
    print("the system can answer about patient medical records.")
    print("\nNote: Remember to set a patient ID filter when using these queries")
    print("to get patient-specific results.")
    print_example_queries()