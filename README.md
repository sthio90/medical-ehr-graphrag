# MediGRAF: A Hybrid Graph-RAG System for Natural Language Querying of Electronic Health Records

A hybrid Retrieval-Augmented Generation (RAG) system that combines graph database queries with vector similarity search to answer medical questions from Electronic Health Records (EHR) data.

## Overview

MediGRAF leverages the strengths of both structured graph queries and semantic vector search to provide accurate, context-aware responses to medical queries. The system uses Neo4j for graph storage and vector indexing, combined with OpenAI's language models for natural language understanding and generation.

## Key Features

- **Hybrid Search Architecture**: Combines Cypher graph queries with vector similarity search
- **Flexible Filtering**: Filter by patient ID and note type (discharge summaries, radiology reports)
- **Interactive Web Interface**: Streamlit-based UI for easy interaction
- **Debug Information**: View generated Cypher queries and data sources
- **Feedback System**: Built-in feedback collection for continuous improvement

## Architecture

The system consists of several core components:

- **Graph Database Layer**: Neo4j database storing patient records, medical notes, and their relationships
- **Vector Search**: Embeddings for discharge notes and radiology reports with similarity search
- **Query Pipeline**: LLM-powered Cypher query generation and answer synthesis
- **Web Interface**: User-friendly Streamlit application

## Prerequisites

- Python 3.8 or higher
- Neo4j database (4.4 or higher)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medical-graphrag-public.git
cd medical-graphrag-public
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

4. Configure your Neo4j database connection and OpenAI API key in the `.env` file.

## Usage

### Web Application

Run the Streamlit web interface:
```bash
streamlit run src/web_app.py
```

The web interface provides:
- Patient ID filtering (optional)
- Note type selection (all notes, discharge only, radiology only)
- Example queries to get started
- Advanced settings for fine-tuning search parameters

### Command Line Interface

Run queries from the command line:
```bash
python src/app.py
```

## Configuration

Create a `.env` file with the following variables:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=your_openai_api_key
```

## Query Examples

- "What imaging studies were performed for this patient?"
- "Summarize the patient's discharge information"
- "List the patient's current medications"
- "What were the findings from the chest X-ray?"
- "What is the patient's diagnosis?"

## Development

### Project Structure
```
medical-graphrag-public/
├── src/
│   ├── app.py           # CLI interface
│   ├── web_app.py       # Streamlit web interface
│   ├── chain.py         # Core query pipeline
│   ├── graph.py         # Graph database operations
│   ├── vector_search.py # Vector similarity search
│   └── config.py        # Configuration management
├── examples/            # Example queries and configurations
└── docs/               # Additional documentation
```

### Extending the System

The modular architecture allows for easy extension:
- Add new node types in the graph schema
- Implement additional vector search strategies
- Customize the LLM prompts for specific use cases
- Add new UI features in the Streamlit interface

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

This project was developed as part of a Master's dissertation on improving medical information retrieval using graph-based and vector search techniques.
