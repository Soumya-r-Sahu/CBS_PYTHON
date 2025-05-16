"""
Predictive Models Module

This module implements machine learning models for predictive analytics
in the banking system.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import json
import pickle
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

# Import Analytics modules using relative import
try:
    from ..config import MODEL_SETTINGS
except (ImportError, ValueError):
    # Fallback if relative import fails
    try:
        from analytics_bi.config import MODEL_SETTINGS
    except ImportError:
        # Default settings if import fails
        MODEL_SETTINGS = {
            'model_path': './models',
            'training_data_path': './data',
            'validation_split_ratio': 0.2
        }
        # Set up logging if not already set
        if 'logger' not in globals():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logger = logging.getLogger('analytics-predictive-models')
        logger.warning("Could not import MODEL_SETTINGS. Using default values.")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('analytics-predictive-models')

class ModelManager:
    """Manager for predictive models in the banking system"""
    
    def __init__(self):
        """Initialize the model manager"""
        self.models = {}
        self.model_metadata = {}
        self._load_models()
        
        # Create model directories if they don't exist
        for path in [MODEL_SETTINGS['model_path'], 
                   MODEL_SETTINGS['training_data_path']]:
            os.makedirs(path, exist_ok=True)
    
    def _load_models(self):
        """Load trained models from the model directory"""
        try:
            model_dir = Path(MODEL_SETTINGS['model_path'])
            
            if not model_dir.exists():
                model_dir.mkdir(parents=True)
                logger.info(f"Created models directory: {model_dir}")
                return
            
            # Load model metadata first
            metadata_file = model_dir / "model_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.model_metadata = json.load(f)
                    logger.info(f"Loaded metadata for {len(self.model_metadata)} models")
            
            # Load each model file
            for model_id, metadata in self.model_metadata.items():
                model_file = model_dir / f"{model_id}.pkl"
                if model_file.exists():
                    try:
                        with open(model_file, 'rb') as f:
                            self.models[model_id] = pickle.load(f)
                            logger.info(f"Loaded model: {model_id}")
                    except Exception as e:
                        logger.error(f"Error loading model {model_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def save_model(self, model_id: str, model: Any, metadata: Dict[str, Any]) -> bool:
        """
        Save a trained model
        
        Args:
            model_id: Model identifier
            model: Trained model object
            metadata: Model metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            model_dir = Path(MODEL_SETTINGS['model_path'])
            model_file = model_dir / f"{model_id}.pkl"
            
            # Save the model
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            
            # Update and save metadata
            metadata['last_updated'] = datetime.datetime.now().isoformat()
            self.model_metadata[model_id] = metadata
            self.models[model_id] = model
            
            # Save metadata file
            metadata_file = model_dir / "model_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
            
            logger.info(f"Saved model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model {model_id}: {e}")
            return False
    
    def predict(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions using a trained model
        
        Args:
            model_id: Model identifier
            data: Input data for prediction
            
        Returns:
            Prediction results
        """
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not found")
                return {"error": f"Model {model_id} not found"}
            
            model = self.models[model_id]
            metadata = self.model_metadata[model_id]
            model_type = metadata.get('type', 'unknown')
            
            # Process input data based on model type
            processed_data = self._preprocess_data(data, metadata)
            
            # Make prediction
            if model_type == 'sklearn':
                prediction = model.predict(processed_data)
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(processed_data)
                else:
                    probabilities = None
                
                return self._format_prediction_result(prediction, probabilities, metadata)
                
            elif model_type == 'keras':
                prediction = model.predict(processed_data)
                return self._format_prediction_result(prediction, None, metadata)
                
            else:
                return {"error": f"Unsupported model type: {model_type}"}
            
        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {e}")
            return {"error": f"Prediction error: {str(e)}"}
    
    def _preprocess_data(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """
        Preprocess input data for a model
        
        Args:
            data: Raw input data
            metadata: Model metadata
            
        Returns:
            Preprocessed data
        """
        # Get feature information from metadata
        features = metadata.get('features', [])
        
        # For sklearn models, convert to numpy array in correct order
        if metadata.get('type') == 'sklearn':
            # Create a feature vector in the correct order
            feature_values = []
            
            for feature in features:
                feature_name = feature.get('name')
                
                if feature_name in data:
                    value = data[feature_name]
                    
                    # Apply any preprocessing specified in metadata
                    if 'preprocessing' in feature:
                        if feature['preprocessing'] == 'one_hot':
                            # Implement one-hot encoding
                            categories = feature.get('categories', [])
                            one_hot = [1 if value == cat else 0 for cat in categories]
                            feature_values.extend(one_hot)
                        elif feature['preprocessing'] == 'normalize':
                            # Apply min-max normalization
                            min_val = feature.get('min', 0)
                            max_val = feature.get('max', 1)
                            if max_val > min_val:
                                norm_value = (value - min_val) / (max_val - min_val)
                                feature_values.append(norm_value)
                            else:
                                feature_values.append(value)
                        else:
                            feature_values.append(value)
                    else:
                        feature_values.append(value)
                else:
                    # Use default or 0 if feature is missing
                    feature_values.append(feature.get('default', 0))
            
            return np.array([feature_values])
            
        # For keras models, might need different preprocessing
        elif metadata.get('type') == 'keras':
            # Similar processing, but might return different shape
            return np.array([data])
        
        # Default: just return the data as is
        return data
    
    def _format_prediction_result(self, prediction: Any, 
                                probabilities: Any, 
                                metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format prediction results
        
        Args:
            prediction: Model prediction
            probabilities: Prediction probabilities (if available)
            metadata: Model metadata
            
        Returns:
            Formatted prediction results
        """
        result = {
            "prediction": prediction.tolist() if hasattr(prediction, 'tolist') else prediction,
            "timestamp": datetime.datetime.now().isoformat(),
            "model_id": metadata.get('id', '')
        }
        
        # For classification, add class labels
        if metadata.get('task') == 'classification' and 'classes' in metadata:
            classes = metadata['classes']
            
            if isinstance(prediction, np.ndarray) and prediction.size == 1:
                pred_class = int(prediction[0])
                if 0 <= pred_class < len(classes):
                    result["predicted_class"] = classes[pred_class]
            
            # Add probabilities if available
            if probabilities is not None:
                if isinstance(probabilities, np.ndarray):
                    probs = probabilities[0].tolist() if probabilities.shape[0] == 1 else probabilities.tolist()
                    result["probabilities"] = {cls: prob for cls, prob in zip(classes, probs)}
        
        return result
    
    def train_model(self, model_config: Dict[str, Any], 
                  training_data: Optional[Dict[str, Any]] = None,
                  data_source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Train a new predictive model
        
        Args:
            model_config: Model configuration
            training_data: Training data (optional)
            data_source: Data source for training (optional)
            
        Returns:
            Training results
        """
        try:
            # Generate model ID
            model_id = model_config.get('id', f"model_{uuid.uuid4().hex[:8]}")
            
            # Get training data
            X_train, y_train, X_test, y_test = self._get_training_data(
                model_config, training_data, data_source
            )
            
            if X_train is None or y_train is None:
                return {"error": "Failed to obtain training data"}
            
            # Train the model
            model_type = model_config.get('type', 'sklearn')
            task = model_config.get('task', 'classification')
            
            if model_type == 'sklearn':
                # Import scikit-learn here to not create hard dependency
                try:
                    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
                    from sklearn.linear_model import LogisticRegression, LinearRegression
                    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
                    
                    algorithm = model_config.get('algorithm', 'random_forest')
                    
                    # Create model based on task and algorithm
                    if task == 'classification':
                        if algorithm == 'random_forest':
                            model = RandomForestClassifier(
                                n_estimators=model_config.get('n_estimators', 100),
                                max_depth=model_config.get('max_depth', None)
                            )
                        elif algorithm == 'logistic_regression':
                            model = LogisticRegression(
                                C=model_config.get('regularization', 1.0),
                                max_iter=model_config.get('max_iter', 1000)
                            )
                        else:
                            return {"error": f"Unsupported algorithm: {algorithm}"}
                    
                    elif task == 'regression':
                        if algorithm == 'random_forest':
                            model = RandomForestRegressor(
                                n_estimators=model_config.get('n_estimators', 100),
                                max_depth=model_config.get('max_depth', None)
                            )
                        elif algorithm == 'linear_regression':
                            model = LinearRegression()
                        else:
                            return {"error": f"Unsupported algorithm: {algorithm}"}
                    
                    else:
                        return {"error": f"Unsupported task: {task}"}
                    
                    # Fit the model
                    model.fit(X_train, y_train)
                    
                    # Evaluate the model
                    y_pred = model.predict(X_test)
                    
                    metrics = {}
                    if task == 'classification':
                        metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
                        
                        if hasattr(model, 'classes_'):
                            model_config['classes'] = model.classes_.tolist()
                    
                    elif task == 'regression':
                        metrics['mse'] = float(mean_squared_error(y_test, y_pred))
                        metrics['r2'] = float(r2_score(y_test, y_pred))
                    
                    # Save the model
                    metadata = {
                        "id": model_id,
                        "name": model_config.get('name', f"Model {model_id}"),
                        "description": model_config.get('description', ''),
                        "type": model_type,
                        "task": task,
                        "algorithm": algorithm,
                        "features": model_config.get('features', []),
                        "target": model_config.get('target', ''),
                        "metrics": metrics,
                        "created": datetime.datetime.now().isoformat(),
                        "version": "1.0"
                    }
                    
                    if 'classes' in model_config:
                        metadata['classes'] = model_config['classes']
                    
                    success = self.save_model(model_id, model, metadata)
                    
                    if success:
                        return {
                            "model_id": model_id,
                            "message": f"Successfully trained model {model_id}",
                            "metrics": metrics
                        }
                    else:
                        return {"error": f"Failed to save model {model_id}"}
                    
                except ImportError:
                    return {"error": "scikit-learn not installed"}
            
            elif model_type == 'keras':
                try:
                    import tensorflow as tf
                    from tensorflow.keras.models import Sequential
                    from tensorflow.keras.layers import Dense, Dropout
                    
                    # Define model architecture
                    input_dim = X_train.shape[1]
                    model = Sequential()
                    
                    # Add layers based on configuration
                    layers = model_config.get('layers', [
                        {"units": 64, "activation": "relu"},
                        {"units": 32, "activation": "relu"}
                    ])
                    
                    # Input layer
                    model.add(Dense(layers[0]["units"], activation=layers[0]["activation"], 
                                  input_dim=input_dim))
                    
                    # Hidden layers
                    for layer in layers[1:]:
                        model.add(Dense(layer["units"], activation=layer["activation"]))
                        if "dropout" in layer:
                            model.add(Dropout(layer["dropout"]))
                    
                    # Output layer
                    if task == 'classification':
                        n_classes = len(set(y_train))
                        if n_classes > 2:
                            model.add(Dense(n_classes, activation='softmax'))
                            model.compile(
                                loss='sparse_categorical_crossentropy',
                                optimizer='adam',
                                metrics=['accuracy']
                            )
                        else:
                            model.add(Dense(1, activation='sigmoid'))
                            model.compile(
                                loss='binary_crossentropy',
                                optimizer='adam',
                                metrics=['accuracy']
                            )
                    else:  # regression
                        model.add(Dense(1, activation='linear'))
                        model.compile(
                            loss='mse',
                            optimizer='adam',
                            metrics=['mse', 'mae']
                        )
                    
                    # Train the model
                    epochs = model_config.get('epochs', 50)
                    batch_size = model_config.get('batch_size', 32)
                    
                    history = model.fit(
                        X_train, y_train,
                        validation_data=(X_test, y_test),
                        epochs=epochs,
                        batch_size=batch_size,
                        verbose=0
                    )
                    
                    # Evaluate the model
                    evaluation = model.evaluate(X_test, y_test, verbose=0)
                    metrics = {}
                    
                    if task == 'classification':
                        metrics['accuracy'] = float(evaluation[1])
                    else:  # regression
                        metrics['mse'] = float(evaluation[1])
                        metrics['mae'] = float(evaluation[2])
                    
                    # Save the model
                    metadata = {
                        "id": model_id,
                        "name": model_config.get('name', f"Model {model_id}"),
                        "description": model_config.get('description', ''),
                        "type": model_type,
                        "task": task,
                        "architecture": {
                            "layers": layers
                        },
                        "features": model_config.get('features', []),
                        "target": model_config.get('target', ''),
                        "metrics": metrics,
                        "training_history": {
                            key: [float(val) for val in values]
                            for key, values in history.history.items()
                        },
                        "created": datetime.datetime.now().isoformat(),
                        "version": "1.0"
                    }
                    
                    # Add class labels if available
                    if task == 'classification':
                        unique_classes = sorted(set(y_train))
                        metadata['classes'] = [str(cls) for cls in unique_classes]
                    
                    success = self.save_model(model_id, model, metadata)
                    
                    if success:
                        return {
                            "model_id": model_id,
                            "message": f"Successfully trained model {model_id}",
                            "metrics": metrics
                        }
                    else:
                        return {"error": f"Failed to save model {model_id}"}
                
                except ImportError:
                    return {"error": "TensorFlow/Keras not installed"}
            
            else:
                return {"error": f"Unsupported model type: {model_type}"}
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": f"Training error: {str(e)}"}
    
    def _get_training_data(self, model_config: Dict[str, Any],
                        training_data: Optional[Dict[str, Any]] = None,
                        data_source: Optional[Dict[str, Any]] = None) -> Tuple:
        """
        Get training data for model training
        
        Args:
            model_config: Model configuration
            training_data: Training data (optional)
            data_source: Data source specification (optional)
            
        Returns:
            Tuple of (X_train, y_train, X_test, y_test)
        """
        try:
            # Option 1: Use provided training data
            if training_data is not None:
                if 'X_train' in training_data and 'y_train' in training_data:
                    X_train = training_data['X_train']
                    y_train = training_data['y_train']
                    
                    # Use test data if provided, otherwise split training data
                    if 'X_test' in training_data and 'y_test' in training_data:
                        X_test = training_data['X_test']
                        y_test = training_data['y_test']
                    else:
                        # Import sklearn for train_test_split
                        from sklearn.model_selection import train_test_split
                        X_train, X_test, y_train, y_test = train_test_split(
                            X_train, y_train, 
                            test_size=MODEL_SETTINGS['validation_split_ratio'],
                            random_state=42
                        )
                    
                    return X_train, y_train, X_test, y_test
                    
            # Option 2: Fetch data from data source
            if data_source is not None:
                source_type = data_source.get('type', 'sql')
                
                if source_type == 'sql':                    # Fetch data from database
                    query = data_source.get('query', '')
                    if not query:
                        return None, None, None, None
                          # Import database connection using flexible import approach
                    try:
                        # Try relative import (assuming standard project structure)
                        from ....database.python.connection import DatabaseConnection
                    except (ImportError, ValueError):
                        try:
                            # Try using hyphenated project structure import mechanism
                            from database.python.connection import DatabaseConnection
                        except ImportError:
                            try:
                                # Try using underscore notation for hyphenated directories
                                from database_python.connection import DatabaseConnection
                            except ImportError:
                                # Fallback implementation if all import attempts fail
                                logger.warning("Could not import DatabaseConnection. Using fallback.")
                                class DatabaseConnection:
                                    def __init__(self):
                                        logger.warning("Using mock database connection")
                                    
                                    def get_connection(self):
                                        return None
                                    
                                    def close_connection(self):
                                        pass
                    
                    db_connection = DatabaseConnection()
                    conn = db_connection.get_connection()
                    
                    if not conn:
                        logger.error("Failed to connect to database")
                        return None, None, None, None
                    
                    import pandas as pd
                    
                    # Execute query
                    data_df = pd.read_sql(query, conn)
                    
                    # Prepare features and target
                    feature_columns = [f['name'] for f in model_config.get('features', [])]
                    target_column = model_config.get('target', '')
                    
                    if not feature_columns or not target_column or target_column not in data_df.columns:
                        return None, None, None, None
                    
                    # Filter to only include columns we need
                    valid_features = [col for col in feature_columns if col in data_df.columns]
                    
                    X = data_df[valid_features].values
                    y = data_df[target_column].values
                    
                    # Split data
                    from sklearn.model_selection import train_test_split
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, 
                        test_size=MODEL_SETTINGS['validation_split_ratio'],
                        random_state=42
                    )
                    
                    return X_train, y_train, X_test, y_test
                    
                elif source_type == 'csv':
                    # Load data from CSV file
                    file_path = data_source.get('path', '')
                    if not file_path:
                        return None, None, None, None
                    
                    import pandas as pd
                    
                    # Handle relative paths
                    if not os.path.isabs(file_path):
                        file_path = os.path.join(MODEL_SETTINGS['training_data_path'], file_path)
                    
                    # Read CSV
                    data_df = pd.read_csv(file_path)
                    
                    # Prepare features and target
                    feature_columns = [f['name'] for f in model_config.get('features', [])]
                    target_column = model_config.get('target', '')
                    
                    if not feature_columns or not target_column or target_column not in data_df.columns:
                        return None, None, None, None
                    
                    # Filter to only include columns we need
                    valid_features = [col for col in feature_columns if col in data_df.columns]
                    
                    X = data_df[valid_features].values
                    y = data_df[target_column].values
                    
                    # Split data
                    from sklearn.model_selection import train_test_split
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, 
                        test_size=MODEL_SETTINGS['validation_split_ratio'],
                        random_state=42
                    )
                    
                    return X_train, y_train, X_test, y_test
            
            # No valid data source
            return None, None, None, None
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return None, None, None, None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models
        
        Returns:
            List of model metadata
        """
        result = []
        
        for model_id, metadata in self.model_metadata.items():
            model_info = {
                "id": model_id,
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "type": metadata.get("type", ""),
                "task": metadata.get("task", ""),
                "algorithm": metadata.get("algorithm", ""),
                "created": metadata.get("created", ""),
                "last_updated": metadata.get("last_updated", ""),
                "metrics": metadata.get("metrics", {})
            }
            
            result.append(model_info)
            
        return result
    
    def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a model
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model details
        """
        if model_id not in self.model_metadata:
            return {"error": f"Model {model_id} not found"}
            
        # Return all metadata except large data
        metadata = self.model_metadata[model_id].copy()
        
        # Remove large data that might be in the metadata
        if 'training_data' in metadata:
            del metadata['training_data']
        
        return metadata
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if model_id not in self.model_metadata:
                logger.warning(f"Model {model_id} not found")
                return False
                
            # Delete model file
            model_dir = Path(MODEL_SETTINGS['model_path'])
            model_file = model_dir / f"{model_id}.pkl"
            
            if model_file.exists():
                model_file.unlink()
            
            # Remove from in-memory storage
            if model_id in self.models:
                del self.models[model_id]
                
            # Remove from metadata
            del self.model_metadata[model_id]
            
            # Save updated metadata
            metadata_file = model_dir / "model_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
            
            logger.info(f"Deleted model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False


# Create sample model configurations
def create_sample_model_configs():
    """Create sample model configurations"""
    configs = [
        {
            "id": "loan_default_predictor",
            "name": "Loan Default Risk Predictor",
            "description": "Predicts the likelihood of a loan defaulting based on customer and loan attributes",
            "type": "sklearn",
            "task": "classification",
            "algorithm": "random_forest",
            "n_estimators": 100,
            "max_depth": 10,
            "features": [
                {
                    "name": "loan_amount",
                    "description": "Loan amount",
                    "type": "numeric",
                    "preprocessing": "normalize",
                    "min": 0,
                    "max": 10000000
                },
                {
                    "name": "interest_rate",
                    "description": "Interest rate",
                    "type": "numeric"
                },
                {
                    "name": "loan_term",
                    "description": "Loan term in months",
                    "type": "numeric"
                },
                {
                    "name": "customer_age",
                    "description": "Customer age in years",
                    "type": "numeric"
                },
                {
                    "name": "customer_income",
                    "description": "Monthly income",
                    "type": "numeric",
                    "preprocessing": "normalize",
                    "min": 0,
                    "max": 1000000
                },
                {
                    "name": "debt_to_income",
                    "description": "Debt to income ratio",
                    "type": "numeric"
                },
                {
                    "name": "credit_score",
                    "description": "Credit score",
                    "type": "numeric",
                    "preprocessing": "normalize",
                    "min": 300,
                    "max": 900
                },
                {
                    "name": "employment_type",
                    "description": "Employment type",
                    "type": "categorical",
                    "preprocessing": "one_hot",
                    "categories": ["SALARIED", "SELF_EMPLOYED", "CONTRACT", "UNEMPLOYED"]
                }
            ],
            "target": "default_flag",
            "classes": ["NOT_DEFAULT", "DEFAULT"],
            "data_source": {
                "type": "sql",
                "query": """
                    SELECT 
                        l.loan_amount,
                        l.interest_rate,
                        l.loan_term,
                        TIMESTAMPDIFF(YEAR, c.date_of_birth, CURDATE()) as customer_age,
                        c.monthly_income as customer_income,
                        c.debt_to_income_ratio as debt_to_income,
                        c.credit_score,
                        c.employment_type,
                        CASE WHEN l.status = 'DEFAULT' THEN 1 ELSE 0 END as default_flag
                    FROM cbs_loans l
                    JOIN cbs_customers c ON l.customer_id = c.customer_id
                    WHERE l.status IN ('ACTIVE', 'CLOSED', 'DEFAULT')
                """
            }
        },
        {
            "id": "customer_churn_predictor",
            "name": "Customer Churn Predictor",
            "description": "Predicts the likelihood of a customer closing all accounts and leaving the bank",
            "type": "sklearn",
            "task": "classification",
            "algorithm": "logistic_regression",
            "regularization": 1.0,
            "max_iter": 1000,
            "features": [
                {
                    "name": "tenure_months",
                    "description": "Customer tenure in months",
                    "type": "numeric"
                },
                {
                    "name": "activity_score",
                    "description": "Transaction activity score",
                    "type": "numeric"
                },
                {
                    "name": "avg_balance",
                    "description": "Average account balance",
                    "type": "numeric",
                    "preprocessing": "normalize",
                    "min": 0,
                    "max": 1000000
                },
                {
                    "name": "products_count",
                    "description": "Number of products",
                    "type": "numeric"
                },
                {
                    "name": "digital_activity_pct",
                    "description": "Percentage of digital channel activity",
                    "type": "numeric"
                },
                {
                    "name": "service_calls_count",
                    "description": "Number of service calls in last 3 months",
                    "type": "numeric"
                },
                {
                    "name": "complaint_flag",
                    "description": "Has had a complaint",
                    "type": "binary"
                },
                {
                    "name": "segment",
                    "description": "Customer segment",
                    "type": "categorical",
                    "preprocessing": "one_hot",
                    "categories": ["STANDARD", "PREMIUM", "ELITE"]
                }
            ],
            "target": "churn_flag",
            "classes": ["ACTIVE", "CHURNED"],
            "data_source": {
                "type": "sql",
                "query": """
                    SELECT 
                        TIMESTAMPDIFF(MONTH, c.registration_date, CURDATE()) as tenure_months,
                        (SELECT COUNT(*) FROM cbs_transactions t 
                         JOIN cbs_accounts a ON t.account_id = a.account_id 
                         WHERE a.customer_id = c.customer_id 
                         AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as activity_score,
                        (SELECT AVG(balance) FROM cbs_accounts 
                         WHERE customer_id = c.customer_id) as avg_balance,
                        (SELECT COUNT(*) FROM cbs_product_subscriptions 
                         WHERE customer_id = c.customer_id) as products_count,
                        IFNULL((SELECT COUNT(*) FROM dc_login_history 
                                WHERE customer_id = c.customer_id AND login_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) / 30 * 100, 0) as digital_activity_pct,
                        (SELECT COUNT(*) FROM crm_service_requests 
                         WHERE customer_id = c.customer_id 
                         AND request_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)) as service_calls_count,
                        CASE WHEN EXISTS (SELECT 1 FROM crm_complaints 
                                         WHERE customer_id = c.customer_id) THEN 1 ELSE 0 END as complaint_flag,
                        c.segment,
                        CASE WHEN c.status = 'INACTIVE' THEN 1 ELSE 0 END as churn_flag
                    FROM cbs_customers c
                    WHERE c.registration_date <= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                """
            }
        }
    ]
    
    return configs


# Singleton instance
model_manager = ModelManager()


def get_model_manager() -> ModelManager:
    """Get the model manager instance"""
    return model_manager


# Initialize with sample models if needed
def init_module():
    """Initialize the module with sample data if needed"""
    model_dir = Path(MODEL_SETTINGS['model_path'])
    metadata_file = model_dir / "model_metadata.json"
    
    if not model_dir.exists() or not metadata_file.exists():
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample model configurations
        with open(model_dir / "sample_model_configs.json", 'w') as f:
            json.dump(create_sample_model_configs(), f, indent=2)
            logger.info("Created sample model configurations")


# Initialize module when imported
init_module()
