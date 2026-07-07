# Fridge-to-Recipe 🍳

AI-powered app: snap a photo of your fridge, get 3 chef-quality recipes.

Built with Next.js 15 · MongoDB · GPT-4o Vision · shadcn/ui · TailwindCSS · framer-motion

## Setup

1. Install deps: `yarn install`
2. Copy `.env.example` to `.env` and fill in your keys
3. Make sure MongoDB is running locally (or use MongoDB Atlas URI)
4. Run: `yarn dev`
5. Open http://localhost:3000

## Endpoints

- `POST /api/vision`   — { imageBase64 } → detected ingredients
- `POST /api/recipes`  — { ingredients, preferences } → 3 recipes
- `POST /api/favorites`, `GET /api/favorites`, `DELETE /api/favorites/:id`

## Key files

- `app/page.js` — full frontend UI
- `app/api/[[...path]]/route.js` — all backend routes + LLM calls
- `app/layout.js` — root layout, dark mode, fonts

## LLM Key

The app calls the Emergent Universal LLM proxy at
`https://integrations.emergentagent.com/llm/chat/completions` using GPT-4o.
Get a key at https://emergent.sh
