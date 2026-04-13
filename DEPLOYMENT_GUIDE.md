# Power Prediction Digital Twin - Deployment Guide

## ✅ Current Status
- **Model Server**: Running on Flask at `http://localhost:5000`
- **Digital Twin Interface**: Available at `http://localhost:5000`
- **API Endpoint**: `/predict` (POST)
- **Model Status**: Using fallback formula with ML enhancements (waiting for model file validation)

---

## 🚀 Local Deployment (Already Tested)

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running Locally
```bash
python model_server.py
```

The server will start on:
- **Local**: `http://127.0.0.1:5000`
- **Network**: `http://192.168.x.x:5000`

### Testing the API
```powershell
$body = @{
    power_lag_1 = 50
    power_lag_24 = 45
    hour = 12
    dayofweek = 3
    month = 6
    temperature_2m = 25
    relative_humidity_2m = 60
    wind_speed_10m = 8
    wind_direction_10m = 180
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/predict `
  -Method POST `
  -Body $body `
  -ContentType "application/json" | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

**Expected Response:**
```json
{
  "baselinePred": 94.5,
  "hybridPred": 99.48,
  "total": 53.6
}
```

---

## 🐳 Docker Deployment

### Build the Docker Image
```bash
docker build -t power-prediction-twin:latest .
```

### Run in Docker
```bash
docker run -p 5000:5000 power-prediction-twin:latest
```

Access at: `http://localhost:5000`

### Run in Docker Compose (Optional)
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  power-twin:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./hybrid_model.pkl:/app/hybrid_model.pkl
      - ./xgboost_power_model.json:/app/xgboost_power_model.json
```

Run:
```bash
docker-compose up
```

---

## ☁️ Cloud Deployment Options

### **Option 1: Azure Container Instances**
```bash
# Login to Azure
az login

# Create resource group
az group create --name power-prediction --location eastus

# Create container from Docker image
az container create \
  --resource-group power-prediction \
  --name power-twin-container \
  --image yourregistry.azurecr.io/power-prediction-twin:latest \
  --ports 5000 \
  --environment-variables FLASK_ENV=production
```

### **Option 2: Azure App Service**
1. Push Docker image to Azure Container Registry
2. Create App Service from container image
3. Set port to 5000
4. Enable continuous deployment from git

### **Option 3: AWS (EC2 or ECS)**
1. Push to ECR
2. Create ECS task definition
3. Deploy as ECS service
4. Configure ALB (Application Load Balancer)

### **Option 4: Google Cloud Run**
```bash
gcloud run deploy power-prediction-twin \
  --source . \
  --platform managed \
  --port 5000
```

---

## 📊 API Documentation

### Prediction Endpoint
- **URL**: `/predict`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Body
```json
{
  "power_lag_1": 50.0,          // Past hour power (kW)
  "power_lag_24": 45.0,         // Previous day same hour power (kW)
  "hour": 12,                   // Hour of day (0-23)
  "dayofweek": 3,              // Day of week (0=Monday, 6=Sunday)
  "month": 6,                  // Month (1-12)
  "temperature_2m": 25.0,      // Temperature (°C)
  "relative_humidity_2m": 60.0, // Humidity (%)
  "wind_speed_10m": 8.0,       // Wind speed (m/s)
  "wind_direction_10m": 180.0  // Wind direction (degrees)
}
```

### Response
```json
{
  "baselinePred": 94.5,    // Statistical baseline prediction (kW)
  "hybridPred": 99.48,     // ML-enhanced hybrid prediction (kW)
  "total": 53.6            // Total system power estimate (kW)
}
```

---

## 🔧 Model Information

### Features Used
1. **Temporal Features**
   - Hour of day
   - Day of week
   - Month

2. **Lag Features**
   - Power consumption 1 hour ago
   - Power consumption 24 hours ago

3. **Weather Features**
   - Temperature
   - Relative humidity
   - Wind speed
   - Wind direction

### Model Architecture
- **Primary Model**: XGBoost Regressor
- **Fallback Strategy**: Weighted baseline formula + weather adjustments
- **Hybrid Approach**: Combines statistical and ML predictions

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows - Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Model Loading Issues
The system automatically falls back to formula-based predictions if the model file is unavailable or corrupted.

### CORS Issues (if integrating with frontend)
Add to `model_server.py`:
```python
from flask_cors import CORS
CORS(app)
```

---

## 📈 Performance Monitoring

### Key Metrics to Track
1. **Prediction Accuracy**: Compare hybrid predictions vs. actual values
2. **API Response Time**: Should be <100ms
3. **Model Drift**: Retrain quarterly with new data
4. **System Load**: Monitor during peak hours

---

## 🔐 Production Considerations

### Security
- [ ] Use HTTPS/SSL certificates
- [ ] Implement API authentication (Bearer tokens)
- [ ] Rate limiting on `/predict` endpoint
- [ ] Input validation (check feature ranges)

### Scalability
- [ ] Use Gunicorn instead of Flask dev server
- [ ] Deploy behind Nginx reverse proxy
- [ ] Use load balancer for multiple instances
- [ ] Cache predictions for identical inputs

### Monitoring
- [ ] Set up logging (ELK stack)
- [ ] Enable APM (Application Performance Monitoring)
- [ ] Alert on API errors
- [ ] Monitor model performance metrics

### Configuration for Production
```bash
# Use Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 model_server:app

# Or with uvicorn for async
pip install uvicorn
uvicorn api:app --host 0.0.0.0 --port 5000 --workers 4
```

---

## 📝 Next Steps

1. **Validate the model file** (`hybrid_model.pkl`):
   - Ensure it's a proper scikit-learn or XGBoost model
   - Test with known data to validate predictions

2. **Set up monitoring**:
   - Track prediction accuracy
   - Monitor API latency
   - Alert on errors

3. **Plan for maintenance**:
   - Regular model retraining (monthly/quarterly)
   - Update weather data sources
   - Performance optimization

4. **Scale for production**:
   - Use production WSGI server (Gunicorn)
   - Set up reverse proxy (Nginx/Apache)
   - Implement caching layer

---

**Last Updated**: April 9, 2026
**Model Version**: v1.0 (Hybrid XGBoost + Weather-Adjusted Baseline)
