# Generating Diagrams

## Mermaid Diagrams (C4 Context and Container)

Исходные файлы диаграмм:
- `c4_context.mmd` - C4 Context diagram
- `c4_container.mmd` - C4 Container diagram

### Option 1: Automatic rendering (GitHub)

GitHub автоматически рендерит `.mmd` файлы при просмотре в браузере. Не требуется генерация PNG.

### Option 2: Generate PNG files (for course requirements)

**Требование курсовика**: Диаграммы должны быть в формате PNG (FR-005).

#### Prerequisites

1. Fix npm cache permissions (if needed):
   ```bash
   sudo chown -R 501:20 "/Users/hein/.npm"
   ```

2. Install Mermaid CLI:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

#### Generate PNG files

```bash
# From project root
cd docs/diagrams

# Generate C4 Context diagram
mmdc -i c4_context.mmd -o c4_context.png

# Generate C4 Container diagram
mmdc -i c4_container.mmd -o c4_container.png
```

#### Expected output

- `c4_context.png` - Context diagram image
- `c4_container.png` - Container diagram image

### Option 3: Online converter

Use https://mermaid.live/ to convert .mmd files to PNG:

1. Open https://mermaid.live/
2. Copy content from .mmd file
3. Paste into editor
4. Click "Download PNG"
5. Save as `c4_context.png` or `c4_container.png`

---

## Database Schema

Database schema is generated using ERAlchemy from SQLAlchemy models.

See [../database/README.md](../database/README.md) for instructions.
