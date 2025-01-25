import os
import sys

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
)
from networksecurity.entity.config_entity import ModelTrainerConfig


from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.utils.main_utils.utils import save_object, load_object
from networksecurity.utils.main_utils.utils import (
    load_numpy_array_data,
    evaluate_models,
)
from networksecurity.utils.ml_utils.metric.classification_metric import (
    get_classification_score,
)

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
import mlflow  # type: ignore
from urllib.parse import urlparse

import dagshub  # type: ignore

dagshub.init(
    repo_owner="HarshavardhanKurtkoti",
    repo_name="Phising_Domain_Detection",
    mlflow=True,
)

os.environ["MLFLOW_TRACKING_URI"] = (
    "https://dagshub.com/HarshavardhanKurtkoti/Phising_Domain_Detection.mlflow"
)
os.environ["MLFLOW_TRACKING_USERNAME"] = os.getenv("DAGSHUB_USERNAME")
os.environ["MLFLOW_TRACKING_PASSWORD"] = os.getenv("DAGSHUB_TOKEN")


class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact,
    ):
        try:
            self.model_trainer_config = model_trainer_config
            self.data_transformation_artifact = data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def track_mlflow(self, best_model, classificationmetric):
        mlflow.set_registry_uri(
            "https://dagshub.com/HarshavardhanKurtkoti/Phising_Domain_Detection.mlflow"
        )
        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
        with mlflow.start_run():
            f1_score = classificationmetric.f1_score
            precision_score = classificationmetric.precision_score
            recall_score = classificationmetric.recall_score

            mlflow.log_metric("f1_score", f1_score)
            mlflow.log_metric("precision", precision_score)
            mlflow.log_metric("recall_score", recall_score)
            mlflow.sklearn.log_model(best_model, "model")
            
            if tracking_url_type_store != "file":

                mlflow.sklearn.log_model(
                    best_model,
                    "model",
                    registered_model_name="phishing_detection_model",
                )
            else:
                mlflow.sklearn.log_model(best_model, "model")

    def train_model(self, X_train, y_train, X_test, y_test):
        # Define models and hyperparameters
        models = {
            "Random Forest": RandomForestClassifier(verbose=1),
            "Decision Tree": DecisionTreeClassifier(),
            "Gradient Boosting": GradientBoostingClassifier(verbose=1),
            "Logistic Regression": LogisticRegression(verbose=1, max_iter=1000),
            "AdaBoost": AdaBoostClassifier(),
        }

        params = {
            "Decision Tree": {
                "criterion": ["gini", "entropy", "log_loss"],
                "splitter": ["best", "random"],
                "max_features": ["sqrt", "log2", None],
                "max_depth": [None, 10, 20, 30, 50],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_leaf_nodes": [None, 10, 20, 50],
            },
            "Random Forest": {
                "criterion": ["gini", "entropy", "log_loss"],
                "max_features": ["sqrt", "log2", None],
                "n_estimators": [8, 16, 32, 64, 128, 256, 512],
                "max_depth": [None, 10, 20, 30, 50],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "bootstrap": [True, False],
            },
            "Gradient Boosting": {
                "loss": ["log_loss", "exponential"],
                "learning_rate": [0.01, 0.05, 0.1, 0.2, 0.5],
                "subsample": [0.6, 0.7, 0.75, 0.85, 0.9],
                "criterion": ["squared_error", "friedman_mse"],
                "max_features": ["auto", "sqrt", "log2"],
                "n_estimators": [8, 16, 32, 64, 128, 256, 512],
                "max_depth": [3, 5, 10, 20],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            },
            "Logistic Regression": {
                "penalty": ["l1", "l2", "elasticnet", None],
                "C": [0.01, 0.1, 1, 10, 100],
                "solver": ["lbfgs", "saga", "liblinear", "newton-cg", "sag"],
                "max_iter": [100, 500, 1000],
                "class_weight": [None, "balanced"],
            },
            "AdaBoost": {
                "learning_rate": [0.01, 0.1, 0.5, 1],
                "n_estimators": [8, 16, 32, 64, 128, 256, 512],
                "algorithm": ["SAMME", "SAMME.R"],
                "base_estimator": [None, DecisionTreeClassifier(max_depth=1)],
            },
        }

        # Evaluate models with hyperparameters
        model_report: dict = evaluate_models(
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            models=models,
            param=params,
        )

        # Get the best model and score
        best_model_score = max(sorted(model_report.values()))
        best_model_name = list(model_report.keys())[
            list(model_report.values()).index(best_model_score)
        ]
        best_model = models[best_model_name]

        # Train and evaluate the best model
        y_train_pred = best_model.predict(X_train)
        classification_train_metric = get_classification_score(
            y_true=y_train, y_pred=y_train_pred
        )
        self.track_mlflow(best_model, classification_train_metric)

        y_test_pred = best_model.predict(X_test)
        classification_test_metric = get_classification_score(
            y_true=y_test, y_pred=y_test_pred
        )
        self.track_mlflow(best_model, classification_test_metric)

        # Save the model and preprocessor
        preprocessor = load_object(
            file_path=self.data_transformation_artifact.transformed_object_file_path
        )
        model_dir_path = os.path.dirname(
            self.model_trainer_config.trained_model_file_path
        )
        os.makedirs(model_dir_path, exist_ok=True)

        Network_Model = NetworkModel(preprocessor=preprocessor, model=best_model)
        save_object(
            self.model_trainer_config.trained_model_file_path, obj=Network_Model
        )
        save_object("final_model/model.pkl", best_model)

        # Create Model Trainer Artifact
        model_trainer_artifact = ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,
            train_metric_artifact=classification_train_metric,
            test_metric_artifact=classification_test_metric,
        )
        logging.info(f"Model trainer artifact: {model_trainer_artifact}")
        return model_trainer_artifact

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_file_path = (
                self.data_transformation_artifact.transformed_train_file_path
            )
            test_file_path = (
                self.data_transformation_artifact.transformed_test_file_path
            )

            # loading training array and testing array
            train_arr = load_numpy_array_data(train_file_path)
            test_arr = load_numpy_array_data(test_file_path)

            x_train, y_train, x_test, y_test = (
                train_arr[:, :-1],
                train_arr[:, -1],
                test_arr[:, :-1],
                test_arr[:, -1],
            )

            model_trainer_artifact = self.train_model(x_train, y_train, x_test, y_test)
            return model_trainer_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)