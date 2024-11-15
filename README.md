File finder:
A file finder is used to retrieve media files from directory tree based on their extensions.
File finder can filter out files based on their modification date. This can be used to only
retrieve files which have been created or modified since a certain timestamp.
Retrieved files are passer to a batch file processing controler.

Batch file processing controler:
A batch file processing is used to control if media files have to be processed based on their
past processing status. This allows to eliminate unnecessary file (re)processing.

media location processing
A media location process is used to analyse media files in order to find if they are embeding geolocation data.
It creates json *media file location index*, identified througha unique key, along with their
geolocation data and a generated thumbnail file.

media Location grouping:
A location grouping command allows to analyse an index of geolocated media files and group them by proximity.
The command can specify a distance threshold which is used to determine location proximity.
The command creates a json *media file grouping*. Each identified group is composed of a set of media keys refering
to the *media file location index* associated with a gps point at the center of the group.

proximity identification:
A proximity identification command allows to compare two *media file grouping* and identify if they have
groups which shows proximity. The command can specify a distance threshold which is used to determine location proximity.
The command creates a json *group proximity register*

## Development Setup

## Development Status
[![CI/CD Pipeline](https://github.com/jmarc580625/medialocate/actions/workflows/ci.yml/badge.svg)](https://github.com/jmarc580625/medialocate/actions/workflows/ci.yml)

### Virtual Environment Setup

1. Create a virtual environment (if not already created):
```bash
python -m venv .venv
```
2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```
3. Install dependencies:
- For production:
```bash
pip install -r requirements.txt
```
- For development:
```bash
pip install -r requirements-dev.txt
```
4. Install pre-commit hooks:
```bash
pre-commit install
```
### Environment Variables
The project uses the following environment variables:
```
PYTHONPATH=test;src