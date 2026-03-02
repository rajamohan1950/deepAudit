from app.ingestion.classifier import FileClassifier, FileType


def test_classify_python_source():
    classifier = FileClassifier()
    files = [{"path": "app/main.py", "extension": ".py"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.SOURCE_CODE
    assert result[0]["language"] == "python"


def test_classify_dockerfile():
    classifier = FileClassifier()
    files = [{"path": "Dockerfile", "extension": ""}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.DOCKER


def test_classify_k8s():
    classifier = FileClassifier()
    files = [{"path": "k8s/deployment.yaml", "extension": ".yaml"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.K8S


def test_classify_terraform():
    classifier = FileClassifier()
    files = [{"path": "infra/main.tf", "extension": ".tf"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.IAC


def test_classify_cicd():
    classifier = FileClassifier()
    files = [{"path": ".github/workflows/ci.yml", "extension": ".yml"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.CICD


def test_classify_dependency():
    classifier = FileClassifier()
    files = [{"path": "requirements.txt", "extension": ".txt"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.DEPENDENCY


def test_classify_test():
    classifier = FileClassifier()
    files = [{"path": "tests/test_auth.py", "extension": ".py"}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.TEST


def test_classify_env_as_security():
    classifier = FileClassifier()
    files = [{"path": ".env", "extension": ""}]
    result = classifier.classify(files)
    assert result[0]["file_type"] == FileType.SECURITY
