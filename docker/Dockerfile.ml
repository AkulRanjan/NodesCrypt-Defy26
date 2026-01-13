FROM python:3.10-slim

WORKDIR /app

# Install ML dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    joblib \
    numpy \
    xgboost \
    scikit-learn

# Copy ML models and service
COPY ml/ /app/ml/
COPY ml-service/ /app/ml-service/

EXPOSE 8002

CMD ["uvicorn", "ml-service.app:app", "--host", "0.0.0.0", "--port", "8002"]
