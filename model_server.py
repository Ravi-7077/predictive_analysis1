import json
import os
from pathlib import Path

from flask import Flask, request, jsonify, send_file
import numpy as np
import xgboost as xgb

app = Flask(__name__)

MODEL_PATH = Path('hybrid_model.pkl')

# You should save your trained model from the notebook as hybrid_model.pkl
# e.g.:
# import joblib
# joblib.dump(model_hybrid, 'hybrid_model.pkl')

model = None
if MODEL_PATH.exists():
    import joblib
    model = joblib.load(MODEL_PATH)
    print(f'Loaded model from {MODEL_PATH}')
else:
    print('Warning: hybrid_model.pkl not found. API will use fallback formula.')

@app.route('/')
def index():
    return send_file('digtwin.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    required = ['power_lag_1', 'power_lag_24', 'hour', 'dayofweek', 'month', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields', 'required': required}), 400

    features = np.array([[
        float(data['power_lag_1']),
        float(data['power_lag_24']),
        float(data['hour']),
        float(data['dayofweek']),
        float(data['month']),
        float(data['temperature_2m']),
        float(data['relative_humidity_2m']),
        float(data['wind_speed_10m']),
        float(data['wind_direction_10m'])
    ]])

    if model is not None:
        pred = model.predict(features)
        hybrid_pred = float(pred[0])
        baseline_pred = float(0.52*data['power_lag_1'] + 0.27*data['power_lag_24'] + 1.8*data['hour'] + 4.5*data['dayofweek'] + 2.1*data['month'] + 0.13*data['temperature_2m'] + 0.09*data['relative_humidity_2m'])
    else:
        # fallback formula from HTML twin simulation
        dayofweek = data['dayofweek']
        baseline_pred = 0.52*data['power_lag_1'] + 0.27*data['power_lag_24'] + 1.8*data['hour'] + 4.5*dayofweek + 2.1*data['month'] + 0.13*data['temperature_2m'] + 0.09*data['relative_humidity_2m']
        weather_adjust = (
            (data['temperature_2m'] - 28) * 2.3 if data['temperature_2m'] > 28 else (20 - data['temperature_2m']) * 1.8 if data['temperature_2m'] < 20 else 0
        ) + max(0, (data['relative_humidity_2m'] - 55) * 1.4) + max(0, (data['wind_speed_10m'] - 10) * 0.4)
        face = abs((data['wind_direction_10m'] + 180) % 360 - 180) < 45
        weather_adjust += 4 if face else -1
        hybrid_pred = baseline_pred + weather_adjust * 0.83

    return jsonify({
        'baselinePred': float(baseline_pred),
        'hybridPred': float(hybrid_pred),
        'total': float(data['power_lag_1'] * 0.9 + data['power_lag_24'] * 0.08 + 5)  # approximate
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
