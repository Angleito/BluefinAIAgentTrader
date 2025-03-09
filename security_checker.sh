#!/bin/bash
# Security checker script for PerplexityTrader

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running security checks for PerplexityTrader${NC}"
echo "====================================================="

# Check for outdated packages
echo -e "\n${YELLOW}Checking for outdated Python packages...${NC}"
cd /home/angle/perpleixtytrader
pip list --outdated

# Check dependencies against vulnerability database
echo -e "\n${YELLOW}Checking for known vulnerabilities in dependencies...${NC}"
if command -v safety &> /dev/null; then
    safety check -r infrastructure/docker/requirements.txt
else
    echo -e "${RED}Safety not installed. Run 'pip install safety' to enable vulnerability scanning.${NC}"
    echo "You can then run: safety check -r infrastructure/docker/requirements.txt"
fi

# Check for exposed secrets
echo -e "\n${YELLOW}Checking for exposed secrets or API keys...${NC}"
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --all-files
else
    echo -e "${RED}detect-secrets not installed. Run 'pip install detect-secrets' to scan for exposed secrets.${NC}"
    echo "You can then run: detect-secrets scan --all-files"
fi

# Check Docker security
echo -e "\n${YELLOW}Checking Docker security...${NC}"
if command -v docker-bench-security &> /dev/null; then
    docker-bench-security
else
    echo -e "${RED}docker-bench-security not installed.${NC}"
    echo "You can install it from: https://github.com/docker/docker-bench-security"
fi

# Check permissions
echo -e "\n${YELLOW}Checking file permissions...${NC}"
find . -name "*.sh" -not -perm -u=x -exec ls -l {} \;

# Recommendations
echo -e "\n${YELLOW}Security Recommendations:${NC}"
echo "1. Regularly update dependencies to patch vulnerabilities"
echo "2. Use environment variables for sensitive configuration (never hardcode)"
echo "3. Enable Docker volume mounts as read-only when possible"
echo "4. Run containers with no-new-privileges:true"
echo "5. Run containers with --read-only flag when possible"
echo "6. Use a Web Application Firewall (WAF) in production"
echo "7. Implement rate limiting for all API endpoints"
echo "8. Add HTTPS with proper certificate management"

echo -e "\n${GREEN}Security check complete!${NC}" 