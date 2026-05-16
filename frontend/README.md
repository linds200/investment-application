# Frontend Setup Guide

This frontend is built with React + Vite and uses React Bootstrap for UI components.

## 1. Install Node.js and npm

On macOS (recommended via Homebrew):

```bash
brew install node
```

Alternative:

- Download and install from https://nodejs.org/

Verify installation:

```bash
node -v
npm -v
```

## 2. Prerequisites

- Node.js 18+ (Node.js 20+ recommended)
- npm 9+

Check versions:

```bash
node -v
npm -v
```

## 3. Install Dependencies

From the project root:

```bash
cd frontend
npm install
```

This installs all dependencies from `package.json`, including:

- `react`, `react-dom`
- `bootstrap`
- `react-bootstrap`
- `react-icons`

## 4. Bootstrap Requirements (Important)

For Bootstrap styling to work correctly, CSS must be imported in the app entry file.

This project already includes it in `src/main.jsx`:

```js
import 'bootstrap/dist/css/bootstrap.min.css'
```

If styles ever disappear, verify this import still exists.

For component usage, import from `react-bootstrap`, for example:

```js
import { Button, Alert, Modal } from 'react-bootstrap'
```

## 5. Run the Frontend

```bash
npm run dev
```

Vite will print a local URL, usually:

- `http://localhost:5173`

## 6. Backend API Proxy

The frontend sends requests to `/api/*` and Vite proxies them to:

- `http://127.0.0.1:5000`

Configured in `vite.config.js`.

Examples:

- `/api/trades/buy` -> `http://127.0.0.1:5000/trades/buy`
- `/api/trades/sell` -> `http://127.0.0.1:5000/trades/sell`

Make sure your Flask backend is running before testing buy/sell.

## 7. Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build production bundle
- `npm run preview`: Serve production build locally
- `npm run lint`: Run ESLint checks

## 8. Production Build

```bash
npm run build
npm run preview
```

## 9. Troubleshooting

### API requests fail in frontend

- Confirm backend is running on `127.0.0.1:5000`
- Confirm requests are sent to `/api/...` (not hardcoded backend URLs)
- If backend runs on a different port, update `vite.config.js` proxy target

### Frontend starts but Bootstrap styles do not apply

- Confirm `bootstrap` is installed:

```bash
npm ls bootstrap react-bootstrap
```

- Confirm `import 'bootstrap/dist/css/bootstrap.min.css'` exists in `src/main.jsx`

### Clean reinstall dependencies

```bash
rm -rf node_modules package-lock.json
npm install
```
