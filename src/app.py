# In app.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chain import get_chain
from src.vector_search import close_connection

def query_with_patient(query, patient_id=None, note_type=None, vector_limit=3, max_chars_per_doc=1500, cypher_limit=25):
    """Execute a query with optional patient ID and note type filters"""
    try:
        chain = get_chain(include_vector_search=True)
        
        # Store the context parameters
        chain.context = {
            "patient_id": patient_id,
            "note_type": note_type,
            "vector_limit": vector_limit,
            "max_chars_per_doc": max_chars_per_doc,
            "cypher_limit": cypher_limit
        }
            
        response = chain.invoke(query)
        last_sources = getattr(chain, 'last_sources', []) # Safely get last_sources
        return response, last_sources # Return sources as well
    finally:
        close_connection()

if __name__ == "__main__":
    # For CLI testing
    patient_list = ["10300608", "11215757", "11318863", "11649167", "12632455", 
                   "12884129", "13242560", "17518372", "18648042", "18707455"]
    
    print("\n=== Medical Information Retrieval System ===")
    print("\nAvailable patients:")
    for i, patient_id in enumerate(patient_list):
        print(f"{i+1}. Patient {patient_id}")
    
    patient_choice = input("\nSelect a patient number (or press Enter for all patients): ")
    selected_patient = None
    
    if patient_choice.strip():
        try:
            index = int(patient_choice) - 1
            if 0 <= index < len(patient_list):
                selected_patient = patient_list[index]
                print(f"Selected Patient: {selected_patient}")
            else:
                print("Invalid selection, searching across all patients")
        except ValueError:
            print("Invalid input, searching across all patients")
    
    print("\nSelect note type to search:")
    print("1. All medical notes")
    print("2. Discharge notes only")
    print("3. Radiology reports only")
    note_choice = input("Enter your choice (1-3): ")
    
    selected_note_type = None
    if note_choice == "2":
        selected_note_type = "discharge"
        print("Searching discharge notes only")
    elif note_choice == "3":
        selected_note_type = "radiology"
        print("Searching radiology reports only")
    else:
        print("Searching all medical notes")
    
    query = input("\nEnter your medical query: ")
    
    print("\nProcessing query...")
    response = query_with_patient(query, selected_patient, selected_note_type)
    response, sources = query_with_patient(query, selected_patient, selected_note_type) # Unpack
    
    print("\nResponse:\n")
    print(response)
    
    # Print sources if available
    if hasattr(chain, 'last_sources') and chain.last_sources:
        print("\n=== Sources Used ===")
        for i, source in enumerate(chain.last_sources):
            # Determine the source type
            if 'node_type' in source and 'RadiologyReport' in source['node_type']:
                source_type = "Radiology Report"
            elif 'node_type' in source and 'DischargeNote' in source['node_type']:
                source_type = "Discharge Summary"
            elif '-RR-' in source['note_id']:
                source_type = "Radiology Report"
            elif '-DS-' in source['note_id']:
                source_type = "Discharge Summary"
            else:
                source_type = "Medical Note"
                
            print(f"Source {i+1}: {source['note_id']} ({source_type})")
            if 'score' in source:
                print(f"Relevance Score: {source['score']:.4f}")
            if 'patient_id' in source:
                print(f"Patient ID: {source['patient_id']}")
            
            # Print a preview of the text (first 100 chars)
            if 'full_text' in source and source['full_text']:
                preview = source['full_text'][:100] + "..." if len(source['full_text']) > 100 else source['full_text']
                print(f"Text Preview: {preview}")
            print()

    print("\n=== Search complete ===")