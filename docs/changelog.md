# Changelog

pyreadstore - ReadStore Python SDK

## [1.3.2] - 2025-02-11

**Bugfixes**
- update - Reset dataset associated project 

## [1.3.1] - 2025-02-11

**Bugfixes**
- update - Reset dataset associated project

## [1.3.0] - 2025-02-10

**Features**
- Add list_metadata methods for project, datasets and ProData to format metadata as data frame
- Add update methods for projects and datasets

**Updates**
- Code Formatting

## [1.2.0] - 2024-12-23

**Features**
- Add method rs_client.create: Create new Dataset 
- Add method rs_client.delete: Remove Dataset
- Add method rs_client.create_project: Create new Project
- Add method rs_client.delete_project: Remove Project

**Updates**
- Add new create, update, and delete methods
- Add validations for metadata
- Improved error messages in case of invalid backend requests 

**Bugfixes**
- Error parsing allowed FASTQ file extensions from ReadStore config file

## [1.1.0] - 2024-12-01

**Features**
- Add method upload_pro_data
- Add method list_pro_data
- Add method get_pro_data
- Add method delete_pro_data

**Updates**

- upload_fastq: Add fastq_name and read_type arguments to enable definition of FASTQ names and read types

## [1.0.0] - 2024-10-30

Initial Version