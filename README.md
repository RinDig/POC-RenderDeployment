# VigilOre Compliance API

An AI-powered multi-agent system for automated compliance analysis that compares audit documents against regulatory frameworks and generates comprehensive compliance reports.

## 🚀 Overview

VigilOre uses advanced AI agents to:
- Parse audit documents (PDFs, Word docs, text files)
- Extract requirements from regulatory frameworks
- Compare findings against multiple compliance standards
- Generate detailed reports with scores, gaps, and recommendations
- Calculate potential financial penalties for non-compliance

## 🌟 Features

- **Multi-Framework Analysis**: Compare against multiple regulatory frameworks simultaneously
- **Intelligent Document Processing**: Supports PDF, DOCX, TXT, and MP3 formats
- **Automated Compliance Scoring**: Get objective compliance scores for each requirement
- **Financial Risk Assessment**: Calculate potential penalties based on framework violations
- **Export Options**: Generate reports in JSON and Excel formats
- **RESTful API**: Easy integration with any frontend application
- **Async Processing**: Handle large documents without timeouts

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **AI/LLM**: OpenAI GPT-4
- **Document Processing**: PyPDF2, python-docx, pandas
- **Deployment**: Render.com (easily portable to AWS/Azure)
- **Architecture**: Multi-agent system with specialized AI agents

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Git

## 🔧 Installation

1. **Clone the repository**
```bash
git clone https://github.com/RinDig/POC-RenderDeployment.git
cd vigilore-api
```

2. **Install dependencies**
```bash
pip install -r requirements-api.txt
```

3. **Set environment variables**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## 🚀 Running Locally

```bash
# Development mode with auto-reload
uvicorn api_v2:app --reload --host localhost --port 9999

# Production mode
uvicorn api_v2:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:9999`

## 📚 API Documentation

Once running, visit `http://localhost:9999/docs` for interactive API documentation.

### Key Endpoints

#### Submit Audit
```http
POST /audits
Content-Type: multipart/form-data

Required fields:
- input_file: Audit document (PDF/DOCX/TXT)
- framework_files[]: Regulatory framework documents
- site_name: Mine site name
- operator: Operator code
- auditor_name: Auditor's name
- auditor_email: Auditor's email
```

#### Check Status
```http
GET /audits/status/{job_id}
```

#### Get Results
```http
GET /reports/{report_id}        # JSON report
GET /reports/{report_id}/excel  # Excel download
```

#### Dashboard Data
```http
GET /dashboard/summary  # Aggregated compliance data
GET /reports           # List all reports
```

## 🏗️ Architecture

The system uses a multi-agent architecture:

```
┌─────────────────┐
│   Orchestrator  │ - Coordinates all agents
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌───▼────┐
│ Input │ │Frame │ │Comparator│ │Aggregator│
│Parser │ │Loader│ │ Agent    │ │  Agent   │
└───────┘ └──────┘ └─────────┘ └─────────┘
```

- **Input Parser**: Extracts compliance statements from audit documents
- **Framework Loader**: Loads and categorizes regulatory requirements
- **Comparator**: Compares audit findings against framework requirements
- **Aggregator**: Consolidates results and generates final reports

## 🚢 Deployment

### Deploy to Render

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
5. Deploy!

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 access | Yes |
| `PORT` | Port number (automatically set by Render) | No |

## 📊 Example Output

The system generates comprehensive compliance reports including:

- **Overall Compliance Score**: Percentage-based score across all frameworks
- **Framework-Specific Scores**: Individual scores for each regulatory framework
- **Gap Analysis**: Identified compliance gaps with specific recommendations
- **Financial Risk**: Potential penalties for non-compliance (where applicable)
- **Executive Summary**: AI-generated summary of key findings

## 🔒 Security Considerations

For production deployment:

1. **Add Authentication**: Implement API key or JWT-based authentication
2. **Secure Storage**: Use cloud storage (S3/Azure Blob) for persistent file storage
3. **HTTPS Only**: Ensure all communications are encrypted
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Data Encryption**: Encrypt sensitive compliance data at rest

## 🧪 Testing

Run the test script to verify your setup:

```bash
python test_api.py
```

This will test:
- API connectivity
- OpenAI key validity
- CORS configuration
- Endpoint availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary and confidential. All rights reserved.

## 📞 Support

For questions or support, please contact the development team.

---

**Note**: This is a proof-of-concept deployment. For production use, additional security measures and infrastructure considerations are required.