# CSV Rescue — decisions

1. **Repo root.** The Git repository *is* the product (not a nested `csv-rescue/` folder) so CI, Docker, and Render work from the clone root.
2. **Single-process apply.** Uploads run ingest + profile + detect synchronously. Files over ~80k rows still return `200` when they finish under the request timeout; a `processing` status path exists for future 202 polling.
3. **SQLAlchemy 2 not used.** Persistence uses stdlib `sqlite3` as allowed by Section 5.3.
4. **`openapi-typescript` optional.** `frontend/src/api/schema.d.ts` is maintained by hand to match Pydantic models. `npm run gen:api` copies `/api/v1/openapi.json` when the backend is running.
5. **Slowapi** is used when installed; if import fails, a no-op limiter keeps the app bootable in constrained environments.
6. **Art assets.** ClayImage SVG/CSS fallbacks ship in Phase 1. Optional WebP files can be dropped into `frontend/public/art/` later (Appendix C).
7. **Duplicate IDs.** Columns whose names match the ID regex are uniqueness-checked even when duplicates pull the distinct ratio below 0.90 (otherwise duplicate-heavy ID columns would never be flagged).
