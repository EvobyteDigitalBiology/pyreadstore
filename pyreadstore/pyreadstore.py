# pyreadstore/pyreadstore.py

# Copyright 2024 EVOBYTE Digital Biology Dr. Jonathan Alles
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides Client class and methods for pyreadstore SDK.

Classes:
    - RSClient: Provides client for interacting with ReadStore API

"""


import os
import configparser
import pandas as pd
from pydantic import BaseModel
from typing import List

from pyreadstore import rsclient
from pyreadstore import rsexceptions
from pyreadstore import rsdataclasses

from pyreadstore.__version__ import __version__


class Client:
    """
    A client for interacting with the ReadStore API

    Globals:
        RETURN_TYPES: List of valid return types

    Attributes:
        config_dir: Path to dir containing config
        username: ReadStore username
        token: ReadStore user token
        host: Hostname of ReadStore server endpoint
        return_type: Default return type of requests, e.g. 'pandas'
        port: Port of ReadStore server
        fastq_extensions: List of valid fastq extensions for upload

    Methods:
        _convert_json_to_pandas: Convert JSON data to pandas DataFrame or Series
        _check_return_type: Check if return type is valid
        get_return_type: Get return type
        list: List Datasets
        list_metadata: List Metadata for Datasets
        get: Get Dataset
        create: Create Dataset
        update: Update Dataset
        delete: Delete Dataset
        get_fastq: Get FASTQ files
        download_attachment: Download Dataset attachment
        list_projects: List Projects
        list_projects_metadata: List Metadata for Projects
        get_project: Get Project
        create_project: Create Project
        update_project: Update Project
        delete_project: Delete Project
        download_project_attachment: Download Project attachment
        upload_fastq: Upload FASTQ files
        list_pro_data: List Processed Data
        list_pro_data_metadata: List Metadata for Processed Data
        get_pro_data: Get Processed Data
        upload_pro_data: Upload Processed Data
        delete_pro_data: Delete Processed Data
    """

    RETURN_TYPES = ["pandas", "json"]

    def __init__(
        self,
        config_dir: str = "~/.readstore",
        username: str | None = None,
        token: str | None = None,
        host: str = "http://localhost",
        return_type: str = "pandas",
        port: int = 8000,
        fastq_extensions: List[str] = [".fastq", ".fastq.gz", ".fq", ".fq.gz"],
    ):
        """Client constructor

        Initialize the ReadStore Client and validate connection and credentials

        Args:
            config_dir: Path to dir containing config. Defaults to '~/.readstore'.
            username: Username. Defaults to None.
            token: User Token. Defaults to None.
            host: Host address. Defaults to 'http://localhost'.
            return_type: Default return type. Defaults to 'pandas'.
            port: ReadStore Server port. Defaults to 8000.
            fastq_extensions: Allowed extensions to fastq.
                Defaults to ['.fastq','.fastq.gz','.fq','.fq.gz'].

        Raises:
            rsexceptions.ReadStoreError: User name and token must be provided
            rsexceptions.ReadStoreError: Config file not found
        """

        # Check valid return types
        self._check_return_type(return_type)
        self.return_type = return_type

        # If username & token provided, use them to initialize the client
        if username and token:
            endpoint_url = f"{host}:{port}"
        elif username or token:
            raise rsexceptions.ReadStoreError(
                "Both Username and Token must be provided"
            )
        # Case load config from files
        # TODO Add support for ENV variables ONLY
        else:
            if "~" in config_dir:
                config_dir = os.path.expanduser(config_dir)
            else:
                config_dir = os.path.abspath(config_dir)

            config_path = os.path.join(config_dir, "config")
            if not os.path.exists(config_path):
                raise rsexceptions.ReadStoreError(
                    f"Config file not found at {config_dir}"
                )

            rs_config = configparser.ConfigParser()
            rs_config.read(config_path)

            username = rs_config.get("credentials", "username", fallback=None)
            token = rs_config.get("credentials", "token", fallback=None)
            endpoint_url = rs_config.get("general", "endpoint_url", fallback=None)
            fastq_extensions = rs_config.get(
                "general", "fastq_extensions", fallback=None
            )
            # fastq_extensions = fastq_extensions.split(',')

        # Check if ENV variables are set
        # Overwrite config if found
        if "READSTORE_USERNAME" in os.environ:
            username = os.environ["READSTORE_USERNAME"]
        if "READSTORE_TOKEN" in os.environ:
            token = os.environ["READSTORE_TOKEN"]
        if "READSTORE_ENDPOINT_URL" in os.environ:
            endpoint_url = os.environ["READSTORE_ENDPOINT_URL"]
        if "READSTORE_FASTQ_EXTENSIONS" in os.environ:
            fastq_extensions = os.environ["READSTORE_FASTQ_EXTENSIONS"]
            fastq_extensions = fastq_extensions.split(",")

        self.fastq_extensions = fastq_extensions

        # Initialize the client
        self.rs_client = rsclient.RSClient(
            username, token, endpoint_url, output_format="csv"
        )

    def _convert_json_to_pandas(
        self, json_data: List[dict] | dict, validation_class: BaseModel
    ) -> pd.DataFrame | pd.Series:
        """_convert_json_to_pandas

        Convert JSON data to pandas DataFrame or Series

        Args:
            json_data: List or dict of JSON data
            validation_class: Pydantic validation class

        Raises:
            rsexceptions.ReadStoreError: Invalid JSON data

        Returns:
            pd.DataFrame | pd.Series: Pandas DataFrame or Series
        """

        if isinstance(json_data, dict):
            if json_data == {}:
                return pd.Series()
            else:
                data = validation_class(**json_data)
                return pd.Series(data.model_dump())

        elif isinstance(json_data, list):
            # Data validation using pydantic
            data = [validation_class(**ele) for ele in json_data]

            if data == []:
                df = pd.DataFrame(columns=validation_class.model_fields.keys())
            else:
                df = pd.DataFrame([ele.model_dump() for ele in data])

            return df
        else:
            raise rsexceptions.ReadStoreError("Invalid JSON data")

    def _check_return_type(self, return_type: str):
        """_check_return_type

        Check if return type is valid

        Args:
            return_type: Return type

        Raises:
            rsexceptions.ReadStoreError: Invalid return type
        """

        if return_type not in Client.RETURN_TYPES:
            raise rsexceptions.ReadStoreError(
                f"Invalid return type. Must be in {Client.RETURN_TYPES}"
            )

    def get_return_type(self) -> str:
        """get_return_type"""
        return self.return_type

    def list(
        self,
        project_id: int | None = None,
        project_name: str | None = None,
        return_type: str | None = None,
    ) -> pd.DataFrame | List[dict]:
        """List ProData

        Args:
            project_id: Filter by project_id. Defaults to None.
            project_name: Filter by project_name. Defaults to None.
            return_type: Specify return type. Default use return type from object.

        Returns:
            pd.DataFrame | List[dict]: List of ProData
        """

        if return_type:
            self._check_return_type(return_type)
        else:
            return_type = self.return_type

        fq_datasets = self.rs_client.list_fastq_datasets(
            project_id=project_id, project_name=project_name
        )

        if return_type == "pandas":
            fq_datasets = self._convert_json_to_pandas(
                fq_datasets, rsdataclasses.RSFqDataset
            )

        return fq_datasets

    def list_metadata(
        self, project_id: int | None = None, project_name: str | None = None
    ) -> pd.DataFrame:
        """List Metadata

        Extract metadata from datasets and return as 
        DataFrame with metadata keys as columns
        Non-existent metadata value will be filled with NaN
        Order of returned dataframe will be consistent with Dataset list operation

        Args:
            project_id: Filter by project_id. Defaults to None.
            project_name: Filter by project_name. Defaults to None.

        Returns:
            pd.DataFrame: Metadata with metadata keys as columns or empty DataFrame
        """

        fq_datasets = self.list(
            project_id=project_id, project_name=project_name, return_type="pandas"
        )

        if fq_datasets.empty:
            return pd.DataFrame()
        else:
            metadata = fq_datasets["metadata"].apply(pd.Series)
            return metadata

    def get(
        self,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        return_type: str | None = None,
    ) -> pd.Series | dict:
        """Get Dataset

        Args:
            dataset_id: Select by ID. Defaults to None.
            dataset_name: Select by Name. Defaults to None.
            return_type: Specify return type. Default return type from Client instance.
                Options: 'pandas', 'json'

        Raises:
            rsexceptions.ReadStoreError: Either dataset_id or dataset_name not provided

        Returns:
            pd.Series | dict: Dataset
        """

        if (dataset_id is None) and (dataset_name is None):
            raise rsexceptions.ReadStoreError(
                "Either dataset_id or dataset_name must be provided"
            )

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        fq_dataset = self.rs_client.get_fastq_dataset(
            dataset_id=dataset_id, dataset_name=dataset_name
        )

        if return_type == "pandas":
            fq_dataset = self._convert_json_to_pandas(
                fq_dataset, rsdataclasses.RSFqDatasetDetail
            )

        return fq_dataset

    def create(
        self,
        dataset_name: str,
        description: str = "",
        project_ids: List[int] = [],
        project_names: List[str] = [],
        metadata: dict = {},
    ):
        """Create an empty Dataset

        Create an empty dataset with the specified name, description and metadata
        and attach it to the specified projects.

        Args:
            name: Set name
            description: Set description. Defaults to ''.
            project_ids: Set project_ids. Defaults to [].
            project_names: Set project_names. Defaults to [].
            metadata: Set metadata. Defaults to {}.

        Raises:
            rsexceptions.ReadStoreError: Dataset with name {name} already exists
            rsexceptions.ReadStoreError: Project with id {pid} not found
            rsexceptions.ReadStoreError: Project with name {pname} not found
            rsexceptions.ReadStoreError: Metadata not valid
        """

        # Should return empty pd.Series if dataset not found
        dataset_check = self.get(dataset_name=dataset_name)

        # Check if pd.Series is empty
        if not dataset_check.empty:
            raise rsexceptions.ReadStoreError(
                f"Dataset with name {dataset_name} already exists"
            )

        # Check if project_ids and names exist
        for pid in project_ids:
            project_check = self.get_project(project_id=pid)
            if project_check.empty:
                raise rsexceptions.ReadStoreError(f"Project with id {pid} not found")
        # Check if project names exist
        for pname in project_names:
            project_check = self.get_project(project_name=pname)
            if project_check.empty:
                raise rsexceptions.ReadStoreError(
                    f"Project with name {pname} not found"
                )

        self.rs_client.create_fastq_dataset(
            name=dataset_name,
            description=description,
            qc_passed=False,
            paired_end=False,
            index_read=False,
            project_ids=project_ids,
            project_names=project_names,
            metadata=metadata,
            fq_file_i1_id=None,
            fq_file_i2_id=None,
            fq_file_r1_id=None,
            fq_file_r2_id=None,
        )

    def update(
        self,
        dataset_id: int,
        dataset_name: str | None = None,
        description: str | None = None,
        project_ids: List[int] | None = None,
        project_names: List[str] | None = None,
        metadata: dict | None = None,
    ):
        """Update Dataset

        Update attributes of a Dataset
        Dataset ID must be provided to identify the dataset to update.
        If no update values are provided, existing values will be maintained.

        Args:
            dataset_id: Dataset ID to update
            dataset_name: Updated Dataset name. Defaults to None.
            description: Updated description. Defaults to None.
            project_ids: Updated Project IDs. Defaults to None.
            project_names: Updated Project Names. Defaults to None.
            metadata: Updated Metadata. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Dataset not found
            rsexceptions.ReadStoreError: Project with defined id not found
            rsexceptions.ReadStoreError: Project with defined name not found
        """

        # Get the dataset // pop id
        dataset = self.get(dataset_id=dataset_id, return_type="json")

        if dataset == {}:
            raise rsexceptions.ReadStoreError("Dataset not found")
        
        project_ids_new = None
        project_names_new = None
        
        # If both project_ids and project_names are None, take over existing values
        if (project_ids is None) and (project_names is None):
            project_ids_new = dataset["project_ids"]
            project_names_new = dataset["project_names"]
        
        # Check if project_ids and names exist
        # Project IDs and Names can be None, Empty list of None (ignore)
        # In None case use existing values
        if project_ids:
            for pid in project_ids:
                project_check = self.get_project(project_id=pid)
                if project_check.empty:
                    raise rsexceptions.ReadStoreError(
                        f"Project with id {pid} not found"
                    )
            else:
                project_ids_new = project_ids
            
        # Check if project names exist
        if project_names:
            for pname in project_names:
                project_check = self.get_project(project_name=pname)
                if project_check.empty:
                    raise rsexceptions.ReadStoreError(
                        f"Project with name {pname} not found"
                    )
            else:
                project_names_new = project_names
        
        if project_ids_new is None:
            project_ids_new = []
        if project_names_new is None:
            project_names_new = []
        
        # Create new dataset update dict
        # If update values are defined, use them, else use existing values
        dataset_update = {
            "dataset_id": dataset_id,
            "name": dataset_name if dataset_name else dataset["name"],
            "description": description if description else dataset["description"],
            "project_ids": project_ids_new,
            "project_names": project_names_new,
            "metadata": metadata if metadata else dataset["metadata"],
            "qc_passed": dataset["qc_passed"],
            "paired_end": dataset["paired_end"],
            "index_read": dataset["index_read"],
            "fq_file_i1_id": dataset["fq_file_i1"],
            "fq_file_i2_id": dataset["fq_file_i2"],
            "fq_file_r1_id": dataset["fq_file_r1"],
            "fq_file_r2_id": dataset["fq_file_r2"],
        }

        print(dataset_update)
        
        self.rs_client.update_fastq_dataset(**dataset_update)


    def delete(self, dataset_id: int | None = None, dataset_name: str | None = None):
        """Delete Dataset

        Delete dataset by ID or Name. Either must be provided.

        Args:
            dataset_id: Delete by ID. Defaults to None.
            dataset_name: Delete by Name. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Either dataset_id or dataset_name not provided
            rsexceptions.ReadStoreError: Dataset not found
        """

        if (dataset_id is None) and (dataset_name is None):
            raise rsexceptions.ReadStoreError(
                "Either dataset_id or dataset_name must be provided"
            )

        if dataset_id:
            dataset = self.get(dataset_id=dataset_id)
            if dataset.empty:
                raise rsexceptions.ReadStoreError("Dataset not found")
        if dataset_name:
            dataset = self.get(dataset_name=dataset_name)
            if dataset.empty:
                raise rsexceptions.ReadStoreError("Dataset not found")
            else:
                dataset_id = int(dataset["id"])

        self.rs_client.delete_fastq_dataset(dataset_id)

    def get_fastq(
        self,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        return_type: str | None = None,
    ) -> pd.DataFrame | List[dict]:
        """Get FASTQ files

        Get FASTQ files by dataset_id or dataset_name

        Args:
            dataset_id: Select by ID. Defaults to None.
            dataset_name: Select by Name. Defaults to None.
            return_type: Specify return type. Default use return type from object.

        Raises:
            rsexceptions.ReadStoreError: Either id or name must be provided

        Returns:
            pd.DataFrame | List[dict]: FASTQ files
        """

        if (dataset_id is None) and (dataset_name is None):
            raise rsexceptions.ReadStoreError("Either id or name must be provided")

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        fq_dataset = self.rs_client.get_fastq_dataset(
            dataset_id=dataset_id, dataset_name=dataset_name
        )

        # Check if the dataset was found
        if fq_dataset == {}:
            if return_type == "pandas":
                return_cols = rsdataclasses.RSFqFile.model_fields.keys()
                return pd.DataFrame(columns=return_cols)
            else:
                return []
        else:
            fq_dataset = rsdataclasses.RSFqDatasetDetail(**fq_dataset)

            fq_file_ids = [
                fq_dataset.fq_file_r1,
                fq_dataset.fq_file_r2,
                fq_dataset.fq_file_i1,
                fq_dataset.fq_file_i2,
            ]

            fq_file_ids = [int(e) for e in fq_file_ids if e is not None]

            fq_files = [
                self.rs_client.get_fq_file(fq_file_id) for fq_file_id in fq_file_ids
            ]

            if return_type == "pandas":
                fq_files = self._convert_json_to_pandas(
                    fq_files, rsdataclasses.RSFqFile
                )

            return fq_files

    def download_attachment(
        self,
        attachment_name: str,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        outpath: str | None = None,
    ):
        """Download attachment

        Specify dataset_id or dataset_name

        Args:
            attachment_name: Select attachment by name
            dataset_id: Select Dataset by ID. Defaults to None.
            dataset_name: Select Dataset by Name. Defaults to None.
            outpath: Set outpath. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Dataset not found
            rsexceptions.ReadStoreError: Attachment not found
            rsexceptions.ReadStoreError: Output directory does not exist
        """

        if (dataset_id is None) and (dataset_name is None):
            raise rsexceptions.ReadStoreError("Either id or name must be provided")

        fq_dataset = self.rs_client.get_fastq_dataset(
            dataset_id=dataset_id, dataset_name=dataset_name
        )

        # Check if the dataset was found
        if fq_dataset == {}:
            raise rsexceptions.ReadStoreError("Dataset not found")

        fq_dataset = rsdataclasses.RSFqDatasetDetail(**fq_dataset)
        attachments = fq_dataset.attachments

        if attachment_name not in attachments:
            raise rsexceptions.ReadStoreError("Attachment not found")
        else:
            if outpath is None:
                outpath = os.getcwd()
                outpath = os.path.join(outpath, attachment_name)

            output_dirname = os.path.dirname(outpath)
            if (output_dirname != "") and (not os.path.exists(output_dirname)):
                raise rsexceptions.ReadStoreError(
                    f"Output directory {output_dirname} does not exist"
                )

            self.rs_client.download_fq_dataset_attachment(
                attachment_name, outpath, dataset_id, dataset_name
            )

    def list_projects(
        self, return_type: str | None = None
    ) -> pd.DataFrame | List[dict]:
        """List Projects

        Args:
            return_type: Define return type. Defaults to None.

        Returns:
            pd.DataFrame | List[dict]: Projects
        """

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        projects = self.rs_client.list_projects()

        if return_type == "pandas":
            projects = self._convert_json_to_pandas(projects, rsdataclasses.RSProject)

        return projects

    def list_projects_metadata(self) -> pd.DataFrame:
        """List Projects Metadata

        Returns:
            pd.DataFrame: Projects Metadata with metadata keys as columns
        """

        projects = self.list_projects(return_type="pandas")

        if projects.empty:
            return pd.DataFrame()
        else:
            metadata = projects["metadata"].apply(pd.Series)
            return metadata

    def get_project(
        self,
        project_id: int | None = None,
        project_name: str | None = None,
        return_type: str | None = None,
    ) -> pd.Series | dict:
        """Get Project

        Args:
            project_id: Project ID. Defaults to None.
            project_name: Project Name. Defaults to None.
            return_type: Specify return type. Default return type from Client instance.
                Options: 'pandas', 'json'

        Raises:
            rsexceptions.ReadStoreError: If project_id and project_name are not provided

        Returns:
            pd.Series | dict: Project
        """

        if (project_id is None) and (project_name is None):
            raise rsexceptions.ReadStoreError(
                "Either project_id or project_name must be provided"
            )

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        project = self.rs_client.get_project(
            project_id=project_id, project_name=project_name
        )

        if return_type == "pandas":
            project = self._convert_json_to_pandas(
                project, rsdataclasses.RSProjectDetail
            )

        return project

    def create_project(
        self,
        project_name: str,
        description: str = "",
        metadata: dict = {},
        dataset_metadata_keys: List[str] = [],
    ):
        """Create Project

        Create a new project

        Args:
            name: Set Project name
            description: Set Project description. Defaults to ''.
            metadata: Set Project metadata. Defaults to {}.
            dataset_metadata_keys: Set dataset metadata keys. Defaults to [].

        Raises:
            rsexceptions.ReadStoreError: Project with name {name} already exists
            rsexceptions.ReadStoreError: Invalid metadata or dataset_metadata_keys
        """

        # Check if project with name already exists
        project_check = self.get_project(project_name=project_name)
        if not project_check.empty:
            raise rsexceptions.ReadStoreError(
                f"Project with name {project_name} already exists"
            )

        self.rs_client.create_project(
            project_name, description, metadata, dataset_metadata_keys
        )

    def update_project(
        self,
        project_id: int,
        project_name: str | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        dataset_metadata_keys: List[str] | None = None,
    ):
        """Update Project

        Update Project attributes
        Project ID must be provided to identify the Project to update.
        If no update values are provided, existing values will be maintained.

        Args:
            project_id: Project ID to update
            project_name: Updated Project name. Defaults to None.
            description: Updated description. Defaults to None.
            metadata: Updated metadata. Defaults to None.
            dataset_metadata_keys: Updated Metadata Keys. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Project not found
        """

        project = self.get_project(project_id=project_id, return_type="json")

        if project == {}:
            raise rsexceptions.ReadStoreError("Project not found")

        project_update = {
            "project_id": project_id,
            "name": project_name if project_name else project["name"],
            "description": description if description else project["description"],
            "metadata": metadata if metadata else project["metadata"],
            "dataset_metadata_keys": (
                dataset_metadata_keys
                if dataset_metadata_keys
                else project["dataset_metadata_keys"]
            ),
        }

        self.rs_client.update_project(**project_update)

    def delete_project(
        self, project_id: int | None = None, project_name: str | None = None
    ):
        """Delete Project

        Delete Project by ID or Name. Either must be provided.

        Args:
            project_id: Delete by ID. Defaults to None.
            project_name: Delete by Name. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Either project_id or project_name not provided.
            rsexceptions.ReadStoreError: Project not found
        """

        if (project_id is None) and (project_name is None):
            raise rsexceptions.ReadStoreError(
                "Either project_id or project_name must be provided"
            )

        if project_id:
            project = self.get_project(project_id=project_id)
            if project.empty:
                raise rsexceptions.ReadStoreError("Project not found")
        if project_name:
            project = self.get_project(project_name=project_name)
            if project.empty:
                raise rsexceptions.ReadStoreError("Project not found")
            else:
                project_id = int(project["id"])

        self.rs_client.delete_project(project_id)

    def download_project_attachment(
        self,
        attachment_name: str,
        project_id: int | None = None,
        project_name: str | None = None,
        outpath: str | None = None,
    ):
        """Download Project Attachment

        Specify project_id or project_name

        Args:
            attachment_name: Select attachment by name
            project_id: Set Project ID. Defaults to None.
            project_name: Set Project Name. Defaults to None.
            outpath: Set outpath. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Specify project_id or project_name
            rsexceptions.ReadStoreError: Project not found
            rsexceptions.ReadStoreError: Attachment not found
            rsexceptions.ReadStoreError: Output directory does not exist
        """

        if (project_id is None) and (project_name is None):
            raise rsexceptions.ReadStoreError("Either id or name must be provided")

        project = self.rs_client.get_project(
            project_id=project_id, project_name=project_name
        )

        # Check if the project was found
        if project == {}:
            raise rsexceptions.ReadStoreError("Project not found")

        project = rsdataclasses.RSProjectDetail(**project)
        attachments = project.attachments

        if attachment_name not in attachments:
            raise rsexceptions.ReadStoreError("Attachment not found")
        else:
            if outpath is None:
                outpath = os.getcwd()
                outpath = os.path.join(outpath, attachment_name)

            output_dirname = os.path.dirname(outpath)
            if (output_dirname != "") and (not os.path.exists(output_dirname)):
                raise rsexceptions.ReadStoreError(
                    f"Output directory {output_dirname} does not exist"
                )

            self.rs_client.download_project_attachment(
                attachment_name, outpath, project_id, project_name
            )

    def upload_fastq(
        self,
        fastq: List[str] | str,
        fastq_name: List[str] | str | None = None,
        read_type: List[str] | str | None = None,
    ):
        """Upload FASTQ files

        Args:
            fastq: List of FASTQ files or single FASTQ file
            fastq_name: List or single names of FASTQ files. Defaults to None.
            read_type: List of read_types. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: FASTQ file not found
            rsexceptions.ReadStoreError: FASTQ file not valid
        """

        if isinstance(fastq, str):
            fastq = [fastq]
        if isinstance(fastq_name, str):
            fastq_name = [fastq_name]
        if isinstance(read_type, str):
            read_type = [read_type]

        if fastq_name:
            assert len(fastq) == len(
                fastq_name
            ), "Number of FASTQ files and names must be equal"
        if read_type:
            assert len(fastq) == len(
                read_type
            ), "Number of FASTQ files and read types must be equal"

        fq_files = []
        fq_names = []
        fq_read_types = []
        for ix, fq in enumerate(fastq):
            if not os.path.exists(fq):
                raise rsexceptions.ReadStoreError(f"File {fq} not found")
            if not fq.endswith(tuple(self.fastq_extensions)):
                raise rsexceptions.ReadStoreError(
                    f"File {fq} is not a valid FASTQ file"
                )
            fq_files.append(os.path.abspath(fq))

            if fastq_name:
                fq_names.append(fastq_name[ix])
            else:
                fq_names.append(None)

            if read_type:
                fq_read_types.append(read_type[ix])
            else:
                fq_read_types.append(None)

        for fq, fq_name, fq_read_type in zip(fq_files, fq_names, fq_read_types):
            self.rs_client.upload_fastq(fq, fq_name, fq_read_type)

    def list_pro_data(
        self,
        project_id: int | None = None,
        project_name: str | None = None,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        name: str | None = None,
        data_type: str | None = None,
        include_archived: bool = False,
        return_type: str | None = None,
    ) -> pd.DataFrame | List[dict]:
        """List ProData

        List Processed Data

        Args:
            project_id: Filter by Project ID. Defaults to None.
            project_name: Filter by Project Name. Defaults to None.
            dataset_id: Filter by Dataset ID. Defaults to None.
            dataset_name: Filter by Dataset Name. Defaults to None.
            name: Filter by name. Defaults to None.
            data_type: Filter by data type. Defaults to None.
            include_archived: Return archived. Defaults to False.
            return_type: Specify return type. Default use return type from object.

        Returns:
            pd.DataFrame | List[dict]: List of ProData
        """

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        pro_data = self.rs_client.list_pro_data(
            project_id=project_id,
            project_name=project_name,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            name=name,
            data_type=data_type,
            include_archived=include_archived,
        )

        if return_type == "pandas":
            pro_data = self._convert_json_to_pandas(pro_data, rsdataclasses.RSProData)

        return pro_data

    def list_pro_data_metadata(
        self,
        project_id: int | None = None,
        project_name: str | None = None,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        name: str | None = None,
        data_type: str | None = None,
        include_archived: bool = False,
    ) -> pd.DataFrame:
        """List ProData Metadata

        Args:
            project_id: Filter by Project ID. Defaults to None.
            project_name: Filter by Project Name. Defaults to None.
            dataset_id: Filter by Dataset ID. Defaults to None.
            dataset_name: Filter by Dataset Name. Defaults to None.
            name: Filter by name. Defaults to None.
            data_type: Filter by data type. Defaults to None.
            include_archived: Return archived. Defaults to False.
        """

        pro_data = self.list_pro_data(
            project_id=project_id,
            project_name=project_name,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            name=name,
            data_type=data_type,
            include_archived=include_archived,
            return_type="pandas",
        )

        if pro_data.empty:
            return pd.DataFrame()
        else:
            metadata = pro_data["metadata"].apply(pd.Series)
            return metadata

    def get_pro_data(
        self,
        pro_data_id: int | None = None,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        name: str | None = None,
        version: int | None = None,
        return_type: str | None = None,
    ) -> pd.Series | dict:
        """Get ProData

        Return ProData by ID or Name + Dataset ID/Name

        Args:
            pro_data_id: ProData ID. Defaults to None.
            dataset_id: Dataset ID. Defaults to None.
            dataset_name: Dataset Name. Defaults to None.
            name: ProData Name. Defaults to None.
            version: ProData Version. Defaults to None.
            return_type: Specify return type. Default use return type from object.

        Raises:
            rsexceptions.ReadStoreError: Either pro_data_id or
                name plus dataset_id/dataset_name must be provided

        Returns:
            pd.Series | dict: ProData
        """

        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type

        if not pro_data_id:
            if not name:
                raise rsexceptions.ReadStoreError(
                    "Either pro_data_id or name + dataset_id/dataset_name required"
                )
            if not dataset_id and not dataset_name:
                raise rsexceptions.ReadStoreError(
                    "Either pro_data_id or name + dataset_id/dataset_name required"
                )

        pro_data = self.rs_client.get_pro_data(
            pro_data_id=pro_data_id,
            name=name,
            version=version,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

        if return_type == "pandas":
            pro_data = self._convert_json_to_pandas(
                pro_data, rsdataclasses.RSProDataDetail
            )

        return pro_data

    def upload_pro_data(
        self,
        name: str,
        pro_data_file: str,
        data_type: str,
        description: str = "",
        metadata: dict = {},
        dataset_id: int | None = None,
        dataset_name: str | None = None,
    ):
        """Upload ProData

        Upload ProData to ReadStore

        Must provide dataset_id or dataset_name

        Args:
            name: Set ProData name
            pro_data_file: Set ProData file path
            data_type: Set ProData data type
            description: Description for ProData. Defaults to ''.
            metadata: Metadata for ProData. Defaults to {}.
            dataset_id: Dataset ID. Defaults to None.
            dataset_name: Dataset Name. Defaults to None.

        Raises:
            rsexceptions.ReadStoreError: Dataset not found
            rsexceptions.ReadStoreError: Error uploading ProData
        """

        fq_dataset = self.rs_client.get_fastq_dataset(
            dataset_id=dataset_id, dataset_name=dataset_name
        )
        if fq_dataset == {}:
            raise rsexceptions.ReadStoreError(
                "No dataset found to associate ProData with"
            )

        fq_dataset_id = fq_dataset["id"]

        try:
            self.rs_client.upload_pro_data(
                name,
                pro_data_file,
                data_type,
                dataset_id=fq_dataset_id,
                metadata=metadata,
                description=description,
            )

        except rsexceptions.ReadStoreError as e:
            raise rsexceptions.ReadStoreError(f"Error uploading ProData: {e.message}")

    def delete_pro_data(
        self,
        pro_data_id: int | None = None,
        dataset_id: int | None = None,
        dataset_name: str | None = None,
        name: str | None = None,
        version: int | None = None,
    ):
        """Delete ProData

        Delete ProData entry by ID or combination of Name + Dataset ID/Name.

        Args:
            pro_data_id: Delete by ID. Defaults to None.
            dataset_id: Set by Dataset ID. Defaults to None.
            dataset_name: Set by Dataset Name. Defaults to None.
            name: Set by Name. Defaults to None.
            version: Set version to delete.
                Defaults to None, which deletes latest valid version.

        Raises:
            rsexceptions.ReadStoreError: Either pro_data_id or
                name plus dataset_id/dataset_name must be provided
            rsexceptions.ReadStoreError: Processed Data not found
        """

        if not pro_data_id:
            if not name:
                raise rsexceptions.ReadStoreError(
                    "Either pro_data_id or name + dataset_id/dataset_name required"
                )
            if not dataset_id and not dataset_name:
                raise rsexceptions.ReadStoreError(
                    "Either pro_data_id or name + dataset_id/dataset_name required"
                )

        try:
            self.rs_client.delete_pro_data(
                pro_data_id, name, dataset_id, dataset_name, version
            )

        except rsexceptions.ReadStoreError as e:
            if "ProData not found" in e.message:
                raise rsexceptions.ReadStoreError(
                    "ReadStore Error: ProData not found\n"
                )
            else:
                raise rsexceptions.ReadStoreError(f"ReadStore Error: {e.message}\n")
