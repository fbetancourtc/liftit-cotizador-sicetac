# V0 MCP Integration Guide for Liftit Cotizador SICETAC

## 🎨 Overview

V0 MCP (Model Context Protocol) integration enables AI-powered UI component generation directly within Claude Desktop, providing seamless access to modern, beautiful interface designs tailored for our trucking quotation system.

## 🚀 Quick Setup

### Step 1: Get Your V0 API Key
1. Visit [v0.app](https://v0.app)
2. Sign up or log in
3. Go to Settings → API Keys
4. Generate a new API key

### Step 2: Configure Environment Variable

**macOS/Linux:**
```bash
echo 'export V0_API_KEY="your_v0_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:**
```cmd
setx V0_API_KEY "your_v0_api_key_here"
```

### Step 3: Configure Claude Desktop

Add V0 to your Claude Desktop MCP configuration:

**macOS/Linux:** `~/.config/claude-desktop/config.json`
**Windows:** `%APPDATA%\Claude Desktop\config.json`

```json
{
  "mcpServers": {
    // ... your existing MCP servers (keep them!) ...
    "v0": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.v0.dev",
        "--header",
        "Authorization: Bearer ${V0_API_KEY}"
      ]
    }
  }
}
```

### Step 4: Restart Claude Desktop
Close and reopen Claude Desktop to load the new configuration.

## 🎯 V0 Use Cases for SICETAC

### 1. Quote Results Enhancement
**Current:** Basic table display
**V0 Enhancement:** Interactive cards with animations

**Example Prompt:**
```
"Create a v0 chat for a trucking quote result card with:
- Liftit blue (#2B3492) accent colors
- Origin/destination route visualization
- Price breakdown with animated counters
- Vehicle configuration (3S3, 2S2) icon
- COP currency formatting
- Mobile-responsive design"
```

### 2. Real-time Price Indicators
**Current:** Static price display
**V0 Enhancement:** Live update badges with WebSocket integration

**Example Prompt:**
```
"Design a real-time price update indicator with:
- Pulse animation for live updates
- Green/red arrows for price changes
- Percentage change badge
- Last update timestamp
- Connection status indicator"
```

### 3. City Selector Upgrade
**Current:** Dropdown with search
**V0 Enhancement:** Map-based selector with popular routes

**Example Prompt:**
```
"Build an advanced city selector component with:
- Interactive Colombia map
- Search with fuzzy matching
- Popular routes quick-select
- Distance calculator
- Recent searches history"
```

### 4. Loading States & Skeletons
**Current:** Basic spinner
**V0 Enhancement:** Content-aware loading states

**Example Prompt:**
```
"Create loading skeleton screens for:
- Quote form submission
- Results display
- History loading
- Match our card-based layout
- Smooth shimmer effect"
```

### 5. Dashboard Visualizations
**Current:** Text-based metrics
**V0 Enhancement:** Interactive charts and graphs

**Example Prompt:**
```
"Design a pricing analytics dashboard with:
- Line chart for price trends
- Heat map for route popularity
- Donut chart for vehicle type distribution
- KPI cards with sparklines
- Dark mode support"
```

## 📋 V0 + Claude Code Workflow

### Standard Enhancement Flow

1. **Analyze Current Component**
   ```
   Claude Code: Read existing component → Understand structure
   ```

2. **Generate Enhanced Version**
   ```
   V0: Create modern UI → Multiple variations
   ```

3. **Integrate & Test**
   ```
   Claude Code: Adapt to project → Test locally → Commit
   ```

### Example Session
```
You: "Enhance the quote results section with modern cards"

Claude:
1. [Reads current implementation with Claude Code]
2. [Creates V0 chat for enhanced design]
3. [Generates component variations]
4. [Integrates best option into project]
5. [Tests at localhost:5050]
6. [Commits when approved]
```

## 🎨 Liftit Design System Specifications

When prompting V0, always include these brand guidelines:

### Colors
```css
Primary: #2B3492 (Liftit Blue)
Primary Dark: #1e2670
Secondary: #F59E0B (Amber)
Success: #10B981
Error: #EF4444
Background: #F8FAFC
Card: #FFFFFF
Text Primary: #333333
Text Secondary: #6B7280
```

### Typography
```css
Font Family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
Headings: 700 weight, -0.5px letter-spacing
Body: 400 weight, 1.6 line-height
```

### Spacing
```css
Base unit: 8px
Spacing scale: 8, 16, 24, 32, 48, 64
Card padding: 24px (desktop), 16px (mobile)
Border radius: 12px (cards), 8px (buttons), 4px (inputs)
```

### Breakpoints
```css
Mobile: < 768px
Tablet: 768px - 1023px
Desktop: 1024px - 1439px
Large: 1440px+
```

## 🚦 V0 Prompting Best Practices

### DO ✅
- Include Liftit brand colors and fonts
- Specify responsive breakpoints
- Request accessibility features (ARIA labels, keyboard nav)
- Ask for Colombian Spanish labels
- Include COP currency formatting
- Request loading and error states

### DON'T ❌
- Generate without brand guidelines
- Ignore existing component patterns
- Skip mobile responsiveness
- Forget localization needs
- Overcomplicate simple components

## 📝 Example V0 Prompts for SICETAC

### Quote Form Enhancement
```
"Create a multi-step quote form wizard with:
1. Route selection (origin/destination with map)
2. Vehicle configuration (visual selector)
3. Additional options (logistics hours, cargo type)
4. Review & submit
- Liftit blue theme (#2B3492)
- Progress indicator
- Form validation
- Mobile-optimized
- Spanish labels"
```

### Price Comparison Table
```
"Design a responsive price comparison table with:
- Sticky header
- Sortable columns
- Highlight best price
- Expandable row details
- Export to PDF button
- COP currency format
- Mobile card view
- Loading skeleton"
```

### Route History Timeline
```
"Build a quote history timeline component with:
- Chronological layout
- Status badges (active, completed, cancelled)
- Price trend indicators
- Quick re-quote action
- Filter by date range
- Search functionality
- Infinite scroll
- Empty state design"
```

## 🔧 Troubleshooting

### Issue: "V0 MCP not available"
**Solution:**
1. Check V0_API_KEY is set: `echo $V0_API_KEY`
2. Restart Claude Desktop
3. Verify config.json syntax

### Issue: "Generated code doesn't match style"
**Solution:**
Always include brand colors and design system specs in prompts

### Issue: "Component not responsive"
**Solution:**
Explicitly request "mobile-first responsive design" in prompts

## 🎯 Quick Start Checklist

- [ ] V0 account created
- [ ] API key generated
- [ ] Environment variable set
- [ ] Claude Desktop configured
- [ ] Test prompt executed
- [ ] First component generated

## 📚 Resources

- [V0 Documentation](https://v0.app/docs)
- [MCP Protocol Spec](https://modelcontextprotocol.io)
- [Liftit Brand Guidelines](/docs/brand-guidelines.md)
- [Component Library](/docs/components.md)

## 💡 Pro Tips

1. **Batch Variations:** Ask V0 to generate 3-4 variations of each component
2. **Progressive Enhancement:** Start simple, iterate with refinements
3. **Component Library:** Save successful V0 generations for reuse
4. **A/B Testing:** Use V0 variants for user testing
5. **Accessibility First:** Always request WCAG compliance

---

*Last Updated: December 2024*
*Maintained by: Liftit Growth Team*