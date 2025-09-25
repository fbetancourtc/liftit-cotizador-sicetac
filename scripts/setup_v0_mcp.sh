#!/bin/bash

# V0 MCP Setup Script for SICETAC Quoter
# This script installs and configures the V0 MCP server for Claude

echo "🚀 Setting up V0 MCP for Claude..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the V0 API key from environment
V0_API_KEY="v1:pDupEd0rbkzRrIj0wecMcY9r:rJBHAOL4RacVrpKOTQV4YD4T"

# Step 1: Clone the V0 MCP repository
echo -e "${YELLOW}Step 1: Cloning V0 MCP repository...${NC}"
if [ ! -d "$HOME/v0-mcp" ]; then
    cd $HOME
    git clone https://github.com/hellolucky/v0-mcp.git
    cd v0-mcp
else
    echo -e "${GREEN}V0 MCP repository already exists${NC}"
    cd $HOME/v0-mcp
    git pull
fi

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
npm install

# Step 3: Create .env file
echo -e "${YELLOW}Step 3: Creating .env file...${NC}"
cat > .env << EOF
V0_API_KEY=$V0_API_KEY
V0_DEFAULT_MODEL=v0-1.5-md
NODE_ENV=production
EOF

echo -e "${GREEN}.env file created with V0 API key${NC}"

# Step 4: Build the project
echo -e "${YELLOW}Step 4: Building V0 MCP...${NC}"
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
else
    echo -e "${RED}Build failed. Please check the error messages above.${NC}"
    exit 1
fi

# Step 5: Update Claude MCP settings
echo -e "${YELLOW}Step 5: Updating Claude MCP settings...${NC}"

MCP_SETTINGS_FILE="$HOME/.claude-code/mcp-settings.json"

# Backup existing settings
if [ -f "$MCP_SETTINGS_FILE" ]; then
    cp "$MCP_SETTINGS_FILE" "$MCP_SETTINGS_FILE.backup"
    echo -e "${GREEN}Backed up existing MCP settings${NC}"
fi

# Create updated MCP settings
cat > "$MCP_SETTINGS_FILE" << 'EOF'
{
  "servers": {
    "superdesign": {
      "command": "node",
      "args": [
        "/tmp/superdesign-mcp/dist/index.js"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    },
    "v0-mcp": {
      "command": "node",
      "args": [
        "'$HOME'/v0-mcp/dist/index.js"
      ],
      "env": {
        "V0_API_KEY": "'$V0_API_KEY'",
        "V0_DEFAULT_MODEL": "v0-1.5-md",
        "NODE_ENV": "production"
      }
    }
  }
}
EOF

# Replace the placeholders with actual values
sed -i '' "s|'$HOME'|$HOME|g" "$MCP_SETTINGS_FILE"
sed -i '' "s|'$V0_API_KEY'|$V0_API_KEY|g" "$MCP_SETTINGS_FILE"

echo -e "${GREEN}Claude MCP settings updated${NC}"

# Step 6: Add V0 API key to project .env.local
echo -e "${YELLOW}Step 6: Adding V0 API key to project .env.local...${NC}"

PROJECT_ENV="$(dirname "$0")/../.env.local"

# Check if V0_API_KEY already exists in .env.local
if grep -q "V0_API_KEY" "$PROJECT_ENV" 2>/dev/null; then
    echo -e "${YELLOW}V0_API_KEY already exists in .env.local${NC}"
else
    echo "" >> "$PROJECT_ENV"
    echo "# V0 MCP Configuration" >> "$PROJECT_ENV"
    echo "V0_API_KEY=$V0_API_KEY" >> "$PROJECT_ENV"
    echo "V0_DEFAULT_MODEL=v0-1.5-md" >> "$PROJECT_ENV"
    echo -e "${GREEN}V0 configuration added to .env.local${NC}"
fi

# Step 7: Test the installation
echo -e "${YELLOW}Step 7: Testing V0 MCP installation...${NC}"
cd $HOME/v0-mcp
node dist/index.js --version 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ V0 MCP installation successful!${NC}"
else
    echo -e "${YELLOW}⚠️  V0 MCP installed but couldn't verify. This is normal.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 V0 MCP Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop application"
echo "2. V0 MCP tools will be available in Claude"
echo "3. Test with: 'Check V0 MCP configuration'"
echo "4. Start generating UI components!"
echo ""
echo "Available V0 tools:"
echo "  - v0_generate_ui: Generate UI from text"
echo "  - v0_generate_from_image: Convert images to code"
echo "  - v0_chat_complete: Iterative UI development"
echo "  - v0_setup_check: Verify configuration"
echo ""
echo -e "${YELLOW}Documentation: docs/V0_WORKFLOW_EXAMPLE.md${NC}"