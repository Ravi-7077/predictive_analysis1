# Power Consumption Digital Twin

A machine learning-powered digital twin system for predicting power consumption using XGBoost models and weather data. The project includes both a Flask REST API backend and a Streamlit web interface for real-time predictions and monitoring.

## 📋 Overview

This project builds a predictive model for power consumption that combines:
- **Historical demand patterns** (lagged power values, temporal features)
- **Weather data** (temperature, humidity, wind speed/direction)
- **XGBoost modeling** for accurate predictions
- **Hybrid forecasting** combining baseline and weather-adjusted predictions

The system provides both programmatic API access and an interactive web dashboard for monitoring and analysis.

## 🎯 Features

- **Predictive Analytics**: Dual-mode predictions (baseline + hybrid with weather adjustments)
- **REST API**: Flask-based API for predictions (`/predict` endpoint)
- **Web Dashboard**: Streamlit interface with real-time visualization and dark theme
- **Digital Twin Simulation**: HTML-based simulation interface
- **Weather Integration**: Accounts for temperature, humidity, and wind patterns
- **Containerized**: Docker support for easy deployment

## 🏗️ Project Structure

```
.
├── streamlit_app.py           # Interactive web dashboard
├── model_server.py            # Flask API server
├── hybrid_model.pkl           # Trained XGBoost model
├── digtwin.html               # Digital twin simulation interface
├── PowerConsumptionpred.ipynb  # Model training notebook
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker (optional, for containerization)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd predproj
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 📦 Dependencies

The project uses the following Python packages:

- **Flask**: Web API framework
- **XGBoost**: Machine learning model
- **Streamlit**: Web dashboard framework
- **Plotly**: Data visualization
- **Pandas/NumPy**: Data processing
- **Joblib**: Model serialization
- **Gunicorn**: Production WSGI server (for Docker)

See `requirements.txt` for complete list.

## 🔧 Usage

### Option 1: Flask API Server

Run the Flask server for REST API access:

```bash
python model_server.py
```

The server starts on `http://localhost:5000`

**Available Endpoints:**

- **GET `/`** - Serves the digital twin HTML interface
- **POST `/predict`** - Get power consumption predictions

**Prediction Request Example:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "power_lag_1": 150.5,
    "power_lag_24": 145.2,
    "hour": 14,
    "dayofweek": 3,
    "month": 6,
    "temperature_2m": 28.5,
    "relative_humidity_2m": 65,
    "wind_speed_10m": 8.3,
    "wind_direction_10m": 180
  }'
```

**Response:**
```json
{
  "baselinePred": 365.2,
  "hybridPred": 372.8,
  "total": 140.4
}
```

### Option 2: Streamlit Dashboard

Start the interactive web dashboard:

```bash
streamlit run streamlit_app.py
```

The dashboard opens in your browser at `http://localhost:8501`

**Features:**
- Real-time power predictions
- Interactive visualizations with Plotly
- Dark-themed modern UI
- Historical data analysis
- Weather impact visualization

### Option 3: Docker

Build and run the application in a container:

```bash
# Build the Docker image
docker build -t power-consumption-twin .

# Run the container
docker run -p 5000:5000 power-consumption-twin
```

Access the API at `http://localhost:5000` and the HTML interface at `/`

## 🔄 Model Details

### Features Used

The model takes the following inputs:

| Feature | Type | Description |
|---------|------|-------------|
| `power_lag_1` | Numeric | Power consumption 1 hour ago |
| `power_lag_24` | Numeric | Power consumption 24 hours ago |
| `hour` | Numeric | Hour of day (0-23) |
| `dayofweek` | Numeric | Day of week (0-6) |
| `month` | Numeric | Month of year (1-12) |
| `temperature_2m` | Numeric | Air temperature (°C) |
| `relative_humidity_2m` | Numeric | Relative humidity (%) |
| `wind_speed_10m` | Numeric | Wind speed (m/s) |
| `wind_direction_10m` | Numeric | Wind direction (degrees) |

### Prediction Modes

1. **Baseline Prediction**: Linear combination of historical and temporal features
2. **Hybrid Prediction**: Baseline + weather-adjusted component accounting for:
   - Temperature deviation from comfort range (20-28°C)
   - Humidity impact (above 55%)
   - Wind speed effects
   - Wind direction (facing vs. non-facing)

## 📚 Model Training

To retrain the model with your own data:

1. Open `PowerConsumptionpred.ipynb` in Jupyter
2. Prepare your dataset with required features
3. Train the XGBoost model
4. Save the model using joblib:
   ```python
   import joblib
   joblib.dump(model, 'hybrid_model.pkl')
   ```

## 🌐 API Integration

The API is designed for easy integration with third-party systems:

```python
import requests

payload = {
    "power_lag_1": 150.5,
    "power_lag_24": 145.2,
    "hour": 14,
    "dayofweek": 3,
    "month": 6,
    "temperature_2m": 28.5,
    "relative_humidity_2m": 65,
    "wind_speed_10m": 8.3,
    "wind_direction_10m": 180
}

response = requests.post('http://localhost:5000/predict', json=payload)
predictions = response.json()
print(f"Hybrid Prediction: {predictions['hybridPred']} kW")
```

## 🎨 Dashboard Features

- **Responsive Design**: Modern dark-themed interface
- **Real-time Charts**: Interactive Plotly visualizations
- **Metric Cards**: Key performance indicators display
- **Parameter Adjustment**: Live prediction updates
- **Historical Analysis**: Trend visualization

## 🐳 Deployment

### Production Deployment

For production environments, use Gunicorn:

```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 model_server:app
```

### Environment Variables

Configure the following as needed:
- `FLASK_ENV`: Set to `production` for production deployment
- `PORT`: Server port (default: 5000)

## 🔗 Interfaces

### Web Interfaces

1. **Streamlit Dashboard** (`streamlit_app.py`)
   - Interactive predictions
   - Data visualization
   - Parameter exploration

2. **HTML Digital Twin** (`digtwin.html`)
   - Served at `/` via Flask
   - Browser-based simulation
   - Real-time updates

3. **REST API** (Flask)
   - Programmatic access
   - JSON request/response
   - Easy integration

## 📊 Data Format

All numeric inputs are floats. The model expects:
- Powers in kW
- Temperature in Celsius
- Humidity as percentage (0-100)
- Wind speed in m/s
- Wind direction in degrees (0-360)

## ⚠️ Important Notes

- Ensure `hybrid_model.pkl` is present for optimal predictions
- If model file is missing, the API falls back to baseline formula
- Weather data should be from a reliable source (e.g., Open-Meteo API)
- Model performance depends on training data quality

## 🛠️ Troubleshooting

**Model not loading?**
- Check that `hybrid_model.pkl` exists in the project root
- Verify file permissions
- Check for joblib version compatibility

**API not responding?**
- Ensure Flask is installed: `pip install flask`
- Check port 5000 is not in use
- Review Flask logs for errors

**Streamlit dashboard slow?**
- Check system resources
- Reduce number of chart updates
- Consider caching predictions

## 📝 License

[Add your license here]

## 👥 Contributing

[Add contribution guidelines here]

## 📧 Contact

[Add contact information here]

## 🔄 Version History

- **v1.0.0** - Initial release with XGBoost model and dual interfaces

---

**Last Updated**: April 2026
