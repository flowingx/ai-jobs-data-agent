#!/usr/bin/env python3
"""Generate ER diagram for the AI Jobs database."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis("off")
ax.set_title("AI Jobs Database ER Diagram", fontsize=16, fontweight="bold", pad=20)

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

def draw_table(ax, x, y, w, h, title, fields, pk_field=None, fk_fields=None):
    pk_field = pk_field or ""
    fk_fields = fk_fields or []

    header_h = h * 0.2
    row_h = (h - header_h) / max(len(fields), 1)

    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                     facecolor="#f0f4ff", edgecolor="#2c3e50", linewidth=2)
    ax.add_patch(rect)

    ax.text(x + w / 2, y + h - header_h / 2, title,
            ha="center", va="center", fontsize=11, fontweight="bold",
            color="white", bbox=dict(boxstyle="round,pad=0.3", facecolor="#2c3e50", edgecolor="none"))

    for i, field in enumerate(fields):
        fy = y + h - header_h - (i + 0.5) * row_h
        prefix = ""
        color = "#333333"
        if field == pk_field:
            prefix = "PK  "
            color = "#c0392b"
        elif field in fk_fields:
            prefix = "FK  "
            color = "#2980b9"
        ax.text(x + 0.15, fy, f"{prefix}{field}", ha="left", va="center",
                fontsize=8.5, color=color, family="monospace")

    return (x + w / 2, y), (x + w / 2, y + h)


def draw_relation(ax, start, end, label, start_side="bottom", end_side="top"):
    sx, sy = start
    ex, ey = end

    if start_side == "bottom":
        sy = start[1]
    elif start_side == "top":
        sy = start[1]
    elif start_side == "right":
        sx = start[0]
    elif start_side == "left":
        sx = start[0]

    if end_side == "top":
        ey = end[1]
    elif end_side == "bottom":
        ey = end[1]
    elif end_side == "left":
        ex = end[0]
    elif end_side == "right":
        ex = end[0]

    ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(arrowstyle="-|>", color="#7f8c8d", lw=1.5,
                                connectionstyle="arc3,rad=0"))

    mx, my = (sx + ex) / 2, (sy + ey) / 2
    ax.text(mx + 0.1, my, label, ha="left", va="center",
            fontsize=8, color="#7f8c8d", style="italic")


draw_table(ax, 0.5, 4.5, 3.2, 3.0, "job_postings",
           ["job_id", "job_title", "job_category", "experience_level",
            "years_of_experience", "education_required", "annual_salary_usd",
            "salary_min_usd", "salary_max_usd", "city", "country",
            "remote_work", "company_size", "industry", "required_skills",
            "ai_salary_premium_pct", "demand_score", "posting_year",
            "posting_month", "is_llm_role", "salary_tier"],
           pk_field="job_id")

draw_table(ax, 5.5, 5.5, 2.5, 1.5, "job_skills",
           ["id", "job_id", "skill"],
           pk_field="id", fk_fields=["job_id"])

draw_table(ax, 5.5, 3.0, 2.5, 1.2, "job_categories",
           ["category", "job_count", "avg_salary", "avg_demand_score"],
           pk_field="category")

draw_table(ax, 5.5, 1.2, 2.5, 1.2, "experience_levels",
           ["level", "job_count", "avg_salary", "avg_years_experience"],
           pk_field="level")

draw_table(ax, 9.5, 3.0, 2.8, 1.2, "location_summary",
           ["country", "city", "job_count", "avg_salary"],
           pk_field="country")


draw_relation(ax, (3.7, 6.0), (5.5, 6.5), "1 : N", "right", "left")
draw_relation(ax, (3.7, 5.5), (5.5, 3.6), "N : 1\n(agg)", "right", "left")
draw_relation(ax, (3.7, 5.0), (5.5, 1.8), "N : 1\n(agg)", "right", "left")
draw_relation(ax, (3.7, 4.8), (9.5, 3.6), "N : M\n(agg)", "right", "left")

ax.text(7, 0.3, "PK = Primary Key (red)    FK = Foreign Key (blue)\n"
        "job_skills.job_id -> job_postings.job_id (FK)\n"
        "Other 3 tables are pre-aggregated summaries from job_postings GROUP BY",
        ha="center", va="center", fontsize=8.5, color="#555555",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fafafa", edgecolor="#cccccc"))

plt.tight_layout()
output = "/home/flow/ai-jobs-data-agent/data/charts/er_diagram.png"
plt.savefig(output, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"ER diagram saved: {output}")
