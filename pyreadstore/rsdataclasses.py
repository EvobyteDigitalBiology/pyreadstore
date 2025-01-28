# pyreadstore/rsdataclasses.py

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


from typing import List
import datetime

from pydantic import BaseModel


class RSFqDataset(BaseModel):
    id: int
    name: str
    description: str
    qc_passed: bool
    paired_end: bool
    index_read: bool
    project_ids: List[int]
    project_names: List[str]
    metadata: dict
    attachments: List[str]

class RSFqDatasetDetail(BaseModel):
    id: int
    name: str
    description: str
    qc_passed: bool
    paired_end: bool
    index_read: bool
    project_ids: List[int]
    project_names: List[str]
    created: datetime.datetime
    fq_file_r1: int | None
    fq_file_r2: int | None
    fq_file_i1: int | None
    fq_file_i2: int | None
    metadata: dict
    attachments: List[str]
    
class RSFqFile(BaseModel):
    id: int
    name: str
    qc_passed: bool
    read_type: str
    read_length: int
    num_reads: int
    size_mb: int
    qc_phred_mean: float
    created: datetime.datetime
    creator: str
    upload_path: str
    md5_checksum: str

class RSProject(BaseModel):
    id: int
    name: str
    metadata: dict
    dataset_metadata_keys: dict
    attachments: List[str]
    
class RSProjectDetail(BaseModel):
    id: int
    name: str
    description: str
    created: datetime.datetime
    creator: str
    metadata: dict
    dataset_metadata_keys: dict
    attachments: List[str]
    
class RSProData(BaseModel):
    id: int
    name: str
    data_type: str
    version: int
    dataset_id: int
    dataset_name: str
    upload_path: str
    metadata: dict

class RSProDataDetail(BaseModel):
    id: int
    name: str
    description: str
    data_type: str
    version: int
    created: datetime.datetime
    valid_to: datetime.datetime | None
    creator: str
    dataset_id: int
    dataset_name: str
    upload_path: str
    metadata: dict
