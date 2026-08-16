import pandas as pd
from wormcat_batch.create_wormcat_xlsx import create_category_summary, significant


def test_significant():
    assert significant(0.01) == 0.01
    assert significant(0.049) == 0.049
    assert significant(0.05) == "NS"
    assert significant(0.10) == "NS"


def test_create_category_summary():
    df = pd.DataFrame({
        "Category 1": ["Metabolism", "Stress response", "Metabolism", "Neuronal"]
    })
    summary = create_category_summary(df, "Category 1")
    assert "Category 1" in summary.columns
    assert "Count" in summary.columns
    assert len(summary) == 3
    metabolism_row = summary[summary["Category 1"] == "Metabolism"]
    assert metabolism_row["Count"].iloc[0] == 2
