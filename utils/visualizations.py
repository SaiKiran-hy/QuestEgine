import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

def generate_dataframe_preview(df: pd.DataFrame, num_rows: int = 5) -> pd.DataFrame:
    """Generate a preview of the DataFrame."""
    return df.head(num_rows)

def create_visualization(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str,
    y_column: Optional[str] = None
):
    """Create a visualization based on the specified chart type."""
    try:
        if chart_type == "bar":
            if y_column:
                fig = px.bar(df, x=x_column, y=y_column, title=f"Bar Chart: {x_column} vs {y_column}")
            else:
                fig = px.bar(df, x=x_column, title=f"Bar Chart: {x_column}")
        elif chart_type == "line":
            if y_column:
                fig = px.line(df, x=x_column, y=y_column, title=f"Line Chart: {x_column} vs {y_column}")
            else:
                fig = px.line(df, x=x_column, title=f"Line Chart: {x_column}")
        elif chart_type == "scatter":
            if y_column:
                fig = px.scatter(df, x=x_column, y=y_column, title=f"Scatter Plot: {x_column} vs {y_column}")
            else:
                raise ValueError("Scatter plot requires both x and y columns")
        elif chart_type == "pie":
            if y_column:
                fig = px.pie(df, names=x_column, values=y_column, title=f"Pie Chart: {x_column}")
            else:
                fig = px.pie(df, names=x_column, title=f"Pie Chart: {x_column}")
        elif chart_type == "histogram":
            fig = px.histogram(df, x=x_column, title=f"Histogram: {x_column}")
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Update layout for better readability
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(size=12)
        )
        
        return fig
    except Exception as e:
        raise ValueError(f"Error creating visualization: {str(e)}")