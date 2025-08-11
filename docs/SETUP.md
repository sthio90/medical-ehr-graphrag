# Setup Guide for Medical GraphRAG

This guide walks through the complete setup process for Medical GraphRAG, from initial installation to running your first query.

## Prerequisites

Before starting, ensure you have:

- Python 3.8 or higher
- Neo4j Database 4.4 or higher (Community or Enterprise Edition)
- OpenAI API key
- At least 4GB of RAM for optimal performance

## Step 1: Neo4j Database Setup

### Option A: Local Installation

1. Download Neo4j from [neo4j.com/download](https://neo4j.com/download/)
2. Install and start Neo4j
3. Access Neo4j Browser at http://localhost:7474
4. Set initial password when prompted

### Option B: Neo4j AuraDB (Cloud)

1. Sign up at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/)
2. Create a new database
3. Save the connection URI and credentials

### Configure Database

Once Neo4j is running, you'll need to:

1. Create constraints and indexes (optional but recommended for performance)
2. Load your medical data following your graph schema

## Step 2: Project Setup

### Clone the Repository

```bash
git clone https://github.com/yourusername/medical-graphrag-public.git
cd medical-graphrag-public
```

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Configuration

### Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687  # Or your AuraDB URI
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j  # Usually 'neo4j' for default database

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Model Configuration
OPENAI_MODEL_NAME=gpt-4  # or gpt-3.5-turbo
EMBEDDING_MODEL_NAME=text-embedding-3-small
```

## Step 4: Data Preparation

### Graph Schema

Your Neo4j database should follow this schema:

```cypher
// Node types
(:Patient {subject_id: string, ...})
(:Admission {hadm_id: string, ...})
(:DischargeNote {note_id: string, full_text: string, ...})
(:RadiologyReport {note_id: string, full_text: string, ...})

// Relationships
(Patient)-[:HAS_ADMISSION]->(Admission)
(Admission)-[:HAS_NOTE]->(DischargeNote)
(Admission)-[:HAS_RADIOLOGY_REPORT]->(RadiologyReport)
```

### Creating Vector Embeddings

If your deployment includes vector search:

1. Ensure your notes have `full_text` properties
2. Run the embedding generation script (if provided)
3. Create vector indexes in Neo4j

Example vector index creation:
```cypher
CREATE VECTOR INDEX discharge_note_embeddings IF NOT EXISTS
FOR (n:DischargeNote)
ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

## Step 5: Running the Application

### Web Interface (Recommended)

```bash
streamlit run src/web_app.py
```

This will:
- Start the Streamlit server
- Open your browser to http://localhost:8501
- Display the Medical GraphRAG interface

### Command Line Interface

```bash
python src/app.py
```

## Step 6: Testing Your Setup

### Quick Test Queries

1. Start with simple queries:
   - "List all patients" (if no filter is set)
   - "What diagnoses are recorded?"

2. Test filtered queries:
   - Set a patient ID filter
   - Try: "What medications is the patient taking?"

3. Test note type filtering:
   - Select "Radiology Reports Only"
   - Try: "What imaging studies were performed?"

### Troubleshooting

**Connection Issues:**
- Verify Neo4j is running: `neo4j status`
- Check connection details in `.env`
- Test connection with Neo4j Browser

**OpenAI API Issues:**
- Verify API key is correct
- Check you have API credits
- Test with a simple OpenAI API call

**Import Errors:**
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version: `python --version`

## Step 7: Production Deployment

### Streamlit Cloud

1. Push your code to GitHub
2. Sign up at [streamlit.io](https://streamlit.io)
3. Connect your GitHub repository
4. Add secrets in Streamlit Cloud dashboard

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "src/web_app.py"]
```

### Security Best Practices

1. Never commit `.env` files
2. Use environment variables for all secrets
3. Implement authentication for production
4. Use HTTPS for web deployment
5. Regularly update dependencies

## Additional Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/)

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review error messages carefully
3. Check GitHub issues for similar problems
4. Create a new issue with detailed information