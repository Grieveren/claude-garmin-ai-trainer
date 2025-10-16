# Architecture Diagrams

This directory contains Mermaid diagrams that visualize the system architecture.

## Viewing the Diagrams

### Option 1: GitHub (Recommended)
GitHub natively supports Mermaid diagrams. Simply view the `.mmd` files on GitHub and they will be rendered automatically.

### Option 2: VS Code
Install the **Mermaid Preview** extension:
1. Open VS Code Extensions (Cmd+Shift+X)
2. Search for "Mermaid Preview" or "Markdown Preview Mermaid Support"
3. Install and reload
4. Open any `.mmd` file and preview it

### Option 3: Mermaid Live Editor
1. Visit https://mermaid.live
2. Copy the content of any `.mmd` file
3. Paste it into the editor to see the rendered diagram

### Option 4: Command Line (Using Mermaid CLI)
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from any diagram
mmdc -i system_architecture.mmd -o system_architecture.png

# Generate SVG
mmdc -i system_architecture.mmd -o system_architecture.svg
```

## Available Diagrams

### 1. System Architecture (`system_architecture.mmd`)
**Type**: Component Diagram
**Purpose**: Shows the complete system architecture with all layers and components

**Includes**:
- Presentation layer (Web Dashboard, Mobile App)
- API layer (FastAPI, middleware)
- Service layer (all business logic services)
- Repository layer (data access)
- Infrastructure layer (database, cache, file storage)
- External services (Garmin API, Claude AI, Email)
- Background jobs
- Monitoring and observability

**Best for**: Understanding overall system structure and component relationships

---

### 2. Data Flow (`data_flow.mmd`)
**Type**: Sequence Diagram
**Purpose**: Shows how data flows through the system in various scenarios

**Includes**:
- Daily automated sync flow (Garmin → Database → AI → Notifications)
- User dashboard view flow
- On-demand AI analysis request
- Training plan generation
- Error handling and retry logic

**Best for**: Understanding step-by-step data processing and service interactions

---

### 3. Authentication Flow (`authentication_flow.mmd`)
**Type**: Sequence Diagram
**Purpose**: Shows authentication and authorization processes

**Includes**:
- User registration flow
- Login flow (JWT token generation)
- Authenticated API request flow
- Token refresh flow
- Logout flow
- Garmin API authentication (background)
- Authorization checks (resource ownership)
- Rate limiting flow

**Best for**: Understanding security implementation and token lifecycle

---

### 4. Service Interactions (`service_interactions.mmd`)
**Type**: Dependency Graph
**Purpose**: Shows how services interact with each other and shared concerns

**Includes**:
- Service dependencies (which services call which)
- Repository usage (which services access which data)
- External API integrations
- Cross-cutting concerns (logging, caching, error handling, validation)

**Best for**: Understanding service boundaries and dependencies

---

## Diagram Key

### Color Coding

- **Light Blue** (`#e1f5ff`): User/Client layer
- **Purple** (`#f3e5f5`): Presentation layer (UI)
- **Orange** (`#fff3e0`): API layer (endpoints, middleware)
- **Green** (`#e8f5e9`): Service layer (business logic)
- **Pink** (`#fce4ec`): Data access layer (repositories)
- **Teal** (`#e0f2f1`): Infrastructure layer (database, cache)
- **Yellow** (`#fff9c4`): External services (APIs)
- **Deep Purple** (`#ede7f6`): Background jobs
- **Red** (`#ffebee`): Monitoring and observability

### Common Symbols

- **Solid Arrow** (`-->`) : Direct dependency or data flow
- **Dotted Arrow** (`-.->`) : Optional or future dependency
- **Rectangle** : Service or component
- **Cylinder** : Database or data store
- **Note** : Additional context or information

---

## Updating Diagrams

When making changes to the architecture:

1. **Update the affected `.mmd` file(s)**
2. **Verify syntax**: Use https://mermaid.live to validate
3. **Update architecture.md** if structure changes significantly
4. **Commit both diagram and documentation changes together**

### Mermaid Syntax Resources

- [Official Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Mermaid Sequence Diagram Syntax](https://mermaid.js.org/syntax/sequenceDiagram.html)
- [Mermaid Live Editor](https://mermaid.live) - Test your diagrams here

---

## Exporting Diagrams

### For Documentation
```bash
# Export as high-quality PNG (for docs)
mmdc -i system_architecture.mmd -o system_architecture.png -w 2400 -H 1800

# Export as SVG (scalable, best for web)
mmdc -i system_architecture.mmd -o system_architecture.svg
```

### For Presentations
```bash
# Export all diagrams as PNG
for file in *.mmd; do
  mmdc -i "$file" -o "${file%.mmd}.png" -w 1920 -H 1080 -b white
done
```

### For PDF Documentation
```bash
# Export as PDF
mmdc -i system_architecture.mmd -o system_architecture.pdf
```

---

## Integration with Documentation

These diagrams are referenced in:
- `../architecture.md` - Main architecture document
- `../ARCHITECTURE_SUMMARY.md` - Quick reference guide
- `../api_design.md` - API documentation

---

## Questions?

If you have questions about the diagrams or need help understanding the architecture:
1. Review the corresponding documentation in `../architecture.md`
2. Check the `../ARCHITECTURE_SUMMARY.md` for quick reference
3. Use Mermaid Live Editor to explore the diagrams interactively
