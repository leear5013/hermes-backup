---
name: career-ops-tracker
description: Use when user asks for Application tracker viewer — read/display/update application status, statistics dashboard.
version: 1.0.0
author: Hermes Agent (ported from santifer/career-ops)
license: MIT
metadata:
  hermes:
    tags: [career-ops, job-search, career, ai]
    related_skills: [career-ops-shared]
    upstream: https://github.com/santifer/career-ops
---

# Career Ops Tracker — Career-Ops for Hermes

> **Ported from [santifer/career-ops](https://github.com/santifer/career-ops) v1.9.0.**
> This skill runs on Hermes Agent. Tool references are adapted for Hermes native tools.
> Original copyright: Santiago Fernández de Valderrama, MIT License.

Lee y muestra `data/applications.md`.

**Formato del tracker:**
```markdown
| # | Fecha | Empresa | Rol | Score | Estado | PDF | Report |
```

Estados posibles: `Evaluada` → `Aplicado` → `Respondido` → `Contacto` → `Entrevista` → `Oferta` / `Rechazada` / `Descartada` / `NO APLICAR`

- `Aplicado` = el candidato envió su candidatura
- `Respondido` = Un recruiter/empresa contactó y el candidato respondió (inbound)
- `Contacto` = El candidato contactó proactivamente a alguien de la empresa (outbound, ej: LinkedIn power move)

Si el usuario pide actualizar un estado, editar la fila correspondiente.

Mostrar también estadísticas:
- Total de aplicaciones
- Por estado
- Score promedio
- % con PDF generado
- % con report generado

