import sys
import os
from dotenv import load_dotenv
import streamlit as st

# Load .env only if not on Streamlit Cloud
if not st.secrets:
    load_dotenv()

# Merge st.secrets into os.environ if running on Streamlit Cloud
for key, value in st.secrets.items():
    os.environ[key] = str(value)

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from src.chain import get_chain
from src.db import store_feedback, create_database
from src.vector_search import close_connection

# Call create_database() to ensure the table is created
create_database()

# Streamlit App Title
st.title("Medical EHR GraphRAG")

# Initialize session state for storing context
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None

if "note_type" not in st.session_state:
    st.session_state.note_type = None

if "response" not in st.session_state:
    st.session_state.response = None

if "submitted_query" not in st.session_state:
    st.session_state.submitted_query = None

if "chain" not in st.session_state:
    with st.spinner("Initializing medical knowledge base..."):
        st.session_state.chain = get_chain(include_vector_search=True)

# Create sidebar for patient selection and filtering options
with st.sidebar:
    st.header("Filter Options")
    
    # Patient ID input
    st.markdown("### Patient Filter")
    patient_id_input = st.text_input(
        "Enter Patient ID (optional)",
        placeholder="e.g., 12345678",
        help="Leave empty to search across all patients"
    )
    
    # Set patient_id in session state
    if patient_id_input:
        st.session_state.patient_id = patient_id_input
        st.success(f"Filtering for patient: {patient_id_input}")
    else:
        st.session_state.patient_id = None
    
    # Note type selection
    note_type = st.radio(
        "Select Note Type to Search",
        ["All Medical Notes", "Discharge Notes Only", "Radiology Reports Only"],
        index=0  # Default to "All Medical Notes"
    )
    
    # Set note_type in session state
    if note_type == "Discharge Notes Only":
        st.session_state.note_type = "discharge"
        st.info("Searching discharge notes only")
    elif note_type == "Radiology Reports Only":
        st.session_state.note_type = "radiology"
        st.info("Searching radiology reports only")
    else:
        st.session_state.note_type = None

    st.divider()
    st.header("Advanced Settings")
    
    st.subheader("Vector Search Settings")
    vector_limit = st.slider(
        "Number of documents to retrieve", 
        min_value=1, 
        max_value=10, 
        value=3
    )
    
    max_chars_per_doc = st.slider(
        "Maximum characters per document", 
        min_value=500, 
        max_value=5000, 
        value=1500,
        step=500
    )
    
    st.subheader("Graph Database Settings")
    cypher_limit = st.slider(
        "Maximum graph records to return", 
        min_value=5, 
        max_value=50, 
        value=25,
        step=5
    )
    
    # Store settings in session state
    st.session_state.vector_limit = vector_limit
    st.session_state.max_chars_per_doc = max_chars_per_doc
    st.session_state.cypher_limit = cypher_limit

# Always update context values in case they changed
if "chain" in st.session_state:
    st.session_state.chain.context["patient_id"] = st.session_state.patient_id
    st.session_state.chain.context["note_type"] = st.session_state.note_type
    st.session_state.chain.context["vector_limit"] = st.session_state.vector_limit

# Define a function to handle query submission
def submit_query():
    if st.session_state.query_input:  # Check if there's a query
        with st.spinner("Searching medical records..."):
            # Using the chain with context already set
            st.session_state.response = st.session_state.chain.invoke(st.session_state.query_input)
            st.session_state.submitted_query = st.session_state.query_input

# Main area - Query input and results
st.header("Medical Information Query")

# Display current filtering state
if st.session_state.patient_id:
    st.info(f"Currently filtering for patient: {st.session_state.patient_id}")
if st.session_state.note_type:
    filter_text = "discharge notes" if st.session_state.note_type == "discharge" else "radiology reports"
    st.info(f"Searching only in {filter_text}")

# Quick Query Examples
st.subheader("Example Queries")
st.write("Click a button to see example query formats:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏥 Imaging Results", key="quick_query_1"):
        st.session_state.query_input = "What imaging studies were performed for this patient?"
        st.rerun()

with col2:
    if st.button("📋 Discharge Summary", key="quick_query_2"):
        st.session_state.query_input = "Summarize the patient's discharge information"
        st.rerun()

with col3:
    if st.button("💊 Medications", key="quick_query_3"):
        st.session_state.query_input = "List the patient's current medications"
        st.rerun()

st.divider()

# Input field for user query
query = st.text_input("Enter your medical query:", key="query_input")

# Submit button
st.button("Submit Query", on_click=submit_query)

# Display results if a query has been submitted
if st.session_state.response:
    st.markdown("### Response:")
    st.markdown(st.session_state.response)
    
    # Add a debug section for query details
    with st.expander("Debug Information"):
        st.markdown("### Query Processing Details")
        
        # Display the generated Cypher query if available
        if hasattr(st.session_state.chain, 'last_cypher_query') and st.session_state.chain.last_cypher_query:
            st.markdown("#### Generated Cypher Query")
            st.code(st.session_state.chain.last_cypher_query, language="cypher")
        
        # Display the graph results if available
        if hasattr(st.session_state.chain, 'last_graph_results') and st.session_state.chain.last_graph_results:
            st.markdown("#### Graph Results")
            st.markdown(f"Found {len(st.session_state.chain.last_graph_results)} results from the graph database")
            
            # Create tabs for different ways to view the results
            tab1, tab2 = st.tabs(["Summary View", "Detailed View"])
            
            with tab1:
                # Display a summary of the graph results
                for i, result in enumerate(st.session_state.chain.last_graph_results[:5]):  # Show first 5 results
                    st.markdown(f"**Result {i+1}:**")
                    # Create a cleaner display of the result
                    for key, value in result.items():
                        if isinstance(value, dict):
                            # It's likely a node or relationship
                            st.markdown(f"**{key}:** (Object with {len(value)} properties)")
                            # Show a subset of important properties
                            important_props = ["id", "name", "subject_id", "hadm_id", "note_id"]
                            shown_props = {}
                            for prop in important_props:
                                if prop in value:
                                    shown_props[prop] = value[prop]
                            
                            # Add a few more properties if available
                            other_props = [p for p in value.keys() if p not in important_props]
                            for prop in other_props[:3]:  # Show up to 3 additional properties
                                shown_props[prop] = value[prop]
                                
                            st.json(shown_props)
                        else:
                            # It's a simple value
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:97] + "..."
                            st.markdown(f"**{key}:** {value}")
                    st.divider()
                
                if len(st.session_state.chain.last_graph_results) > 5:
                    st.info(f"{len(st.session_state.chain.last_graph_results) - 5} more results not shown")
            
            with tab2:
                # Option to view individual results in more detail
                result_index = st.selectbox(
                    "Select result to view in detail", 
                    range(len(st.session_state.chain.last_graph_results)),
                    format_func=lambda x: f"Result {x+1}"
                )
                
                if result_index is not None:
                    st.json(st.session_state.chain.last_graph_results[result_index])
        
        # Display information about vector search
        if hasattr(st.session_state.chain, 'vector_search_info'):
            st.markdown("#### Vector Search Information")
            enabled = st.session_state.chain.vector_search_info.get("enabled", False)
            st.markdown(f"Vector search enabled: {enabled}")
            if 'vector_limit' in st.session_state.chain.context:
                st.markdown(f"Vector limit: {st.session_state.chain.context['vector_limit']}")
            if 'note_type' in st.session_state.chain.context and st.session_state.chain.context['note_type']:
                st.markdown(f"Note type filter: {st.session_state.chain.context['note_type']}")
            if hasattr(st.session_state.chain, 'last_sources'):
                vector_sources = [s for s in st.session_state.chain.last_sources if 'score' in s]
                st.markdown(f"Vector sources found: {len(vector_sources)}")
                
    # Get the sources from chain context if available
    if hasattr(st.session_state.chain, 'last_sources') and st.session_state.chain.last_sources:
        with st.expander("View Sources"):
            st.markdown("### Sources Used")
            
            for i, source in enumerate(st.session_state.chain.last_sources):
                st.markdown(f"**Source {i+1}:** {source['note_id']}")
                
                # Determine the source type based on the note_id or node_type
                if 'node_type' in source and isinstance(source['node_type'], list) and 'RadiologyReport' in source['node_type']:
                    source_type = "Radiology Report"
                elif 'node_type' in source and isinstance(source['node_type'], list) and 'DischargeNote' in source['node_type']:
                    source_type = "Discharge Summary" 
                elif '-RR-' in source['note_id']:
                    source_type = "Radiology Report"
                elif '-DS-' in source['note_id']:
                    source_type = "Discharge Summary"
                else:
                    source_type = "Medical Note"
                    
                st.markdown(f"**Type:** {source_type}")
                
                if 'score' in source:
                    st.markdown(f"**Relevance Score:** {source['score']:.4f}")
                    
                if 'patient_id' in source:
                    st.markdown(f"**Patient ID:** {source['patient_id']}")
                    
                # Show a preview of the text (first 200 chars)
                if 'full_text' in source and source['full_text']:
                    preview = source['full_text'][:200] + "..." if len(source['full_text']) > 200 else source['full_text']
                    st.markdown("**Text Preview:**")
                    st.text(preview)
                    
                    # Add a checkbox to toggle full text visibility
                    show_full_text = st.checkbox(f"Show full text for Source {i+1}", key=f"full_text_{i}")
                    if show_full_text:
                        st.text_area("Full Document", source['full_text'], height=300, key=f"full_text_area_{i}")
                    
                    st.divider()
    
    # Add expander for filter information
    with st.expander("Filter Details"):
        st.write(f"Patient ID: {st.session_state.patient_id or 'All Patients'}")
        if st.session_state.note_type:
            st.write(f"Note Type: {st.session_state.note_type}")
        else:
            st.write("Note Type: All Notes")
    
    # Feedback section
    st.divider()
    st.markdown("### Was this response helpful?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👍 Yes, this was helpful"):
            store_feedback(st.session_state.submitted_query, st.session_state.response, 1)
            st.success("Thank you for your feedback!")
            
    with col2:
        if st.button("👎 No, needs improvement"):
            store_feedback(st.session_state.submitted_query, st.session_state.response, -1)
            st.success("Thank you for your feedback!")

# Ensure connection is closed when the app is terminated
def cleanup():
    close_connection()

# Register the cleanup function to be called when the app terminates
import atexit
atexit.register(cleanup)