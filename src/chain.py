from langchain_openai import ChatOpenAI
from src.graph import connect_to_graph
from src.prompts import CYPHER_GENERATION_PROMPT, MEDICAL_QA_PROMPT, HYBRID_QA_PROMPT
from src.vector_search import find_similar_documents, close_connection

def get_chain(include_vector_search=True):
    """Create a custom chain that doesn't rely on LangChain's Neo4jGraph."""
    graph = connect_to_graph()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def generate_cypher(question, patient_id=None):
        """Generate Cypher query from the question, optionally filtering by patient_id"""
        # If patient_id is provided, modify the question to include this context
        if patient_id:
            question = f"For patient with subject_id '{patient_id}', {question}"
            print(f"Modified question with patient filter: {question}")
        
        prompt = CYPHER_GENERATION_PROMPT.format(
            schema=graph.schema,
            question=question
        )
        response = llm.invoke(prompt)
        return response.content
    
    # Custom chain class with context support
    class CustomChain:
        def __init__(self, invoke_func):
            self.invoke = invoke_func
            self.context = {
                "patient_id": None,
                "note_type": None,  # Can be 'discharge', 'radiology', or None for all
                "vector_limit": 3,  # Default to 3 documents
                "max_chars_per_doc": 1500,  # Default to 1500 characters per document
                "cypher_limit": 25  # Default to 25 Cypher records
            }
            self.last_sources = []  # Store the sources used for the last query
            self.last_cypher_query = ""  # Store the last Cypher query
            self.last_graph_results = []  # Store the last graph results
            self.vector_search_info = {}  # Info about vector search
    
    # Create a custom QA function that can access the chain instance
    def answer_question(question, custom_chain=None):
        # Get context parameters
        patient_id = None
        note_type = None
        vector_limit = 3
        max_chars_per_doc = 1500
        cypher_limit = 25
        
        if custom_chain and hasattr(custom_chain, 'context'):
            patient_id = custom_chain.context.get("patient_id")
            note_type = custom_chain.context.get("note_type")
            vector_limit = custom_chain.context.get("vector_limit", 3)
            max_chars_per_doc = custom_chain.context.get("max_chars_per_doc", 1500)
            cypher_limit = custom_chain.context.get("cypher_limit", 25)
            
            if patient_id:
                print(f"Using specified patient ID: {patient_id}")
            if note_type:
                print(f"Filtering for note type: {note_type}")
        
        cypher_query = generate_cypher(question, patient_id)
        print(f"Generated Cypher query: {cypher_query}")
        
        # Store the Cypher query
        if custom_chain:
            custom_chain.last_cypher_query = cypher_query
        
        try:
            results = graph.query(cypher_query)

            # Store the graph results
            if custom_chain:
                custom_chain.last_graph_results = results[:cypher_limit]  # Store limited results

            # Print detailed results from Cypher query
            print("\n=== CYPHER QUERY RESULTS ===")
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results[:5]):  # Show first 5 results
                    print(f"  Result {i+1}:")
                    for key, value in result.items():
                        print(f"    {key}: {value}")
                if len(results) > 5:
                    print(f"  ... and {len(results) - 5} more results")
            else:
                print("No results returned from Cypher query")

            # Limit number of records
            if len(results) > cypher_limit:
                print(f"Limiting Cypher results to {cypher_limit} records")
                results = results[:cypher_limit]

            # Build context from Cypher results
            context_items = []
            for i, record in enumerate(results):
                # Process each record, limiting properties
                record_context = process_record_for_context(record, max_properties=5)
                context_items.append(record_context)
            
            context = "\n".join(context_items)
            print(f"Graph query returned {len(results)} results")
            
            # If vector search is enabled, get vector results and combine them
            if include_vector_search:
                print("\nPerforming vector similarity search...")
                # Store vector search info
                if custom_chain:
                    custom_chain.vector_search_info = {
                        "enabled": True,
                        "limit": vector_limit,
                        "note_type": note_type
                    }
                
                vector_results = find_similar_documents(
                    question, 
                    limit=vector_limit,  # Use the vector_limit
                    note_type=note_type,
                    patient_id=patient_id  # Add patient_id filtering
                )
                
                # Update vector search info with results count
                if custom_chain and vector_results:
                    custom_chain.vector_search_info["results_count"] = len(vector_results)

                if vector_results:
                    print(f"Combining graph results with {len(vector_results)} vector results")
                    vector_context = "\n\n" + "\n\n".join([
                        f"Document {i+1}: {r['note_id']} (Similarity: {r['score']:.4f})\n\n{r['full_text']}" 
                        for i, r in enumerate(vector_results)
                    ])
                    
                    # Use hybrid prompt to combine graph and vector results
                    hybrid_prompt = HYBRID_QA_PROMPT.format(
                        question=question,
                        graph_context=context,
                        vector_context=vector_context
                    )
                    print("Using hybrid prompt with both graph and vector results")
                    response = llm.invoke(hybrid_prompt)
                    
                    # Store sources for both vector and graph results
                    all_sources = []

                    # Add graph results as sources if they exist and have useful information
                    if results and len(results) > 0:
                        for i, record in enumerate(results):
                            if 'note_id' in record and record['note_id'] and 'text' in record and record['text']:
                                graph_source = {
                                    'note_id': record['note_id'],
                                    'full_text': record['text'],
                                    'source_type': 'graph'
                                }
                                # Add patient_id if available
                                if 'subject_id' in record:
                                    graph_source['patient_id'] = record['subject_id']
                                
                                all_sources.append(graph_source)

                    # Add vector results as sources
                    if vector_results and len(vector_results) > 0:
                        for vec_result in vector_results:
                            all_sources.append(vec_result)  # Vector results already have the right format

                    # Store the sources in the chain
                    if custom_chain:
                        custom_chain.last_sources = all_sources

                    return response.content
                else:
                    print("No vector results found, using graph results only")
            else:
                print("Vector search disabled, using graph results only")
        
            # If no vector search or no vector results, use standard medical QA prompt
            qa_prompt = MEDICAL_QA_PROMPT.format(
                question=question,
                context=context
            )
            response = llm.invoke(qa_prompt)
            
            # Store sources for both vector and graph results
            all_sources = []

            # Add graph results as sources if they exist and have useful information
            if results and len(results) > 0:
                for i, record in enumerate(results):
                    if 'note_id' in record and record['note_id'] and 'text' in record and record['text']:
                        graph_source = {
                            'note_id': record['note_id'],
                            'full_text': record['text'],
                            'source_type': 'graph'
                        }
                        # Add patient_id if available
                        if 'subject_id' in record:
                            graph_source['patient_id'] = record['subject_id']
                        
                        all_sources.append(graph_source)

            # Add vector results as sources
            if vector_results and len(vector_results) > 0:
                for vec_result in vector_results:
                    all_sources.append(vec_result)  # Vector results already have the right format

            # Store the sources in the chain
            if custom_chain:
                custom_chain.last_sources = all_sources

            return response.content
            
        except Exception as e:
            print(f"Error executing query: {e}")
            return f"I couldn't execute the query due to an error: {e}"
    
    # Create a chain instance
    chain_instance = CustomChain(None)  # Create instance first
    
    # Define the invoke method that passes the chain instance to answer_question
    def chain_invoke(question):
        return answer_question(question, chain_instance)
    
    # Set the invoke method on the chain instance
    chain_instance.invoke = chain_invoke
    
    return chain_instance

def process_record_for_context(record, max_properties=15):
    """Process a Neo4j record for context, limiting properties to control size"""
    record_parts = []
    
    for key, value in record.items():
        if isinstance(value, dict) and len(value) > max_properties:
            # It's a node or relationship with many properties
            # Keep id/name properties and limit others
            important_props = {}
            for prop in ['id', 'name', 'subject_id', 'hadm_id', 'note_id']:
                if prop in value:
                    important_props[prop] = value[prop]
            
            # Fill remaining slots with other properties
            remaining_slots = max_properties - len(important_props)
            for prop, val in value.items():
                if prop not in important_props and remaining_slots > 0:
                    important_props[prop] = val
                    remaining_slots -= 1
            
            # Truncate text fields if they exist and are too long
            if 'text' in important_props and isinstance(important_props['text'], str) and len(important_props['text']) > 200:
                important_props['text'] = important_props['text'][:197] + "..."
            
            record_parts.append(f"{key}: {important_props}")
        else:
            # Handle text truncation for direct string values
            if isinstance(value, str) and len(value) > 200:
                value = value[:197] + "..."
            record_parts.append(f"{key}: {value}")
    
    return ", ".join(record_parts)