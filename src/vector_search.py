import os
from openai import OpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE, OPENAI_API_KEY

# Load environment variables
load_dotenv()

# Configure clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
neo4j_client = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

def generate_query_embedding(query_text):
    """Generate an embedding for a search query"""
    try:
        response = openai_client.embeddings.create(
            input=query_text,
            model="text-embedding-3-small"
        )
        return [float(x) for x in response.data[0].embedding]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None
      
def find_similar_documents(query_text, limit=3, note_type=None, patient_id=None):
    """Find documents similar to the query using vector search
      Args:
        query_text: The text to search for
        limit: Maximum number of results to return
        note_type: Optional note type to filter ('discharge', 'radiology', or None for all)
        patient_id: Optional patient ID to filter results to specific patient
    """
    print("\n=== VECTOR SEARCH ACTIVATED ===")
    print(f"Searching for documents similar to: '{query_text}'")
    if patient_id:
        print(f"Filtering for patient ID: {patient_id}")
    
    # Determine which index to search based on note_type
    if note_type == "discharge":
        index_name = "discharge_note_vector_idx"
        print(f"Searching only discharge notes")
    elif note_type == "radiology":
        index_name = "radiology_report_vector_idx"
        print(f"Searching only radiology reports")
    else:
        # When no specific type is selected, search both indexes
        print(f"Searching all medical notes (discharge notes and radiology reports)")
        results = []
        
        # First search discharge notes
        discharge_results = find_similar_documents(
            query_text, 
            limit=max(1, limit // 2),  # Split the limit between the two types
            note_type="discharge",
            patient_id=patient_id  # Pass patient_id to recursive calls
        )
        if discharge_results:
            results.extend(discharge_results)
        
        # Then search radiology reports
        radiology_results = find_similar_documents(
            query_text, 
            limit=max(1, limit // 2),
            note_type="radiology",
            patient_id=patient_id  # Pass patient_id to recursive calls
        )
        if radiology_results:
            results.extend(radiology_results)
        
        # Sort by similarity score and return top results
        if results:
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
        else:
            return []
    
    # Generate embedding for the query
    query_embedding = generate_query_embedding(query_text)
    if not query_embedding:
        print("Failed to generate query embedding")
        return []
    
    print(f"Generated embedding for query (dimension: {len(query_embedding)})")
      # Perform vector search using the appropriate index
    with neo4j_client.session(database=NEO4J_DATABASE) as session:
        try:
            # Build the Cypher query with optional patient ID filtering
            if patient_id:
                cypher_query = f"""
                CALL db.index.vector.queryNodes('{index_name}', {limit * 2}, $query_embedding)
                YIELD node, score
                WHERE node.subject_id = $patient_id
                RETURN node.note_id AS note_id, 
                       node.text AS full_text, 
                       score,
                       node.subject_id AS subject_id,
                       node.hadm_id AS hadm_id,
                       node.note_type AS note_type
                ORDER BY score DESC
                LIMIT $limit
                """
                query_params = {
                    'query_embedding': query_embedding, 
                    'patient_id': patient_id,
                    'limit': limit
                }
            else:
                cypher_query = f"""
                CALL db.index.vector.queryNodes('{index_name}', {limit}, $query_embedding)
                YIELD node, score
                RETURN node.note_id AS note_id, 
                       node.text AS full_text, 
                       score,
                       node.subject_id AS subject_id,
                       node.hadm_id AS hadm_id,
                       node.note_type AS note_type
                ORDER BY score DESC
                """
                query_params = {'query_embedding': query_embedding}            
            print(f"Executing vector search query on index: {index_name}")
            if patient_id:
                print(f"Filtering results for patient: {patient_id}")
            
            result = session.run(cypher_query, **query_params)
            records = list(result)
            
            if not records:
                print(f"No similar documents found in {index_name}")
                return []
            
            print(f"Found {len(records)} similar documents")
            
            # Format results
            formatted_results = []
            for record in records:
                formatted_results.append({
                    'note_id': record['note_id'],
                    'full_text': record['full_text'] if record['full_text'] else '',
                    'score': float(record['score']),
                    'subject_id': record['subject_id'],
                    'hadm_id': record['hadm_id'],
                    'note_type': record['note_type']
                })
                print(f"  - {record['note_id']} (Score: {record['score']:.4f}, Patient: {record['subject_id']}, Admission: {record['hadm_id']})")
            
            return formatted_results
            
        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

def close_connection():
    """Close the Neo4j connection"""
    if neo4j_client:
        neo4j_client.close()
        print("Neo4j connection closed")