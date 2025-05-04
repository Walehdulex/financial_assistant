# FINANCIAL INVESTMENT ASSISTANT


## Overview

This project delivers an AI-driven personalized Financial Investment Assistant that combines advanced machine learning techniques to provide individual investors with personalized investment recommendations. The system helps investors make better decisions through portfolio management, risk analysis, and educational integration.

## Key Features

- **Portfolio Management**: Create, track, and analyze investment portfolios
- **Risk Assessment**: Dynamic risk modeling with intuitive visualizations
- **Performance Tracking**: Monitor investment performance with detailed metrics
- **Personalized Recommendations**: AI-driven investment suggestions tailored to individual preferences
- **Educational Integration**: Contextual learning resources to improve financial literacy

## Architecture
The system follows a service-oriented architecture built on Flask:

- **Frontend**: Bootstrap 5, Chart.js for data visualization
- **Backend**: Flask with Blueprint organization
- **Database**: SQLAlchemy ORM for data modeling
- **API Integration**: External financial data sources with multi-level caching

## Technology Stack
- **Backend** Framework: Flask
- **Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Data Visualization**: Chart.js
- **Financial Data**: Alpha Vantage API
- **Machine Learnin**g: scikit-learn, TensorFlow

### Installation
### Prerequisites
* Python 3.8+
* pip
* Virtual environment (recommended)

#### Setup
1. Clone the repository
`git clone https://campus.cs.le.ac.uk/gitlab/ug_project/24-25/aa1327.git`
* `cd aa1327`
2. Create and activate virtual environment
* `python -m venv venv`
* `source venv/bin/activate `
* On Windows: 
`venv\Scripts\activate`
3. Install dependencies
* `pip install -r requirements.txt`
4. Set up environment variables
* `cp .env.example .env`
* `Edit .env with your API keys and configuration`
5. Initialize the database
* `flask db init`
* `flask db migrate`
* `flask db upgrade`
6. Run the application
* `flask run`

## Project Structure
![img.png](img.png)

## Key Components

* **PortfolioService**: Manages portfolio creation and valuation
* **RiskService**: Executes risk assessment algorithms
* **PerformanceService**: Calculates investment performance metrics
* **RecommendationService**: Generates personalized investment recommendations
* **MLService**: Implements machine learning models for prediction
* **HistoryService**: Records and retrieves historical data
* **NewsService**: Retrieves market news affecting portfolios

## Security Features
* Secure password hashing with PBKDF2
* Role-based access control
* Input validation and CSRF protection
* Secure session management

## Testing
`pytest`

**Evaluation Results**

The system achieved positive evaluation results:
* System Usability Scale (SUS) score: 82/100
* High satisfaction ratings for educational integration (4.8/5)
* Efficient portfolio management (4.7/5)
* Strong performance tracking capabilities (4.6/5)

## Future Development
* Expand asset class coverage beyond stocks
* Implement additional machine learning models
* Enhance mobile experience
* Integrate with broader financial planning tools

## Academic Context

This project was developed as part of a dissertation research exploring how technology can bridge the gap between theoretical investment knowledge and practical application for individual investors.

## License

This project is licensed for academic use and demonstration purposes only.

## Acknowledgements
I would like to give my Acknowledgements to Dr. Savoye Yann for guidance and support throughout the development of this project.