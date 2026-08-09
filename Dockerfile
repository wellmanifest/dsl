FROM python:3.12.11-alpine3.22

WORKDIR /workspace
COPY . /workspace

CMD ["python3", ".governance/governance_check.py", "--root", ".", "--actor", "agent"]
