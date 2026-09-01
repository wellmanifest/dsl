FROM python:3.12.11-alpine3.22@sha256:efcdfa6a6b2fd2afb9c7dfa9a5b288a6f68338b5cfdebe6b637d986067d85757

WORKDIR /workspace
COPY . /workspace

CMD ["python3", ".governance/governance_check.py", "--root", ".", "--actor", "agent"]
