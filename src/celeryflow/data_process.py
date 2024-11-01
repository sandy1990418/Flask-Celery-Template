from typing import Dict

import pandas as pd

from src.utils import logger  # , yaml_data


class DataFrameSerializer:
    """Mixin for DataFrame serialization and deserialization operations.

    Provides utilities to convert pandas DataFrames to/from dictionary format
    for storage and transmission while preserving structure and metadata.
    """

    def serialize_dataframe(self, df: pd.DataFrame) -> Dict:
        """Convert DataFrame to dictionary format.

        Args:
            df: pandas DataFrame to serialize

        Returns:
            Dict containing DataFrame data, columns, and index

        Raises:
            Exception: If serialization fails
        """
        try:
            data = {
                "data": df.to_dict("records"),
                "columns": df.columns.tolist(),
                "index": df.index.tolist(),
            }
            logger.info(f"Serialized DataFrame with {len(data['data'])} records")
            return data
        except Exception as e:
            logger.error(f"Error serializing DataFrame: {e}")
            raise

    def deserialize_dataframe(self, data: Dict) -> pd.DataFrame:
        """Reconstruct DataFrame from dictionary format.

        Args:
            data: Dictionary containing DataFrame components

        Returns:
            Reconstructed pandas DataFrame

        Raises:
            ValueError: If data format is invalid
        """
        try:
            logger.info(f"Deserializing DataFrame with {len(data['data'])} records")
            df = pd.DataFrame(data["data"], columns=data["columns"])
            if len(data["index"]) == len(df):
                df.index = pd.Index(data["index"])
            return df
        except Exception as e:
            logger.error(f"Failed to deserialize DataFrame: {e}")
            raise ValueError("Invalid DataFrame data format")
