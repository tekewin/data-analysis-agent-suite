# Data Analysis Agent Suite - Technical Specification

> **Mission**: Give data analysts back 1+ hour every day through AI-powered automation

---

## 1. Overview

### 1.1 Purpose
A suite of specialized AI agents designed for data analysts working in Gemini CLI. Each agent handles a specific aspect of the data analysis workflow, from cleaning raw data to producing executive-ready reports.

### 1.2 Core Value Proposition
- **Speed**: Automate time-consuming tasks (data cleaning, report writing)
- **Quality**: Consistent, professional outputs every time
- **Flexibility**: Use agents individually or chain them together

### 1.3 Target Users
- Data analysts comfortable with CLI/terminal environments
- Professionals who work primarily with CSV and Excel files
- Teams needing consistent, repeatable analysis workflows

---

## 2. Architecture

### 2.1 Agent Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ANALYSIS AGENT SUITE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   📥 INPUT                                                      │
│   └── CSV / Excel files                                         │
│                                                                 │
│   🤖 AGENTS                                                     │
│   ├── @data-cleaner      → Clean and standardize data           │
│   ├── @data-analyzer     → Explore and find insights            │
│   ├── @data-visualizer   → Create interactive Plotly charts     │
│   ├── @report-writer     → Generate detailed analytical report  │
│   └── @exec-summarizer   → Create executive summary             │
│                                                                 │
│   📤 OUTPUT                                                     │
│   ├── cleaned_data.csv                                          │
│   ├── analysis_report.md                                        │
│   ├── executive_summary.md                                      │
│   └── visualizations/*.html                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

1. **Single Responsibility**: Each agent does one thing well
2. **Loose Coupling**: Agents can run independently or together
3. **Conversational**: Agents ask clarifying questions when needed
4. **Transparent**: Agents explain what they're doing and why
5. **Collaborative**: Human stays in control, AI assists

### 2.3 Usage Modes

| Mode | Description | Example |
|------|-------------|---------|
| **À la carte** | Run single agent | `@data-cleaner sales.csv` |
| **Full pipeline** | Run all agents in sequence | `@full-analysis sales.csv` |
| **Custom combo** | Chain specific agents | `@data-cleaner` → `@data-visualizer` |

---

## 3. Agent Specifications

### 3.1 Data Cleaner Agent (`@data-cleaner`)

#### Purpose
Transform messy, inconsistent data into clean, analysis-ready datasets.

#### Input
- CSV or Excel file (`.csv`, `.xlsx`, `.xls`)
- Optional: User-specified cleaning preferences

#### Output
- `cleaned_data.csv` - Cleaned dataset
- `cleaning_report.md` - Summary of changes made

#### Capabilities

| Task | Description |
|------|-------------|
| **Duplicate Detection** | Identify and handle duplicate rows |
| **Missing Values** | Detect, report, and handle nulls/blanks |
| **Data Type Standardization** | Ensure consistent types per column |
| **Date Normalization** | Convert dates to consistent format (ISO 8601) |
| **String Cleaning** | Trim whitespace, fix encoding, standardize case |
| **Outlier Flagging** | Identify statistical outliers for review |
| **Column Name Cleanup** | Standardize column names (snake_case) |

#### Interaction Flow

```
User: @data-cleaner sales_q4.csv

Agent: 📊 Analyzing sales_q4.csv...

       I found the following issues:

       🔴 Critical:
          • 47 duplicate rows (based on all columns)
          • 'date' column has 3 different formats

       🟡 Warnings:
          • 12 missing values in 'region' column
          • 'revenue' has 3 potential outliers (>3 std dev)

       🟢 Minor:
          • Column names have inconsistent casing
          • 'customer_name' has leading/trailing whitespace

       How would you like me to handle these?

       1. Fix all automatically (recommended)
       2. Let me choose for each issue
       3. Just fix critical issues

User: 1

Agent: ✅ Done! Created:
       • cleaned_data.csv (1,247 rows)
       • cleaning_report.md (full details)

       Summary: Removed 47 duplicates, standardized dates to
       YYYY-MM-DD, filled 12 missing regions with "Unknown"
```

#### Configuration Options

```yaml
data_cleaner:
  duplicates:
    action: remove | flag | ask        # default: ask
    keep: first | last                 # default: first
  missing_values:
    numeric: mean | median | zero | drop | ask
    categorical: mode | "Unknown" | drop | ask
  dates:
    output_format: "YYYY-MM-DD"        # ISO 8601 default
  outliers:
    method: zscore | iqr              # default: zscore
    threshold: 3                       # std deviations
    action: flag | remove | ask        # default: flag
```

---

### 3.2 Data Analyzer Agent (`@data-analyzer`)

#### Purpose
Explore datasets to uncover patterns, trends, correlations, and actionable insights.

#### Input
- CSV file (ideally cleaned)
- Optional: Specific questions or areas of focus

#### Output
- `analysis_findings.md` - Detailed analysis with insights
- Console output with key discoveries

#### Capabilities

| Analysis Type | Description |
|---------------|-------------|
| **Descriptive Statistics** | Mean, median, mode, std dev, percentiles |
| **Distribution Analysis** | Shape, skewness, normality tests |
| **Correlation Discovery** | Find relationships between variables |
| **Trend Detection** | Identify time-based patterns |
| **Segmentation** | Group data by categories, find differences |
| **Anomaly Detection** | Spot unusual patterns or outliers |
| **Hypothesis Generation** | Suggest areas for deeper investigation |

#### Interaction Flow

```
User: @data-analyzer cleaned_data.csv

Agent: 🔍 Exploring your dataset...

       📋 Dataset Overview:
       • 1,247 rows × 8 columns
       • Date range: 2024-10-01 to 2024-12-31
       • Key columns: date, region, product, revenue, quantity

       🎯 Initial Findings:

       1. 📈 Revenue Trend
          Sales increased 23% from Oct → Dec
          Peak day: Black Friday ($47,230)

       2. 🗺️ Regional Patterns
          West region outperforms by 34%
          East region has highest growth rate (41%)

       3. 🔗 Interesting Correlation
          Product category strongly correlates with
          day-of-week (r=0.72) - Electronics spike on weekends

       Would you like me to:
       1. Dig deeper into any of these findings?
       2. Look for something specific?
       3. Generate the full analysis report?

User: Tell me more about the weekend electronics pattern

Agent: 🔍 Deep Dive: Weekend Electronics Pattern

       [Detailed breakdown follows...]
```

#### Analysis Depth Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Quick scan** | High-level overview, key stats | Initial exploration |
| **Standard** | Full statistical analysis | Regular analysis |
| **Deep dive** | Comprehensive with significance tests | Important decisions |

---

### 3.3 Data Visualizer Agent (`@data-visualizer`)

#### Purpose
Create beautiful, interactive visualizations using Plotly that help tell the data story.

#### Input
- CSV file (cleaned/analyzed)
- Optional: Specific visualization requests
- Optional: Analysis findings to visualize

#### Output
- `visualizations/` directory containing:
  - Interactive HTML files (one per chart)
  - `index.html` - Dashboard view of all visualizations
  - `chart_manifest.json` - Metadata about generated charts

#### Capabilities

| Chart Type | Best For |
|------------|----------|
| **Line Charts** | Time series, trends |
| **Bar Charts** | Comparisons, categories |
| **Scatter Plots** | Correlations, distributions |
| **Heatmaps** | Correlation matrices, patterns |
| **Box Plots** | Distributions, outliers |
| **Pie/Donut** | Composition, proportions |
| **Histograms** | Frequency distributions |
| **Combo Charts** | Multiple metrics together |

#### Interaction Flow

```
User: @data-visualizer cleaned_data.csv

Agent: 📊 Analyzing data for visualization opportunities...

       Based on your data, I recommend these visualizations:

       1. 📈 Revenue Over Time (Line)
          Shows the Q4 trend with weekly aggregation

       2. 📊 Revenue by Region (Bar)
          Compare regional performance

       3. 🔥 Product × Day Heatmap
          Visualize the weekend electronics pattern

       4. 📦 Revenue Distribution (Box)
          Show spread and outliers by category

       Should I:
       1. Generate all recommended charts
       2. Let me pick specific ones
       3. Create something custom

User: 1

Agent: ✅ Created 4 interactive visualizations!

       📁 visualizations/
       ├── index.html (dashboard view)
       ├── revenue_trend.html
       ├── regional_comparison.html
       ├── product_day_heatmap.html
       └── revenue_distribution.html

       Open visualizations/index.html to explore!
```

#### Styling Defaults

```yaml
visualizer:
  theme: plotly_white          # clean, professional
  color_palette:
    - "#636EFA"                # blue
    - "#EF553B"                # red
    - "#00CC96"                # green
    - "#AB63FA"                # purple
    - "#FFA15A"                # orange
  defaults:
    show_legend: true
    interactive: true
    responsive: true
    title_font_size: 18
    export_format: html
```

---

### 3.4 Report Writer Agent (`@report-writer`)

#### Purpose
Transform analysis findings into comprehensive, well-structured analytical reports.

#### Input
- Analysis findings (from `@data-analyzer` or manual input)
- Cleaned data file for reference
- Optional: Specific sections to include/exclude

#### Output
- `analysis_report.md` - Full analytical report

#### Report Structure

```markdown
# [Dataset Name] Analysis Report

## Executive Summary
[Brief overview - 2-3 paragraphs]

## 1. Introduction
### 1.1 Objective
### 1.2 Data Source
### 1.3 Methodology

## 2. Data Overview
### 2.1 Dataset Description
### 2.2 Data Quality Notes
### 2.3 Key Metrics Definitions

## 3. Key Findings
### 3.1 [Finding 1 - Most Important]
### 3.2 [Finding 2]
### 3.3 [Finding 3]
(etc.)

## 4. Detailed Analysis
### 4.1 [Analysis Area 1]
### 4.2 [Analysis Area 2]
(etc.)

## 5. Visualizations
[References to generated charts with insights]

## 6. Recommendations
### 6.1 Immediate Actions
### 6.2 Further Investigation

## 7. Appendix
### 7.1 Data Dictionary
### 7.2 Methodology Notes
### 7.3 Limitations
```

#### Interaction Flow

```
User: @report-writer

Agent: 📝 Ready to write your analysis report!

       I found these available inputs:
       • cleaned_data.csv (1,247 rows)
       • analysis_findings.md
       • 4 visualizations in /visualizations

       What's the context for this report?

       1. Who is the primary audience?
       2. What decisions will this inform?
       3. Any specific sections to emphasize?

User: Audience is the sales team. They need to understand
      Q4 performance and plan for Q1.

Agent: Got it! Sales team, Q4 review, Q1 planning focus.

       Generating report with emphasis on:
       • Actionable insights for sales strategy
       • Regional and product performance breakdown
       • Trend analysis with Q1 projections

       ✅ Created: analysis_report.md

       Key sections:
       • Executive Summary (quick wins highlighted)
       • Regional Performance Deep Dive
       • Product Category Analysis
       • Q1 Recommendations

       Would you like me to adjust anything?
```

#### Writing Style Options

| Style | Characteristics | Best For |
|-------|-----------------|----------|
| **Technical** | Precise, methodology-heavy | Data teams |
| **Business** | Insight-focused, actionable | Business users |
| **Executive** | High-level, decision-focused | Leadership |

---

### 3.5 Executive Summarizer Agent (`@exec-summarizer`)

#### Purpose
Distill complex analysis into clear, concise summaries for leadership and stakeholders.

#### Input
- Full analysis report OR analysis findings
- Optional: Specific focus areas or questions to address

#### Output
- `executive_summary.md` - 1-2 page executive summary

#### Summary Structure

```markdown
# Executive Summary: [Title]

**Date**: [Generated date]
**Period**: [Analysis period]
**Prepared for**: [Audience]

---

## Bottom Line Up Front (BLUF)
[2-3 sentences capturing the most critical insight]

## Key Metrics at a Glance
| Metric | Value | vs. Previous | Status |
|--------|-------|--------------|--------|
| ...    | ...   | ...          | 🟢/🟡/🔴 |

## Top 3 Findings

### 1. [Most Important Finding]
**Impact**: [Business impact]
**Action**: [Recommended action]

### 2. [Second Finding]
**Impact**: [Business impact]
**Action**: [Recommended action]

### 3. [Third Finding]
**Impact**: [Business impact]
**Action**: [Recommended action]

## Recommended Actions
1. [Immediate action]
2. [Short-term action]
3. [Strategic consideration]

## Risks & Considerations
- [Key risk or caveat]
- [Important limitation]

---
*Full analysis available in: analysis_report.md*
```

#### Interaction Flow

```
User: @exec-summarizer

Agent: 👔 Creating executive summary...

       Found: analysis_report.md (comprehensive report)

       Quick questions:
       1. How much time does the exec have?
          • 2 min read (half page)
          • 5 min read (1 page) ← recommended
          • 10 min read (2 pages)

       2. What's their primary concern?
          • Revenue/growth
          • Efficiency/costs
          • Market/competition
          • General overview

User: 5 min, revenue focused

Agent: ✅ Created: executive_summary.md

       Highlights:
       • BLUF: Q4 revenue up 23%, West region driving growth
       • 3 key findings with clear action items
       • Risk flag on East region inventory

       Ready for the C-suite! 👔
```

#### Summarization Principles

1. **BLUF First**: Lead with the bottom line
2. **Numbers Matter**: Include key metrics with context
3. **So What?**: Every finding needs business impact
4. **Action Oriented**: Clear next steps
5. **Visual Hierarchy**: Scannable in 30 seconds
6. **Honest Caveats**: Flag limitations upfront

---

## 4. Data Flow

### 4.1 Full Pipeline Flow

```
                    📥 INPUT
                       │
                       ▼
        ┌──────────────────────────┐
        │     @data-cleaner        │
        │  • Validate & clean      │
        │  • Output: cleaned.csv   │
        └──────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │     @data-analyzer       │
        │  • Explore & discover    │
        │  • Output: findings.md   │
        └──────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  @data-visualizer│    │  @report-writer  │
│  • Create charts │    │  • Full report   │
│  • Output: HTML  │    │  • Output: MD    │
└──────────────────┘    └──────────────────┘
          │                         │
          └────────────┬────────────┘
                       ▼
        ┌──────────────────────────┐
        │    @exec-summarizer      │
        │  • Distill insights      │
        │  • Output: summary.md    │
        └──────────────────────────┘
                       │
                       ▼
                   📤 OUTPUT
```

### 4.2 File Artifacts

| Agent | Produces | Consumes |
|-------|----------|----------|
| `@data-cleaner` | `cleaned_data.csv`, `cleaning_report.md` | Raw CSV/Excel |
| `@data-analyzer` | `analysis_findings.md` | Cleaned CSV |
| `@data-visualizer` | `visualizations/*.html` | Cleaned CSV, Findings |
| `@report-writer` | `analysis_report.md` | Findings, Visualizations |
| `@exec-summarizer` | `executive_summary.md` | Full Report |

---

## 5. Project Structure

```
data-analysis-agents/
├── .gemini/
│   └── agents/
│       ├── data-cleaner.md           # Cleaner agent prompt
│       ├── data-analyzer.md          # Analyzer agent prompt
│       ├── data-visualizer.md        # Visualizer agent prompt
│       ├── report-writer.md          # Report writer agent prompt
│       ├── exec-summarizer.md        # Exec summary agent prompt
│       └── full-analysis.md          # Pipeline orchestrator
│
├── templates/
│   ├── cleaning_report.md        # Cleaning report template
│   ├── analysis_report.md        # Full report template
│   └── executive_summary.md      # Exec summary template
│
├── examples/
│   ├── sample_data.csv           # Example input
│   └── sample_output/            # Example outputs
│       ├── cleaned_data.csv
│       ├── analysis_report.md
│       ├── executive_summary.md
│       └── visualizations/
│
├── output/                       # Default output directory
│   └── [generated files]
│
├── SPECIFICATION.md              # This document
├── TODO.md                       # Development progress
└── README.md                     # User documentation
```

---

## 6. Technical Requirements

### 6.1 Dependencies

| Tool | Purpose | Required |
|------|---------|----------|
| Python 3.9+ | Runtime | Yes |
| pandas | Data manipulation | Yes |
| plotly | Interactive visualizations | Yes |
| openpyxl | Excel file support | Yes |
| numpy | Numerical operations | Yes |
| scipy | Statistical tests | Optional |

### 6.2 Environment Setup

Agents will use Gemini CLI's ability to execute Python code for data operations. The agents will:

1. Check for required packages
2. Install missing packages if needed (with user permission)
3. Execute analysis code in a consistent environment

### 6.3 Output Formats

| Format | Use Case | Notes |
|--------|----------|-------|
| CSV | Cleaned data | UTF-8 encoding, standard delimiters |
| Markdown | Reports | GitHub-flavored markdown |
| HTML | Visualizations | Standalone, includes Plotly.js |
| JSON | Metadata | Chart manifests, configs |

---

## 7. Usage Examples

### 7.1 Quick Clean

```
User: @data-cleaner messy_sales.xlsx

[Agent cleans data, outputs cleaned_data.csv]
```

### 7.2 Full Analysis Pipeline

```
User: @full-analysis quarterly_revenue.csv

[Runs all agents in sequence, produces complete output package]
```

### 7.3 Custom Workflow

```
User: @data-cleaner inventory.csv
User: @data-visualizer cleaned_data.csv --focus "stock levels by warehouse"
User: @exec-summarizer --audience "warehouse managers"
```

### 7.4 Conversational Analysis

```
User: @data-analyzer sales.csv
Agent: [Shows initial findings]
User: What's driving the Tuesday spike?
Agent: [Deep dives into Tuesday patterns]
User: Create a viz showing that
Agent: [Generates targeted visualization]
```

---

## 8. Future Enhancements

### Phase 2: Extended Data Sources
- [ ] Direct database connections (PostgreSQL, MySQL, SQLite)
- [ ] API data fetching
- [ ] Cloud storage integration (S3, GCS)

### Phase 3: Advanced Analysis
- [ ] Predictive modeling agent
- [ ] Statistical testing agent
- [ ] Natural language querying

### Phase 4: Collaboration
- [ ] Shared analysis sessions
- [ ] Report versioning
- [ ] Team templates

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time saved | 1+ hour/day | User surveys |
| Analysis accuracy | 95%+ | Spot checks |
| User satisfaction | 4.5+/5 | Feedback |
| Adoption | 80%+ daily use | Usage tracking |

---

*Specification Version: 1.0*
*Last Updated: 2025-01-22*
