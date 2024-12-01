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

import os
import configparser
import pandas as pd
from pydantic import BaseModel
from typing import List

from pyreadstore import rsclient
from pyreadstore import rsexceptions
from pyreadstore import rsdataclasses


class Client():
    
    RETURN_TYPES = ['pandas', 'json']
    
    def __init__(self,
                 config_dir: str = '~/.readstore',
                 username: str | None = None, 
                 token : str | None = None,
                 host: str = 'http://localhost',
                 return_type: str = 'pandas',
                 port: int = 8000,
                 fastq_extensions: List[str] = ['.fastq','.fastq.gz','.fq','.fq.gz']):
        """_summary_

        URL schema MUST be set
        
        Args:
            config_dir: Path to dir containing config. Defaults to '~/.readstore'.
            username: Username. Defaults to None.
            token: User Token. Defaults to None.
            host: Host address. Defaults to 'http://localhost'.
            return_type: Default return type. Defaults to 'pandas'.
            port: ReadStore Server port. Defaults to 8000.
            fastq_extensions: Allowed extensions to fastq. Defaults to ['.fastq','.fastq.gz','.fq','.fq.gz'].

        Raises:
            rsexceptions.ReadStoreError: User name and token must be provided
            rsexceptions.ReadStoreError: Config file not found
        """
        
        # Check valid return types
        self._check_return_type(return_type)
        self.return_type = return_type
        
        # If username & token provided, use them to initialize the client
        if username and token:
            endpoint_url  = f'{host}:{port}'      
        elif username or token:
            raise rsexceptions.ReadStoreError('Both Username and Token must be provided')
        # Case load config from files
        # TODO Add support for ENV variables ONLY
        else:
            if '~' in config_dir:
                config_dir = os.path.expanduser(config_dir)
            else:
                config_dir = os.path.abspath(config_dir)
            
            config_path = os.path.join(config_dir, 'config')
            if not os.path.exists(config_path):
                raise rsexceptions.ReadStoreError(f'Config file not found at {config_dir}')
            
            rs_config = configparser.ConfigParser()
            rs_config.read(config_path)
        
            username = rs_config.get('credentials', 'username', fallback=None)
            token = rs_config.get('credentials', 'token', fallback=None)
            endpoint_url = rs_config.get('general', 'endpoint_url', fallback=None)
            fastq_extensions = rs_config.get('general', 'fastq_extensions', fallback=None)
            fastq_extensions = fastq_extensions.split(',')
            
        # Check if ENV variables are set
        # Overwrite config if found
        if 'READSTORE_USERNAME' in os.environ:
            username = os.environ['READSTORE_USERNAME']
        if 'READSTORE_TOKEN' in os.environ:
            token = os.environ['READSTORE_TOKEN']
        if 'READSTORE_ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['READSTORE_ENDPOINT_URL']
        if 'READSTORE_FASTQ_EXTENSIONS' in os.environ:
            fastq_extensions = os.environ['READSTORE_FASTQ_EXTENSIONS']
            fastq_extensions = fastq_extensions.split(',')
        
        self.fastq_extensions = fastq_extensions
        
        # Initialize the client
        self.rs_client = rsclient.RSClient(username,
                                            token,
                                            endpoint_url,
                                            output_format='csv')
        
        
    def _convert_json_to_pandas(self,
                                json_data: List[dict] | dict,
                                validation_class: BaseModel) -> pd.DataFrame | pd.Series:
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
            raise rsexceptions.ReadStoreError('Invalid JSON data')
    
    def _check_return_type(self, return_type: str):
        """_check_return_type
        
        Check if return type is valid
        
        Args:
            return_type: Return type

        Raises:
            rsexceptions.ReadStoreError: Invalid return type 
        """
        
        if return_type not in Client.RETURN_TYPES:
            raise rsexceptions.ReadStoreError(f'Invalid return type. Must be in {Client.RETURN_TYPES}')
        
    def get_return_type(self) -> str:
        """get_return_type"""
        return self.return_type
     
    def list(self,
             project_id: int | None = None,
             project_name: str | None = None,
             return_type: str | None = None) -> pd.DataFrame | List[dict]:
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
        
        fq_datasets = self.rs_client.list_fastq_datasets(project_id=project_id,
                                                         project_name=project_name)
        
        if return_type == 'pandas':
            fq_datasets = self._convert_json_to_pandas(fq_datasets, rsdataclasses.RSFqDataset)
        
        return fq_datasets
    
    # TODO: Function to explode metadata
    
    def get(self,
            dataset_id: int| None = None,
            dataset_name: str | None = None,
            return_type: str | None = None) -> pd.Series | dict:
        """Get Dataset
        
        Args:
            dataset_id: Select by ID. Defaults to None.
            dataset_name: Select by Name. Defaults to None.
            return_type: Specify return type. Default use return type from object.

        Raises:
            rsexceptions.ReadStoreError: Either dataset_id or dataset_name must be provided

        Returns:
            pd.Series | dict: Dataset
        """
            
        if (dataset_id is None) and (dataset_name is None):
            raise rsexceptions.ReadStoreError('Either dataset_id or dataset_name must be provided')
            
        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type
        
        fq_dataset = self.rs_client.get_fastq_dataset(dataset_id = dataset_id,
                                                      dataset_name = dataset_name)
        
        if return_type == 'pandas':
            fq_dataset = self._convert_json_to_pandas(fq_dataset, rsdataclasses.RSFqDatasetDetail)
        
        return fq_dataset
    
    def get_fastq(self,
                dataset_id: int | None = None,
                dataset_name: str | None = None,
                return_type: str | None = None) -> pd.DataFrame | List[dict]:
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
            raise rsexceptions.ReadStoreError('Either id or name must be provided')
        
        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type
        
        fq_dataset = self.rs_client.get_fastq_dataset(dataset_id = dataset_id,
                                                      dataset_name = dataset_name)
        
        # Check if the dataset was found
        if fq_dataset == {}:
            if return_type == 'pandas':
                return_cols = rsdataclasses.RSFqFile.model_fields.keys()
                return pd.DataFrame(columns=return_cols)
            else:
                return []
        else:
            fq_dataset = rsdataclasses.RSFqDatasetDetail(**fq_dataset)
            
            fq_file_ids = [fq_dataset.fq_file_r1,
                           fq_dataset.fq_file_r2,
                           fq_dataset.fq_file_i1,
                           fq_dataset.fq_file_i2]
            
            fq_file_ids = [int(e) for e in fq_file_ids if not e is None]
            
            fq_files = [self.rs_client.get_fq_file(fq_file_id) for fq_file_id in fq_file_ids]
            
            if return_type == 'pandas':
                fq_files = self._convert_json_to_pandas(fq_files, rsdataclasses.RSFqFile)

            return fq_files
        

    def download_attachment(self,
                            attachment_name: str,
                            dataset_id: int | None = None,
                            dataset_name: str | None = None,
                            outpath: str | None = None):
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
            raise rsexceptions.ReadStoreError('Either id or name must be provided')
        
        fq_dataset = self.rs_client.get_fastq_dataset(dataset_id = dataset_id,
                                                      dataset_name = dataset_name)
        
        # Check if the dataset was found
        if fq_dataset == {}: 
            raise rsexceptions.ReadStoreError('Dataset not found')
        
        fq_dataset = rsdataclasses.RSFqDatasetDetail(**fq_dataset)
        attachments = fq_dataset.attachments
        
        if attachment_name not in attachments:
            raise rsexceptions.ReadStoreError('Attachment not found')
        else:
            if outpath is None:
                outpath = os.getcwd()
                outpath = os.path.join(outpath, attachment_name)
            
            output_dirname = os.path.dirname(outpath)
            if (output_dirname != '') and (not os.path.exists(output_dirname)):
                raise rsexceptions.ReadStoreError(f'Output directory {output_dirname} does not exist')
            
            self.rs_client.download_fq_dataset_attachment(attachment_name,
                                                        outpath,
                                                        dataset_id,
                                                        dataset_name)
    
    
    def list_projects(self,
                      return_type: str | None = None) -> pd.DataFrame | List[dict]:
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
        
        if return_type == 'pandas':
            projects = self._convert_json_to_pandas(projects, rsdataclasses.RSProject)
        
        return projects
    
    
    def get_project(self,
                    project_id: int | None = None,
                    project_name: str | None = None,
                    return_type: str | None = None) -> pd.Series | dict:
        """Get Project

        Args:
            project_id: Project ID. Defaults to None.
            project_name: Project Name. Defaults to None.
            return_type: Specify return type. Default use return type from object.

        Raises:
            rsexceptions.ReadStoreError: _description_

        Returns:
            pd.Series | dict: _description_
        """
        
        if (project_id is None) and (project_name is None):
            raise rsexceptions.ReadStoreError('Either project_id or project_name must be provided')
        
        if return_type:
            self._check_return_type(return_type)
            return_type = return_type
        else:
            return_type = self.return_type
        
        project = self.rs_client.get_project(project_id = project_id,
                                            project_name = project_name)
        
        if return_type == 'pandas':
            project = self._convert_json_to_pandas(project, rsdataclasses.RSProjectDetail)
        
        return project
    
    def download_project_attachment(self,
                                   attachment_name: str,
                                   project_id: int | None = None,
                                   project_name: str | None = None,
                                   outpath: str | None = None):
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
            raise rsexceptions.ReadStoreError('Either id or name must be provided')
        
        project = self.rs_client.get_project(project_id = project_id,
                                            project_name = project_name)
        
        # Check if the project was found
        if project == {}: 
            raise rsexceptions.ReadStoreError('Project not found')
        
        project = rsdataclasses.RSProjectDetail(**project)
        attachments = project.attachments
        
        if attachment_name not in attachments:
            raise rsexceptions.ReadStoreError('Attachment not found')
        else:
            if outpath is None:
                outpath = os.getcwd()
                outpath = os.path.join(outpath, attachment_name)
            
            output_dirname = os.path.dirname(outpath)
            if (output_dirname != '') and (not os.path.exists(output_dirname)):
                raise rsexceptions.ReadStoreError(f'Output directory {output_dirname} does not exist')
            
            self.rs_client.download_project_attachment(attachment_name,
                                                        outpath,
                                                        project_id,
                                                        project_name)
            
    def upload_fastq(self,
                     fastq : List[str] | str,
                     fastq_name : List[str] | str | None = None,
                     read_type: List[str] | str | None = None):
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
            assert len(fastq) == len(fastq_name), 'Number of FASTQ files and names must be equal'
        if read_type:
            assert len(fastq) == len(read_type), 'Number of FASTQ files and read types must be equal'
        
        fq_files = []
        fq_names = []
        fq_read_types = []
        for ix, fq in enumerate(fastq):
            if not os.path.exists(fq):
                raise rsexceptions.ReadStoreError(f'File {fq} not found')
            if not fq.endswith(tuple(self.fastq_extensions)):
                raise rsexceptions.ReadStoreError(f'File {fq} is not a valid FASTQ file')
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
            
            
    def list_pro_data(self,
                    project_id: int | None = None,
                    project_name: str | None = None,
                    dataset_id: int | None = None,
                    dataset_name: str | None = None,
                    name: str | None = None,
                    data_type: str | None = None,
                    include_archived: bool = False,
                    return_type: str | None = None) -> pd.DataFrame | List[dict]:
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
        
        pro_data = self.rs_client.list_pro_data(project_id=project_id,
                                                project_name=project_name,
                                                dataset_id=dataset_id,
                                                dataset_name=dataset_name,
                                                name=name,
                                                data_type=data_type,
                                                include_archived=include_archived)
        
        if return_type == 'pandas':
            pro_data = self._convert_json_to_pandas(pro_data, rsdataclasses.RSProData)
        
        return pro_data
        
        
    def get_pro_data(self,
                    pro_data_id: int | None = None,
                    dataset_id: int | None = None,
                    dataset_name: str | None = None,
                    name: str | None = None,
                    version: int | None = None,
                    return_type: str | None = None) -> pd.Series | dict:
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
                rsexceptions.ReadStoreError: Either pro_data_id or name + dataset_id/dataset_name must be provided

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
                raise rsexceptions.ReadStoreError('Either pro_data_id or name + dataset_id/dataset_name must be provided')
            if not dataset_id and not dataset_name:
                raise rsexceptions.ReadStoreError('Either pro_data_id or name + dataset_id/dataset_name must be provided')
            
        pro_data = self.rs_client.get_pro_data(pro_data_id=pro_data_id,
                                               name=name,
                                               version=version,
                                               dataset_id=dataset_id,
                                               dataset_name=dataset_name)
        
        if return_type == 'pandas':
            pro_data = self._convert_json_to_pandas(pro_data, rsdataclasses.RSProDataDetail)
        
        return pro_data
    
    
    def upload_pro_data(self,
                        name: str,
                        pro_data_file: str,
                        data_type: str,
                        description: str = '',
                        metadata: dict = {},
                        dataset_id: int | None = None,
                        dataset_name: str | None = None):
        """Upload ProData
        
        Upload ProData to ReadStore

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
        
        fq_dataset = self.rs_client.get_fastq_dataset(dataset_id = dataset_id,
                                                        dataset_name = dataset_name)
        if fq_dataset == {}:
            raise rsexceptions.ReadStoreError('No dataset found to associate ProData with')
                
        fq_dataset_id = fq_dataset['id']
        
        try:
            self.rs_client.upload_pro_data(name,
                                            pro_data_file,
                                            data_type,
                                            dataset_id=fq_dataset_id,
                                            metadata=metadata,
                                            description=description)

        except rsexceptions.ReadStoreError as e:
            raise rsexceptions.ReadStoreError(f'Error uploading ProData: {e.message}')
        
    def delete_pro_data(self,
                        pro_data_id: int | None = None,
                        dataset_id: int | None = None,
                        dataset_name: str | None = None,
                        name: str | None = None,
                        version: int | None = None):
        """Delete ProData

        Delete ProData by ID or Name + Dataset ID/Name
        
        Args:
            pro_data_id: Delete by ID. Defaults to None.
            dataset_id: Set by Dataset ID. Defaults to None.
            dataset_name: Set by Dataset Name. Defaults to None.
            name: Set by Name. Defaults to None.
            version: Set version to delete. Defaults to None, which deletes valid version.

        Raises:
            rsexceptions.ReadStoreError: Either pro_data_id or name + dataset_id/dataset_name must be provided
            rsexceptions.ReadStoreError: Processed Data not found
        """

        if not pro_data_id:
            if not name:
                raise rsexceptions.ReadStoreError('Either pro_data_id or name + dataset_id/dataset_name must be provided')
            if not dataset_id and not dataset_name:
                raise rsexceptions.ReadStoreError('Either pro_data_id or name + dataset_id/dataset_name must be provided')

        try:
            self.rs_client.delete_pro_data(pro_data_id,
                                            name,
                                            dataset_id,
                                            dataset_name,
                                            version)

        except rsexceptions.ReadStoreError as e:
            if 'ProData not found' in e.message:
                raise rsexceptions.ReadStoreError(f'ReadStore Error: ProData not found\n')
            else:
                raise rsexceptions.ReadStoreError(f'ReadStore Error: {e.message}\n')
