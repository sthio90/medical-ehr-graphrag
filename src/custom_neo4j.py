from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase

class SimpleNeo4jGraph:
    """A simple Neo4j graph implementation that doesn't require APOC."""
    
    def __init__(self, url, username, password, database="neo4j"):
        self.url = url
        self.username = username
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(url, auth=(username, password))
        self.schema = self._get_schema()
        
    def _get_schema(self) -> str:
        """Extract detailed schema information without APOC."""
        with self.driver.session(database=self.database) as session:
            # Get node labels
            labels_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in labels_result]
            
            # Get node properties for each label
            node_properties = {}
            for label in labels:
                # Get all unique properties across multiple nodes of this label
                props_query = f"""
                MATCH (n:{label})
                WITH n LIMIT 100
                UNWIND keys(n) AS prop
                RETURN DISTINCT prop
                ORDER BY prop
                """
                props_result = session.run(props_query)
                node_properties[label] = [record["prop"] for record in props_result]
            
            # Get relationship patterns
            rel_patterns_query = """
            MATCH (a)-[r]->(b)
            RETURN DISTINCT labels(a)[0] as source_label, 
                type(r) as relationship, 
                labels(b)[0] as target_label, 
                count(*) as frequency
            ORDER BY frequency DESC
            """
            rel_patterns_result = session.run(rel_patterns_query)
            rel_patterns = [
                {
                    "source": record["source_label"], 
                    "relationship": record["relationship"], 
                    "target": record["target_label"],
                    "count": record["frequency"]
                }
                for record in rel_patterns_result
            ]
            
            # Build a detailed schema string
            schema = "# Neo4j Schema\n\n## Node Labels\n"
            for label in labels:
                schema += f"- {label}"
                if label in node_properties and node_properties[label]:
                    schema += f" (Properties: {', '.join(node_properties[label])})"
                schema += "\n"
            
            schema += "\n## Relationships\n"
            for pattern in rel_patterns:
                schema += f"- ({pattern['source']})-[:{pattern['relationship']}]->({pattern['target']}) ({pattern['count']} occurrences)\n"
            
            return schema
    
    def query(self, query_str, params=None):
        """Execute a Cypher query and return the results."""
        result_limit = 25  # Default maximum number of records to return
        property_limit = 20  # Default maximum number of properties per node to include
        
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run(query_str, params or {})
                all_results = []
                
                # Limit total number of records
                for i, record in enumerate(result):
                    if i >= result_limit:
                        print(f"Warning: Query returned more than {result_limit} records. Truncating results.")
                        break
                    
                    processed_record = {}
                    for key, value in record.items():
                        # Handle nodes - limit properties
                        if hasattr(value, 'labels') and hasattr(value, 'items'):  # It's a Neo4j Node
                            node_dict = dict(value.items())
                            if len(node_dict) > property_limit:
                                print(f"Warning: Node has {len(node_dict)} properties. Limiting to {property_limit} properties.")
                                # Keep important properties first
                                priority_props = ['subject_id', 'hadm_id', 'note_id', 'text', 'name', 'id']
                                kept_props = {}
                                
                                # First add priority properties
                                for prop in priority_props:
                                    if prop in node_dict:
                                        kept_props[prop] = node_dict[prop]
                                
                                # Then add others until limit
                                for prop, val in node_dict.items():
                                    if prop not in kept_props and len(kept_props) < property_limit:
                                        kept_props[prop] = val
                                
                                processed_record[key] = kept_props
                            else:
                                processed_record[key] = dict(value.items())
                        else:
                            processed_record[key] = value
                    
                    all_results.append(processed_record)
                
                print(f"Found {len(all_results)} results from database")
                return all_results
            except Exception as e:
                print(f"Error executing Cypher query: {e}")
                return []
    
    def refresh_schema(self) -> str:
        """Refresh the schema."""
        self.schema = self._get_schema()
        return self.schema
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()