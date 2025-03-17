import re
from pathlib import Path
from .trxas_dataset import is_sample_data


def get_valid_file_index(folder):
    """Returns a list of filenames in 'folder' that end with exactly five digits."""
    pattern = re.compile(r".*\d{5}$")  
    prefix_db = {}
    
    for entry in Path(folder).iterdir():
        if entry.is_file() and is_sample_data(entry):
            if pattern.match(entry.name):
                index = int(entry.name[-5:])
                prefix = entry.name[:-5]
                if prefix not in prefix_db:
                    prefix_db[prefix] = [index]
                else:
                    prefix_db[prefix].append(index)
    
    return prefix_db
