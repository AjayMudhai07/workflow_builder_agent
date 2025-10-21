# Frontend Setup Complete

## Overview

The IRA Orchestrator frontend has been successfully initialized with Next.js 15.5.5, TypeScript, Tailwind CSS v4, and shadcn/ui component library.

## Technology Stack

- **Next.js**: 15.5.5 with Turbopack enabled
- **React**: 19.1.0
- **TypeScript**: 5.x
- **Tailwind CSS**: v4 (latest)
- **shadcn/ui**: Component library (New York style)
- **Icon Library**: Lucide React
- **MCP Server**: Configured for AI-assisted component development

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── globals.css   # Global styles with CSS variables
│   │   ├── layout.tsx    # Root layout
│   │   └── page.tsx      # Home page
│   └── lib/
│       └── utils.ts      # Utility functions (cn, clsx, tailwind-merge)
├── public/               # Static assets
├── components.json       # shadcn/ui configuration
├── .mcp.json            # MCP server configuration
├── tsconfig.json        # TypeScript configuration
├── next.config.ts       # Next.js configuration
├── postcss.config.mjs   # PostCSS configuration
└── package.json         # Dependencies and scripts
```

## Configuration Details

### shadcn/ui Configuration
- **Style**: New York
- **Base Color**: Neutral
- **CSS Variables**: Enabled
- **RSC**: Enabled (React Server Components)
- **TypeScript**: Enabled

### Import Aliases
```typescript
{
  "@/components": "src/components",
  "@/lib": "src/lib",
  "@/utils": "src/lib/utils",
  "@/ui": "src/components/ui",
  "@/hooks": "src/hooks"
}
```

### MCP Server
The MCP (Model Context Protocol) server is configured to enable AI-assisted component development:

```json
{
  "mcpServers": {
    "shadcn": {
      "command": "npx",
      "args": ["shadcn@latest", "mcp"]
    }
  }
}
```

This allows Claude Code to directly interact with shadcn/ui to:
- Browse available components
- Search components by functionality
- Install components with proper configuration
- View component documentation

## Available Scripts

```bash
# Development server (with Turbopack)
npm run dev

# Production build (with Turbopack)
npm run build

# Start production server
npm run start
```

## Development Server

The development server runs on:
- **Local**: http://localhost:3000
- **Network**: http://192.168.1.37:3000

## Key Dependencies

### Production Dependencies
- `next`: 15.5.5
- `react`: 19.1.0
- `react-dom`: 19.1.0
- `lucide-react`: 0.545.0 (Icon library)
- `class-variance-authority`: 0.7.1 (CVA for component variants)
- `clsx`: 2.1.1 (Utility for conditionally joining classes)
- `tailwind-merge`: 3.3.1 (Merge Tailwind classes intelligently)

### Dev Dependencies
- `typescript`: 5.x
- `@tailwindcss/postcss`: 4.x
- `tailwindcss`: 4.x
- `tw-animate-css`: 1.4.0 (Animation utilities)
- `@types/node`: 20.x
- `@types/react`: 19.x
- `@types/react-dom`: 19.x

## CSS Variables

The project uses CSS variables for theming (defined in `src/app/globals.css`):

```css
:root {
  --background: ...
  --foreground: ...
  --card: ...
  --primary: ...
  --secondary: ...
  --accent: ...
  --destructive: ...
  --muted: ...
  --border: ...
  --input: ...
  --ring: ...
}
```

Dark mode is supported via the `.dark` class.

## Next Steps

### 1. Add shadcn/ui Components

Use the MCP server or CLI to add components as needed:

```bash
# Using MCP (through Claude Code)
# Just ask: "Add the Button component"

# Using CLI
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add table
npx shadcn@latest add dialog
npx shadcn@latest add form
```

### 2. Create API Layer

Create a service layer to communicate with the Python backend:

```typescript
// src/lib/api/orchestrator.ts
export async function startWorkflow(config: WorkflowConfig) {
  // API call to Python backend
}
```

### 3. Build UI Components

Key pages to build:

1. **Workflow Configuration Page**
   - Form to configure workflow name, description, CSV files, output filename
   - Uses: Form, Input, Button, Card components

2. **Planning Phase Page**
   - Display Planner questions
   - User input for answers
   - Progress indicator
   - Uses: Card, Form, Input, Progress components

3. **Plan Review Page**
   - Display Business Logic Plan
   - Approve/Request changes buttons
   - Feedback textarea
   - Uses: Card, Button, Textarea, Dialog components

4. **Code Generation Page**
   - Loading indicator during code generation
   - Display code preview
   - Uses: Card, Skeleton, Code components

5. **Output Review Page**
   - Data table showing output CSV
   - Output summary (rows, columns)
   - Refinement feedback form
   - Approve/Refine buttons
   - Uses: Table, Card, Form, Textarea, Button components

6. **Workflow Summary Page**
   - Display complete workflow summary
   - Links to generated code and output files
   - Uses: Card, Badge, Button components

### 4. State Management

Consider adding state management:

```bash
# Option 1: React Context (built-in)
# Good for simple state

# Option 2: Zustand (recommended)
npm install zustand

# Option 3: Redux Toolkit
npm install @reduxjs/toolkit react-redux
```

### 5. API Integration

Create API routes in Next.js or connect to external Python API:

```typescript
// app/api/orchestrator/route.ts
export async function POST(request: Request) {
  // Forward to Python backend
  const response = await fetch('http://localhost:8000/api/start', {
    method: 'POST',
    body: JSON.stringify(await request.json()),
  });
  return response;
}
```

### 6. Environment Variables

Create `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Other config
NEXT_PUBLIC_APP_NAME="IRA Orchestrator"
```

## Testing the Setup

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 to see the default Next.js page.

## Recommended Components to Add First

Based on the IRA Orchestrator requirements:

```bash
# Forms and inputs
npx shadcn@latest add form
npx shadcn@latest add input
npx shadcn@latest add textarea
npx shadcn@latest add button

# Layout and display
npx shadcn@latest add card
npx shadcn@latest add table
npx shadcn@latest add badge
npx shadcn@latest add progress

# Feedback and interaction
npx shadcn@latest add dialog
npx shadcn@latest add toast
npx shadcn@latest add skeleton
npx shadcn@latest add alert

# Navigation
npx shadcn@latest add tabs
npx shadcn@latest add separator
```

## Notes

- The project uses **Turbopack** for faster builds and hot reload
- **Server Components** are enabled by default (RSC)
- **TypeScript** is strictly enabled
- **CSS Variables** approach allows easy theming
- **MCP Server** enables AI-assisted development

## Support

For shadcn/ui documentation:
- Docs: https://ui.shadcn.com/docs
- Components: https://ui.shadcn.com/docs/components
- MCP: https://ui.shadcn.com/docs/mcp

For Next.js documentation:
- Docs: https://nextjs.org/docs
- Learn: https://nextjs.org/learn
- Examples: https://github.com/vercel/next.js/tree/canary/examples

---

**Setup completed on**: October 16, 2025
**Status**: Ready for development
