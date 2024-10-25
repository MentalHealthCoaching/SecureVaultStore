```python
import pytest
import os

def pytest_addoption(parser):
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8000",
        help="URL of the SecureVault API"
    )
    parser.addoption(
        "--test-file-size",
        action="store",
        default="1024",
        type=int,
        help="Size of test files in bytes"
    )

@pytest.fixture(scope="session")
def api_url(request):
    return request.config.getoption("--api-url")

@pytest.fixture(scope="session")
def test_file_size(request):
    return request.config.getoption("--test-file-size")
```
