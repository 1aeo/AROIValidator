# AROI Validator

A web-based validation tool for evaluating AI responses using the Accuracy, Relevance, Objectivity, and Informativeness (AROI) framework.

## Features

- **Web Interface**: User-friendly Streamlit application for validating AI responses
- **Command Line Tool**: CLI interface for batch processing and automation
- **Comprehensive Validation**: Evaluates responses across multiple quality dimensions
- **Automated Scoring**: Calculates weighted scores based on AROI criteria
- **Result Tracking**: Saves validation results with timestamps for analysis

## How to Use

### Web Application

Run the Streamlit web interface:
```bash
./run.sh
```
Or directly:
```bash
streamlit run app.py --server.port 5000
```

The web interface provides:
- Text input for questions and AI responses
- Real-time validation with detailed scoring
- Visual feedback on response quality
- History of recent validations

### Command Line Interface

Use the CLI for batch validation:
```bash
python aroi_cli.py "Your question" "AI response to validate"
```

The CLI will output:
- Individual scores for each AROI dimension
- Overall weighted score
- Quality assessment and recommendations

## Validation Metrics

The AROI framework evaluates responses on:

1. **Accuracy** (30% weight) - Correctness and factual accuracy
2. **Relevance** (30% weight) - How well the response addresses the question
3. **Objectivity** (20% weight) - Neutral tone and balanced perspective
4. **Informativeness** (20% weight) - Depth and completeness of information

## Output

Validation results are saved to `validation_results/` directory as JSON files containing:
- Question and response text
- Individual dimension scores
- Overall weighted score
- Detailed feedback
- Timestamp

## Requirements

- Python 3.x
- Streamlit
- Pandas
- Requests

All dependencies are managed automatically through the project configuration.