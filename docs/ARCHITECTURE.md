# Medical GraphRAG Architecture

## System Overview

Medical GraphRAG implements a hybrid retrieval system that combines the precision of graph database queries with the semantic understanding of vector search. This architecture enables comprehensive and accurate retrieval of medical information from electronic health records.

## Core Components

### 1. Data Storage Layer

#### Neo4j Graph Database
- **Purpose**: Stores structured medical data and relationships
- **Schema**:
  - **Nodes**: Patients, Admissions, Discharge Notes, Radiology Reports
  - **Relationships**: HAS_ADMISSION, HAS_NOTE, HAS_RADIOLOGY_REPORT
  - **Properties**: Patient demographics, admission details, note content, timestamps

#### Vector Indexes
- **Discharge Note Embeddings**: Semantic representations of discharge summaries
- **Radiology Report Embeddings**: Vectorized radiology findings
- **Embedding Model**: OpenAI text-embedding-3-small (configurable)

### 2. Query Processing Pipeline

The system processes queries through multiple stages:

1. **Natural Language Understanding**
   - User query → LLM analysis
   - Intent recognition and entity extraction
   - Context preservation (patient ID, note type filters)

2. **Cypher Query Generation**
   - LLM generates Neo4j Cypher queries based on user intent
   - Dynamic query construction with filters
   - Safety constraints to prevent unbounded queries

3. **Graph Database Retrieval**
   - Execute generated Cypher query
   - Retrieve structured data from Neo4j
   - Apply result limits for performance

4. **Vector Similarity Search** (Optional)
   - Generate query embedding
   - Search similar documents in vector indexes
   - Filter by patient ID and note type
   - Retrieve top-k most similar documents

5. **Result Synthesis**
   - Combine graph and vector search results
   - LLM synthesizes final answer
   - Include source attribution

### 3. Application Layer

#### Web Interface (Streamlit)
- Patient filtering controls
- Note type selection
- Query input and submission
- Results display with source viewing
- Debug information panel
- Feedback collection

#### CLI Interface
- Command-line query execution
- Batch processing support
- Direct API access

## Data Flow

```
User Query
    ↓
Context Setting (Patient ID, Note Type)
    ↓
LLM Query Analysis
    ↓
    ├── Cypher Query Generation
    │       ↓
    │   Graph Database Query
    │       ↓
    │   Structured Results
    │
    └── Vector Embedding Generation
            ↓
        Similarity Search
            ↓
        Similar Documents
            ↓
    Result Combination
            ↓
    LLM Answer Synthesis
            ↓
    Final Response with Sources
```

## Key Design Decisions

### 1. Hybrid Retrieval Strategy
- **Rationale**: Combines structured query precision with semantic understanding
- **Benefits**: 
  - Accurate factual retrieval via graph queries
  - Context-aware retrieval via vector search
  - Redundancy for improved recall

### 2. Modular Architecture
- **Rationale**: Separation of concerns for maintainability
- **Benefits**:
  - Easy to extend individual components
  - Clear interfaces between modules
  - Flexible deployment options

### 3. Context Preservation
- **Rationale**: Medical queries often require patient-specific context
- **Implementation**: Session state management for filters
- **Benefits**: Consistent results within a session

### 4. Configurable Search Parameters
- **Vector Limit**: Number of similar documents to retrieve
- **Character Limit**: Maximum text per document
- **Cypher Limit**: Maximum graph query results
- **Benefits**: Performance tuning for different use cases

## Security Considerations

1. **Input Validation**: All user inputs are validated before processing
2. **Query Constraints**: Cypher queries include LIMIT clauses
3. **Environment Variables**: Sensitive configuration stored securely
4. **No Direct Query Execution**: Users cannot execute arbitrary Cypher

## Performance Optimizations

1. **Vector Index Configuration**: Optimized similarity search algorithms
2. **Query Result Caching**: Session-based result storage
3. **Batch Processing**: Efficient embedding generation
4. **Connection Pooling**: Reused database connections

## Extensibility

The architecture supports several extension points:

1. **Additional Node Types**: Easy to add new medical record types
2. **Alternative Embedding Models**: Pluggable embedding generation
3. **Custom Query Templates**: Domain-specific query patterns
4. **New UI Features**: Modular Streamlit components
5. **Additional Search Strategies**: Pluggable retrieval methods

## Deployment Considerations

1. **Scalability**: Horizontal scaling of web interface
2. **Database**: Neo4j cluster for high availability
3. **API Keys**: Secure management via environment variables
4. **Monitoring**: Query performance and usage tracking
5. **Backup**: Regular database and configuration backups