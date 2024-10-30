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
    attachments: List[str]
    

class RSProjectDetail(BaseModel):
    id: int
    name: str
    description: str
    created: datetime.datetime
    creator: str
    metadata: dict
    attachments: List[str]