# import boto3
# from botocore.client import Config
# from botocore import UNSIGNED


# def get_s3_object(s3_bucket, s3_key, use_credentials=False):
#     # Set up the S3 client
#     if use_credentials:
#         s3 = boto3.client("s3")
#     else:
#         s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

#     # Get the object from the S3 bucket
#     obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
#     return obj["Body"].read().decode("utf-8")

# def read_flattened_json_from_s3(bucket: str, key: str):
#     fs = s3fs.S3FileSystem(anon=True)
#     with fs.open(f"s3://{bucket}/{key}", "rb") as f:
#         df = pl.read_json(f)
#     return df.flatten()

from typing import Iterator

import polars as pl


def read_flattened_json_from_local(
    file_path: str, chunksize: int = 10000
) -> Iterator[pl.DataFrame]:
    dfs = []

    with open(file_path, "r") as f:
        for line_number, line in enumerate(f):
            json_data = line.strip()
            if json_data:  # To avoid empty lines
                df_line = pl.read_json(json_data)
                dfs.append(df_line)

            if (line_number + 1) % chunksize == 0:
                df_chunk = pl.concat(dfs)
                dfs = []  # Reset the list for the next chunk
                yield df_chunk

        # Yield the last chunk if there are remaining lines
        if dfs:
            df_chunk = pl.concat(dfs)
            yield df_chunk
