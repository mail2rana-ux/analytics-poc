# Analytics Query Examples

This document provides example queries and their expected results for the analytics system.

## 1. Badge-Specific Queries

### Query: "How many people are enrolled in the Python Master badge?"
Expected Response:
- Total enrollment count
- Completion rate
- Bar chart showing enrollments vs completions
- Trend over time (if available)

Example:
```json
{
    "response": "The Python Master badge currently has 8 enrollments with a 75% completion rate (6 completions).",
    "type": "analytics",
    "metadata": {
        "badge_stats": {
            "total_enrollments": 8,
            "completed": 6,
            "completion_rate": 75.0
        }
    },
    "visualization": "bar_chart_data"
}
```

## 2. Organization-Specific Queries

### Query: "What's the enrollment trend for Tech Corp?"
Expected Response:
- Monthly enrollment numbers
- Line chart showing trend
- Comparison with overall average

Example:
```json
{
    "response": "Tech Corp has shown a steady increase in enrollments over the past 6 months, with a peak of 12 new enrollments in July 2025.",
    "type": "analytics",
    "metadata": {
        "monthly_stats": [
            {"month": "2025-03", "enrollments": 5},
            {"month": "2025-04", "enrollments": 7},
            {"month": "2025-05", "enrollments": 8},
            {"month": "2025-06", "enrollments": 10},
            {"month": "2025-07", "enrollments": 12}
        ]
    },
    "visualization": "line_chart_data"
}
```

## 3. Multi-Dimensional Queries

### Query: "How many people from Education Plus are enrolled in Data Science Pro?"
Expected Response:
- Specific count
- Completion rate for this combination
- Comparison with other organizations

Example:
```json
{
    "response": "Education Plus has 5 employees enrolled in the Data Science Pro badge, with a 60% completion rate. This is above the average completion rate of 45% across all organizations for this badge.",
    "type": "analytics",
    "metadata": {
        "org_badge_stats": {
            "enrollments": 5,
            "completed": 3,
            "completion_rate": 60.0,
            "avg_completion_rate": 45.0
        }
    },
    "visualization": "comparison_chart_data"
}
```

## 4. Temporal Queries

### Query: "Show me the enrollment trends over the last 6 months"
Expected Response:
- Monthly trends
- Multiple line chart for all badges
- Peak enrollment periods

Example:
```json
{
    "response": "Over the last 6 months, we've seen a total of 45 new enrollments across all badges. The most active month was July 2025 with 15 new enrollments.",
    "type": "analytics",
    "metadata": {
        "trend_data": {
            "total_enrollments": 45,
            "peak_month": "2025-07",
            "peak_count": 15
        }
    },
    "visualization": "trend_chart_data"
}
```

## 5. Comparative Queries

### Query: "Which badges have the highest completion rates?"
Expected Response:
- Ranked list of badges
- Completion rates
- Bar chart comparison

Example:
```json
{
    "response": "The top 3 badges by completion rate are:\n1. Python Master (85%)\n2. Cloud Expert (78%)\n3. Data Science Pro (72%)",
    "type": "analytics",
    "metadata": {
        "completion_rates": [
            {"badge": "Python Master", "rate": 85.0},
            {"badge": "Cloud Expert", "rate": 78.0},
            {"badge": "Data Science Pro", "rate": 72.0}
        ]
    },
    "visualization": "ranking_chart_data"
}
```

## 6. Learning Path Analysis

### Query: "What are the most common learning paths?"
Expected Response:
- Common badge combinations
- Sequential patterns
- Sankey diagram

Example:
```json
{
    "response": "The most common learning path is Python Master → Data Science Pro → AI Developer, followed by 35% of users who complete multiple badges.",
    "type": "analytics",
    "metadata": {
        "learning_paths": [
            {
                "path": ["Python Master", "Data Science Pro", "AI Developer"],
                "frequency": 35
            }
        ]
    },
    "visualization": "sankey_diagram_data"
}
```

## Performance Considerations

Each query type has been optimized for:
- Response time < 2 seconds
- Accurate data aggregation
- Relevant visualizations
- Contextual insights

## Visualization Types

The system supports multiple visualization types:
1. Bar Charts (enrollment comparisons)
2. Line Charts (trends over time)
3. Heatmaps (completion rates by organization/badge)
4. Sankey Diagrams (learning paths)
5. Scatter Plots (correlation analysis)

## Best Practices

When querying the system:
1. Be specific with badge and organization names
2. Specify time ranges when relevant
3. Use natural language phrasing
4. Consider including comparison requests
