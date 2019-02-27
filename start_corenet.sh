#!/bin/sh

# ====================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ====================================================================

echo -e "${GREEN}Sourcing virtual env ./venv/bin/activate${NC}"
source venv/bin/activate
echo -e "${GREEN}Starting Database...${NC}"
nohup python Database/db_core.py
sleep 60s
echo -e "${GREEN}Starting Collector...${NC}"
nohup python Event-Collector/collector.py
sleep 60s
echo -e "${GREEN}Starting Executor...${NC}"
nohup python Executor/executor.py
sleep 60s
echo -e "${GREEN}Starting Evaluator...${NC}"
nohup python Evaluator/evaluate.py
