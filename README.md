# Phishing Domain Detection with MLOps

Welcome to the **Phishing Domain Detection** project! This project demonstrates an **end-to-end Machine Learning** workflow, from data collection and processing to model training, evaluation, and deployment. The project incorporates **industry-standard MLOps practices**, including **CI/CD pipelines**, **model tracking**, **logging**, **exception handling**, and **cloud deployment**.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technologies Used](#technologies-used)
4. [Project Setup](#project-setup)
5. [Data Version Control (DVC)](#data-version-control-dvc)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Model Tracking](#model-tracking)
8. [Containerization with Docker](#containerization-with-docker)
9. [Cloud Storage](#cloud-storage)
10. [Environment Setup](#environment-setup)
11. [Contributing](#contributing)
12. [License](#license)

## Project Overview

This project aims to detect phishing domains using a Machine Learning model. The system is built using **MLOps principles**, allowing for an automated, scalable, and repeatable process that mimics industry-standard practices. The project includes several components like:

- **ETL Pipelines**: Extracting, transforming, and loading data into the system.
- **Training Pipelines**: Training the model and testing it for accuracy.
- **Model Deployment**: Deploying the trained model for real-time use.
- **MongoDB**: Data storage solution for efficient access and retrieval of data during the pipeline execution.

## Architecture

The project follows a modular architecture to ensure scalability and maintainability. The components of the architecture include:

1. **Data Collection & Preprocessing**: We gather phishing domain data and preprocess it to ensure it's suitable for training.
2. **ETL Pipelines**:
   - **Data Ingestion**: Raw data is ingested from various sources, including MongoDB.
   - **Data Transformation**: Data is cleaned, structured, and prepared for training.
   - **Data Validation**: Ensures data integrity and correctness before training.
3. **Training Pipeline**: Machine learning algorithms are applied to train a model for phishing detection.
4. **Model Storage**: Models are saved to AWS S3 and Docker images are stored in AWS ECR.
5. **CI/CD Pipeline**: GitHub Actions automate the build, testing, and deployment process.
6. **Model Tracking**: MLflow and DVC are used to track experiments and models.

## Technologies Used

- **AWS S3**: Storage for model artifacts.
- **AWS ECR**: Repository for Docker images.
- **GitHub Actions**: CI/CD pipelines for automating builds and deployments.
- **DVC**: Data Version Control for managing datasets and experiments.
- **MLflow**: Model tracking, logging, and managing experiments.
- **Docker**: Containerization of the application for easy deployment.
- **MongoDB**: NoSQL database used for storing and managing data efficiently.
- **Python**: Programming language for implementing ML models and pipelines.
- **.env files**: Secure storage of environment variables.
- **setup.py**: Python packaging for managing dependencies.

## Project Setup

### Prerequisites

1. **Python 3.8+**: Ensure you have Python installed. You can download it from [here](https://www.python.org/downloads/).
2. **Docker**: Docker is required to build and deploy containerized applications. You can download it from [here](https://www.docker.com/get-started).
3. **GitHub Account**: Required for interacting with the repository and CI/CD pipelines.
4. **AWS Account**: For storing artifacts and Docker images.
5. **MongoDB**: Installed locally or accessed through MongoDB Atlas for storing and retrieving data. If using MongoDB Atlas, follow this [setup guide](https://www.mongodb.com/docs/atlas/tutorial/create-new-cluster/).

### Clone the Repository

```bash
git clone https://github.com/HarshavardhanKurtkoti/Phising_Domain_Detection.git
cd Phising_Domain_Detection
```

### Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### Setup Environment Variables

Create a `.env` file to store sensitive information such as AWS credentials, MongoDB credentials, and other configuration parameters:

```plaintext
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_aws_region
MONGO_URI=mongodb+srv://your_mongo_db_connection
```

### Docker Setup

To build the Docker image:

```bash
docker build -t phishing-detection .
```

### Running the Application

After setting up the environment, run the training pipeline:

```bash
python train.py
```

## Data Version Control (DVC)

We use **DVC** to version control our datasets and model artifacts. DVC helps track data changes, making it easier to collaborate on machine learning projects.

### Tracking Experiments

All experiments, including model parameters, metrics, and datasets, are tracked using **DVC**. You can view the experiment history using the following command:

```bash
dvc exp show
```

Check the experiment repository for a detailed history of all experiments: [DVC Repository](https://dagshub.com/HarshavardhanKurtkoti/Phising_Domain_Detection/experiments).

## CI/CD Pipeline

### GitHub Actions

We use **GitHub Actions** to automate our CI/CD pipeline. This ensures that every change to the codebase is automatically built, tested, and deployed. The pipeline is defined in the `main.yaml` file.

Key stages of the pipeline:

- **Build**: Build the Docker image and install dependencies.
- **Test**: Run unit tests on the codebase.
- **Deploy**: Deploy the model to AWS or other cloud services.

### Example of `main.yaml` Workflow

```yaml
name: workflow

on:
  push:
    branches:
      - main
    paths-ignore:
      - 'README.md'

permissions:
  id-token: write
  contents: read

jobs:
  integration:
    name: Continuous Integration
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Lint code
        run: echo "Linting repository"

      - name: Run unit tests
        run: echo "Running unit tests"

  build-and-push-ecr-image:
    name: Continuous Delivery
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Install Utilities
        run: |
          sudo apt-get update
          sudo apt-get install -y jq unzip
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{secrets.AWS_REGION  }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY_NAME }}
          IMAGE_TAG: latest
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "::set-output name=image::$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

  Continuous-Deployment:
    needs: build-and-push-ecr-image
    runs-on: self-hosted
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Pull latest images
        run: |
         docker pull ${{secrets.AWS_ECR_LOGIN_URI}}/${{ secrets.ECR_REPOSITORY_NAME }}:latest
         
      - name: Run Docker Image to serve users
        run: |
         docker run -d -p 8080:8080 --ipc="host" --name=networksecurity -e 'AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }}' -e 'AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}' -e 'AWS_REGION=${{ secrets.AWS_REGION }}'  ${{secrets.AWS_ECR_LOGIN_URI}}/${{ secrets.ECR_REPOSITORY_NAME }}:latest
      - name: Clean previous images and containers
        run: |
         docker system prune -f
```

## Model Tracking

**MLflow** is used to track the progress of different experiments. It helps to log model metrics, parameters, and artifacts, providing a detailed view of how the models are performing.

## Containerization with Docker

The project is fully containerized using **Docker**, making it easy to deploy and run anywhere. The project is packaged into a Docker image, ensuring that the environment remains consistent across different systems.

### Dockerfile Example

```dockerfile
FROM python:3.10-slim-buster
WORKDIR /app
COPY . /app

RUN apt update -y && apt install awscli -y

RUN apt-get update && pip install -r requirements.txt
CMD ["python3", "app.py"]
```

## Cloud Storage

Model artifacts and Docker images are stored in **AWS S3** and **AWS ECR**, respectively.

- **AWS S3**: Used to store large model files and other artifacts.
- **AWS ECR**: Stores Docker images for easy deployment to AWS services like ECS or Lambda.

## Environment Setup

To ensure smooth project execution, the **setup.py** script manages all dependencies and configurations for the project:

```bash
python setup.py install
```

## Pipeline Stages

The pipeline follows a structured sequence of stages to ensure efficient data processing and model training:

1. **Data Ingestion**: Raw data is ingested from multiple sources and stored in MongoDB for efficient access.
2. **Data Transformation**: The raw data is cleaned and transformed to be ready for model training.
3. **Data Validation**: This step ensures that the data is consistent, accurate, and ready for model training.
4. **Model Training**: Machine learning algorithms are applied to the transformed and validated data to train a model that can detect phishing domains.

## Contributing

Contributions to this project are welcome! If you find any issues or want to enhance the project, please feel free to create a pull request or submit an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
