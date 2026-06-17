#!/usr/bin/env python3
"""Generate a clean ER diagram using matplotlib."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(-1, 17)
ax.set_ylim(-1, 10)
ax.axis("off")
fig.patch.set_facecolor("#FAFBFC")

# Colors
C_HEADER = "#1a1a2e"
C_PK = "#e74c3c"
C_FK = "#3498db"
C_FIELD = "#2c3e50"
C_LINE = "#95a5a6"
C_BG = "#ffffff"
C_BORDER = "#dee2e6"


def draw_table(ax, x, y, w, title, fields, pk=None, fks=None):
    pk = pk or ""
    fks = fks or set()
    row_h = 0.38
    header_h = 0.5
    h = header_h + len(fields) * row_h + 0.15

    # Shadow
    shadow = FancyBboxPatch((x + 0.04, y - 0.04), w, h,
                             boxstyle="round,pad=0.06", facecolor="#e0e0e0",
                             edgecolor="none", alpha=0.4, zorder=1)
    ax.add_patch(shadow)

    # Table body
    body = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.06", facecolor=C_BG,
                           edgecolor=C_BORDER, linewidth=1.5, zorder=2)
    ax.add_patch(body)

    # Header
    header = FancyBboxPatch((x, y + h - header_h), w, header_h,
                             boxstyle="round,pad=0.06", facecolor=C_HEADER,
                             edgecolor=C_HEADER, linewidth=1.5, zorder=3)
    ax.add_patch(header)
    # Cover bottom corners of header
    ax.add_patch(plt.Rectangle((x, y + h - header_h), w, header_h * 0.3,
                                facecolor=C_HEADER, edgecolor="none", zorder=3))

    ax.text(x + w / 2, y + h - header_h / 2, title,
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="white", zorder=4, family="sans-serif")

    for i, field in enumerate(fields):
        fy = y + h - header_h - (i + 0.5) * row_h - 0.07
        color = C_FIELD
        prefix = "    "
        if field == pk:
            color = C_PK
            prefix = "PK "
        elif field in fks:
            color = C_FK
            prefix = "FK "
        ax.text(x + 0.15, fy, f"{prefix}{field}", ha="left", va="center",
                fontsize=8, color=color, family="monospace", zorder=4)

    # Bottom center (for connection)
    bottom = (x + w / 2, y)
    # Top center
    top = (x + w / 2, y + h)
    return top, bottom


def draw_arrow(ax, p1, p2, label="", style="arc3,rad=0.15"):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=C_LINE, lw=1.8,
                                connectionstyle=style, shrinkA=5, shrinkB=5),
                zorder=1)
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2
    if label:
        ax.text(mx, my + 0.15, label, ha="center", va="bottom",
                fontsize=7.5, color="#7f8c8d", style="italic", zorder=4)


# Table positions
t1_top, t1_bot = draw_table(ax, 0.5, 2.5, 3.5, "job_postings",
    ["job_id", "job_title", "job_category", "experience_level",
     "years_of_experience", "education_required", "annual_salary_usd",
     "salary_min_usd", "salary_max_usd", "city", "country",
     "remote_work", "company_size", "industry", "required_skills",
     "demand_score", "posting_year", "posting_month", "is_llm_role"],
    pk="job_id")

t2_top, t2_bot = draw_table(ax, 6.5, 6.0, 2.8, "job_skills",
    ["id", "job_id", "skill"],
    pk="id", fks={"job_id"})

t3_top, t3_bot = draw_table(ax, 6.5, 3.5, 2.8, "job_categories",
    ["category", "job_count", "avg_salary", "avg_demand_score"],
    pk="category")

t4_top, t4_bot = draw_table(ax, 6.5, 1.0, 2.8, "experience_levels",
    ["level", "job_count", "avg_salary", "avg_years_experience"],
    pk="level")

t5_top, t5_bot = draw_table(ax, 11.5, 3.5, 2.8, "location_summary",
    ["country", "city", "job_count", "avg_salary"],
    pk="country")

# Relations
draw_arrow(ax, (4.0, 7.5), (6.5, 7.2), "1 : N")
draw_arrow(ax, (4.0, 5.5), (6.5, 4.8), "N : 1", style="arc3,rad=-0.1")
draw_arrow(ax, (4.0, 3.8), (6.5, 2.3), "N : 1", style="arc3,rad=-0.1")
draw_arrow(ax, (4.0, 3.2), (11.5, 4.8), "N : M", style="arc3,rad=0.2")

# Legend
legend_x, legend_y = 11.5, 8.0
ax.add_patch(FancyBboxPatch((legend_x, legend_y - 0.2), 4.5, 1.4,
             boxstyle="round,pad=0.1", facecolor="#f8f9fa", edgecolor="#dee2e6"))
ax.plot(legend_x + 0.2, legend_y + 0.9, "s", color=C_PK, markersize=8)
ax.text(legend_x + 0.5, legend_y + 0.9, "Primary Key", fontsize=8, va="center", color=C_PK)
ax.plot(legend_x + 0.2, legend_y + 0.5, "s", color=C_FK, markersize=8)
ax.text(legend_x + 0.5, legend_y + 0.5, "Foreign Key", fontsize=8, va="center", color=C_FK)
ax.plot(legend_x + 0.2, legend_y + 0.1, "s", color=C_FIELD, markersize=8)
ax.text(legend_x + 0.5, legend_y + 0.1, "Regular Field", fontsize=8, va="center", color=C_FIELD)

# Title
ax.text(8, 9.5, "AI Jobs Database - Entity Relationship Diagram",
        ha="center", va="center", fontsize=16, fontweight="bold", color=C_HEADER)
ax.text(8, 9.1, "5 tables | SQLite | Star Schema",
        ha="center", va="center", fontsize=10, color="#7f8c8d")

plt.tight_layout(pad=0.5)
output = "/home/flow/ai-jobs-data-agent/data/charts/er_diagram.png"
plt.savefig(output, dpi=180, bbox_inches="tight", facecolor="#FAFBFC")
plt.close()
print(f"ER diagram saved: {output}")
