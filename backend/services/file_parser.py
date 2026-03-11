"""
File Parser Service
Handles parsing of CSV and XLSX files into pandas DataFrames.
Includes validation for file type, size, and structure.
"""

import io
import pandas as pd
from fastapi import UploadFile, HTTPException

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


async def validate_file(file: UploadFile) -> bytes:
    """Validate uploaded file type and size."""
    # Check file extension
    filename = file.filename or ""
    extension = ""
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{extension}'. Only .csv and .xlsx files are allowed.",
        )

    # Read and check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    return content


def parse_file(content: bytes, filename: str) -> pd.DataFrame:
    """Parse file content into a pandas DataFrame."""
    extension = ""
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[1].lower()

    try:
        if extension == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif extension == ".xlsx":
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse file: {str(e)}",
        )

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains no data.")

    if len(df.columns) < 2:
        raise HTTPException(
            status_code=400,
            detail="The file must contain at least 2 columns for meaningful analysis.",
        )

    return df


def dataframe_to_summary_text(df: pd.DataFrame) -> str:
    """Convert a DataFrame into a text summary suitable for LLM input."""
    lines = []
    lines.append(f"Dataset Overview: {len(df)} rows × {len(df.columns)} columns")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("")

    # Column types and stats
    lines.append("Column Details:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        if pd.api.types.is_numeric_dtype(df[col]):
            lines.append(
                f"  - {col} ({dtype}): min={df[col].min()}, max={df[col].max()}, "
                f"mean={df[col].mean():.2f}, nulls={null_count}"
            )
        else:
            unique = df[col].nunique()
            lines.append(f"  - {col} ({dtype}): {unique} unique values, nulls={null_count}")
            # Show top values for categorical columns
            if unique <= 10:
                top_vals = df[col].value_counts().head(5).to_dict()
                lines.append(f"    Top values: {top_vals}")

    lines.append("")

    # Include first few rows as sample data
    sample_size = min(15, len(df))
    lines.append(f"Sample Data (first {sample_size} rows):")
    lines.append(df.head(sample_size).to_string(index=False))

    # Basic aggregation hints
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        lines.append("")
        lines.append("Numeric Summary Statistics:")
        lines.append(df[numeric_cols].describe().to_string())

    return "\n".join(lines)
