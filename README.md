# ReadStore CLI

This README describes the ReadStore Command Line Interface (CLI). The ReadStore CLI is used to upload FASTQ files to the ReadStore database and access Projects, Datasets, metadata and attachment files.

The ReadStore CLI enables you to automate your bioinformatics pipelines and workflows.
 
Find ReadStore Tutorials and Intro Videos on 
https://www.youtube.com/@evobytedigitalbio

Or as blog posts https://evo-byte.com/blog/

General ReadStore information on www.evo-byte.com/readstore

For questions reach out to info@evo-byte.com

## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgments](#acknowledgments)

## The Lean Solution for Managing FASTQ and NGS Data

ReadStore is a platform for storing, managing, and integrating genomic data. It speeds up analysis and offers a simple way of managing and sharing FASTQ and NGS datasets. Built-in project and metadata management structures your workflows and a collaborative user interface enhances teamwork — so you can focus on generating insights.

The integrated Webservice enables your to directly retrieve data from ReadStore via the terminal Command-Line-Interface (CLI) or Python / R SDKs.

The ReadStore Basic version provides a local webserver with a simple user management. If you need an organization-wide deployment, advanced user and group management or cloud integration please check the ReadStore Advanced versions and reach out to info@evo-byte.com.

## Description

The ReadStore CLI is used to upload FASTQ files to the ReadStore database and access Projects, Datasets, metadata and attachment files.

You can use the CLI from your shell, terminal or from your data pipelines and scripts. You are encouraged to embed the ReadStore CLI in any bioinformatics application or pipeline.


## Security and Permissions<a id="backup"></a>

**PLEASE READ AND FOLLOW THESE INSTRUCTIONS CAREFULLY!**

### User Accounts and Token<a id="token"></a>

Using the CLI with a ReadStore server requires an active User Account and a Token. You should **never enter your user account password** when working with the CLI.

To retrieve your token:

1. Login to the ReadStore App via your browser
2. Navigate to `Settings` page and click on `Token`
3. If needed you can regenerate your token (`Reset`). This will invalidate the previous token

For uploading FASTQ files your User Account needs to have `Staging Permission`. If you can check this in the `Settings` page of your account. If you not have `Staging Permission`, ask the ReadStore Server Admin to grant you permission.

### CLI Configuration

After running the `readstore configure` the first time, a configuration file is created in your home directory (`~/.readstore/config`).
This is create with user specific read-/write permissions (`chmod 600`), make sure to keep restricted permission in order to protect your token.

You find more information on the configuration file below.

## Installation

`pip3 install readstore-cli`

You can perform the install in a conda or venv virtual environment to simplify package management.

A local install is also possible

`pip3 install --user readstore-cli`

Make sure that `~/.local/bin` is on your `$PATH` in case you encounter problems when starting the server.

Validate the install by running, which should print the ReadStore CLI version

`readstore -v`

## Usage

Detailed tutorials, videos and explanations are found on [YouTube](https://www.youtube.com/playlist?list=PLk-WMGySW9ySUfZU25NyA5YgzmHQ7yquv) or on the [**EVO**BYTE blog](https://evo-byte.com/blog).

### Quickstart

Let's upload some FASTQ files.

#### 1. Configure CLI

Make sure you have the ReadStore CLI installed and a running ReadStore server with your user registered.

1. Run `readstore configure`

2. Enter your username and [token](#token)
3. Select the default output of your CLI requests. You can choose between `text` outputs, comma-separated `csv` or `json`.
4. Run `readstore configure list` and check if your credentials are correct. 

#### 2. Upload Files

For uploading FASTQ files your User Account needs to have `Staging Permission`. If you can check this in the `Settings` page of your account. If you not have `Staging Permission`, ask the ReadStore Server Admin to grant you permission.

Move to a folder that contains some FASTQ files.

`readstore upload myfile_r1.fastq`

This will upload the file and run the QC check. You can select several files at once using the `*` wildcard.
The fastq files need tio have default endings `.fastq, .fastq.gz, .fq, .fq.gz`

#### 3. Stage Files

Login to the User Interface on your browser and move to the `Staging` page. Here you find a list of all FASTQ files you just upload. For large files the QC step can take a while to complete. FASTQ files are grouped in Datasets which you can `Check In`. Then they appear in the `Datasets` page and for instance be assigned to a Project.

#### 4. Access Datasets via the CLI

The ReadStore CLI enables programmatic access to Datasets and FASTQ files. Some examples are:

`readstore list` : List all FASTQ files

`readstore get --id 25` : Get detailed view on Dataset 25

`readstore get --id 25 --read1-path` : Get path for Read1 FASTQ file

`readstore get --id 25 --meta` : Get metadata for Dataset 25

`readstore project get --name cohort1 --attachment` : Get attachment files for Project "cohort1"

You can find a full list in the readstore documentation


### CLI Configuration

`readstore configure` manages the CLI configuration. To setup the configuration:

1. Run `readstore configure`

2. Enter your username and [token](#token)
3. Select the default output of your CLI requests. You can choose between `text` outputs, comma-separated `csv` or `json`.
4. Run `readstore configure list` and check if your credentials are correct. 

If you already have a configuration in place, the CLI will ask you if you want to overwrite the existing credentials. Select `y` if yes.

After running the `readstore configure` the first time, a configuration file is created in your home directory (`~/.readstore/config`).
This is create with user specific read-/write permissions (`chmod 600`), make sure to keep restricted permission in order to protect your token.

```
[general]
endpoint_url = http://localhost:8000
fastq_extensions = ['.fastq', '.fastq.gz', '.fq', '.fq.gz']
output = csv

[credentials]
username = myusername
token = myrandomtoken
``` 

You can further edit the configuration of the CLI client from this configuration file. In case your ReadStore Django server is not run at the default port 8000, you need to update the `endpoint_url`. If you need to process FASTQ files with file endings other than the those listed in `fastq_extensions`, you can modify the list.

### Upload FASTQ files

For uploading FASTQ files your User Account needs to have `Staging Permission`. If you can check this in the `Settings` page of your account. If you not have `Staging Permission`, ask the ReadStore Server Admin to grant you permission.

`readstore upload myfile_r1.fastq myfile_r2.fastq ...`

This will upload the file and run the QC check. You can select several files at once using the `*` wildcard. It can take some time before FASTQ files are available in your `Staging` page depending on how large file are and how long the QC step takes.

### Access Projects

There are 3 commands for accessing projects, `readstore project list`, `readstore project get` and `readstore project download`.

- `list` provides an overview of project, metadata and attachments
- `get` provides detailed information on individual projects and to its metadata and attachments
- `download` lets you download attachment files of a project from the ReadStore database

####  readstore project list

```
usage: readstore project ls [options]

List Projects

options:
  -h, --help            show this help message and exit
  -m, --meta            Get Metadata
  -a, --attachment      Get Attachment
  --output {json,text,csv}
                        Format of command output (see config for default)
```

Show project id and name.

The `-m/--meta` include metadata for projects as json string in output.

The `-a/--attachment` include attachment names as list in output.

Adapt the output format of the command using the `--output` options.


####  readstore project get

```
usage: readstore project get [options]

Get Project

options:
  -h, --help            show this help message and exit
  -id , --id            Get Project by ID
  -n , --name           Get Project by name
  -m, --meta            Get only Metadata
  -a, --attachment      Get only Attachment
  --output {json,text,csv}
                        Format of command output (see config for default)
```

Show project details for a project selected either by `--id` or the `--name` argument.
The project details include description, date of creation, attachments and metadata

The `-m/--meta` shows **only** the metadata with keys in header.

The `-a/--attachment` shows **only** the attachments.

Adapt the output format of the command using the `--output` options.

Example: `readstore project get --id 2`

####  readstore project download

```
usage: readstore project download [options]

Download Project Attachments

options:
  -h, --help          show this help message and exit
  -id , --id          Select Project by ID
  -n , --name         Select Project by name
  -a , --attachment   Set Attachment Name to download
  -o , --outpath      Download path or directory (default . )
```

Download attachment files for a project. Select a project selected either by `--id` or the `--name` argument.

With the `--attachment` argument you specify the name of the attachment file to download.

Use the `--outpath` to set a directory to download files to.

Example `readstore project download --id 2 -a ProjectQC.pptx -o ~/downloads`

## Contributing

Please feel free to create an issue for problems with the software or feature suggestions.

## License

ReadStore Basic Server is distributed under a commercial / proprietary license.
Details are found in the LICENSE file


## Credits and Acknowledgments<a id="acknowledgments"></a>

ReadStore CLI is built upon the following open-source python packages and would like to thank all contributing authors, developers and partners.

- Python (https://www.djangoproject.com/)
- djangorestframework (https://www.django-rest-framework.org/)
- requests (https://requests.readthedocs.io/en/latest/)
- gunicorn (https://gunicorn.org/)
- pysam (https://pysam.readthedocs.io/en/latest/api.html)
- pyyaml (https://pyyaml.org/)
- streamlit (https://streamlit.io/)
- pydantic (https://docs.pydantic.dev/latest/)
- pandas (https://pandas.pydata.org/)




