#!/bin/sh

# ====================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ====================================================================

echo "${GREEN}Sourcing virtual env ./venv/bin/activate${NC}"
source venv/bin/activate
echo "${GREEN}Starting Database...${NC}"
cd Database
nohup python db_core.py &
cd ..
echo "${YELLOW}Sleeping for 30 seconds ...${NC}"
sleep 30s
echo "${GREEN}Starting Collector...${NC}"
cd Event-Collector
nohup python collector.py &
cd ..
echo "${YELLOW}Sleeping for 30 seconds ...${NC}"
sleep 30s
echo "${GREEN}Starting Executor...${NC}"
cd Executor
nohup python executor.py &
cd ..
echo "${YELLOW}Sleeping for 30 seconds ...${NC}"
sleep 30s
echo "${GREEN}Starting Evaluator...${NC}"
cd Evaluator
nohup python evaluate.py &
cd ..
