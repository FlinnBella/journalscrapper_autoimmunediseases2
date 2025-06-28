# Autoimmune Disease Journal Scraper

A comprehensive Python tool for scraping research papers on autoimmune diseases from multiple academic journals and databases.

## 🎯 Target Diseases
- Crohn's Disease
- Systemic Lupus Erythematosus
- Multiple Sclerosis
- Type 1 Diabetes
- Rheumatoid Arthritis

## 📚 Data Sources
- **PubMed** (NCBI Entrez API)
- **Europe PMC** (REST API)
- **OpenAlex** (API)
- **Core.ac.uk** (API)
- **bioRxiv & medRxiv** (API)
- **Springer Nature** (API)

## 🔧 Prerequisites

### Python Version
This project requires **Python 3.9 or higher**. You can check your Python version with:
```bash
python --version
```

If you need to install Python, download it from [python.org](https://www.python.org/downloads/).

### Why Use a Virtual Environment?
A virtual environment is an isolated Python environment that keeps your project dependencies separate from your system Python installation. This prevents:
- **Dependency conflicts** between different projects
- **System-wide package pollution** that could break other applications
- **Version compatibility issues** when working on multiple projects
- **Cluttering your system** with hundreds of packages permanently

Think of it as a "sandbox" for your project that keeps everything clean and organized.

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd journalscrapper_autoimmunediseases
```

### 2. Create a Virtual Environment

#### On Windows:
```powershell
# Create virtual environment
python -m venv autoimmune_scraper_env

# Activate virtual environment
.\autoimmune_scraper_env\Scripts\Activate.ps1
```

#### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv autoimmune_scraper_env

# Activate virtual environment
source autoimmune_scraper_env/bin/activate
```

**Note**: You'll need to activate the virtual environment every time you work on this project. Your terminal prompt should show `(autoimmune_scraper_env)` when the environment is active.

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the example environment file and configure your API keys:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys (some sources may require registration):
```
SPRINGER_API_KEY=your_springer_api_key_here
CORE_API_KEY=your_core_api_key_here
# Add other API keys as needed
```

## 📖 Usage

### Basic Usage
```python
from src.main import AutoimmuneScraper

# Initialize scraper
scraper = AutoimmuneScraper()

# Scrape all sources for all diseases
results = scraper.scrape_all()

# Scrape specific disease from specific sources
results = scraper.scrape_disease(
    disease="crohns", 
    sources=["pubmed", "europe_pmc"]
)
```

### Command Line Interface
```bash
# Scrape all diseases from all sources
python -m src.main

# Scrape specific disease
python -m src.main --disease crohns

# Scrape from specific sources
python -m src.main --sources pubmed,europe_pmc

# Export results to different formats
python -m src.main --output-format json
python -m src.main --output-format csv
```

## 📁 Project Structure
```
journalscrapper_autoimmunediseases/
├── src/
│   ├── scrapers/           # Individual scraper modules
│   ├── models/            # Data models and schemas
│   ├── utils/             # Utility functions
│   ├── config/            # Configuration files
│   └── main.py           # Main orchestrator
├── tests/                # Unit tests
├── data/                 # Output data directory
├── logs/                 # Log files
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Deactivating Virtual Environment
When you're done working on the project:
```bash
deactivate
```

## 📊 Output Formats
- **JSON**: Structured data for programmatic use
- **CSV**: Spreadsheet-compatible format
- **XML**: Standard academic format
- **BibTeX**: Citation format for reference managers

## ⚠️ Rate Limiting & Ethics
This scraper implements responsible rate limiting and follows each platform's robots.txt and API terms of service. Please use responsibly and consider the load on academic servers.

## 📄 License
[Add your license here]

## 🤝 Contributing
[Add contribution guidelines here]

## 📞 Support
[Add support information here] 