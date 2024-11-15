import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from celery.result import AsyncResult

from src.utils.logger import logger


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


class TaskIDExtractor:
    """Extract chain IDs from various result structures."""

    def __init__(self, key_name: Optional[str] = "chain_result"):
        self.collected_ids: List[str] = []
        self.key_name = key_name

    def extract_chain_ids(self, items: Any) -> List[str]:
        """
        Extract all chain IDs from the given result structure.

        Args:
            items: items structure containing task chains

        Returns:
            List of unique chain IDs
        """
        try:
            if isinstance(items, list):
                self._handle_list(items)
            elif isinstance(items, AsyncResult):
                self._handle_asyncresult(items)
            else:
                logger.error("Wrong task_id types")

        except Exception as e:
            logger.error(f"Error extracting chain IDs: {e}")

        return self.collected_ids

    def _handle_list(self, items: list) -> None:
        for subitem in items:
            if isinstance(subitem, dict) and self.key_name in subitem:
                # Get celery chain result from a dictionary
                chain_result = subitem[self.key_name]
                if isinstance(chain_result, AsyncResult):
                    self._handle_asyncresult(chain_result)

    def _handle_asyncresult(self, item: AsyncResult) -> None:
        """If result is a single AsyncResult, collect its task ID and any parent IDs"""

        # Add current task ID
        self.collected_ids.append(item.id)

        # Handle parent chain
        current = item

        while current.parent:
            if isinstance(current.parent, AsyncResult):
                self.collected_ids.append(current.parent.id)
            current = current.parent

        # Handle tuple results
        if current.result and isinstance(current.result, tuple):
            self._handle_tuple(current.result)

    def _handle_tuple(self, result_tuple: tuple) -> None:
        """
        Process task IDs if the result contains a tuple

        situation1: (uuid.UUID((uuid.UUID, None), None)
        situation2: (<AsyncResult ....>)
        """
        for task_id in result_tuple:
            if isinstance(task_id, uuid.UUID):
                self.collected_ids.append(str(task_id))

            elif isinstance(task_id, AsyncResult):
                self.collected_ids.append(task_id.id)
