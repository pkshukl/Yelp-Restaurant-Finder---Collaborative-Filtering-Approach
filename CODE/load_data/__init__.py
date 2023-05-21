import polars as pl


def pl_type_to_sqlite_type(pl_type):
    if (
        pl_type == pl.Int8
        or pl_type == pl.Int16
        or pl_type == pl.Int32
        or pl_type == pl.Int64
    ):
        return "INTEGER"
    elif (
        pl_type == pl.UInt8
        or pl_type == pl.UInt16
        or pl_type == pl.UInt32
        or pl_type == pl.UInt64
    ):
        return "INTEGER"
    elif pl_type == pl.Float32 or pl_type == pl.Float64:
        return "REAL"
    elif pl_type == pl.Boolean:
        return "INTEGER"
    elif pl_type == pl.Date32 or pl_type == pl.Date64:
        return "TEXT"
    elif pl_type == pl.Time64NS:
        return "TEXT"
    elif pl_type == pl.DurationNS:
        return "INTEGER"
    elif pl_type == pl.Object:
        return "TEXT"
    elif pl_type == pl.Categorical:
        return "TEXT"
    elif pl_type == pl.Utf8:
        return "TEXT"
    else:
        raise ValueError(f"Unsupported polars data type: {pl_type}")
