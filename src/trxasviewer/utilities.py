import re
import os
from .trxas_dataset import is_sample_data


def get_valid_file_index(folder):
    """Returns a list of filenames in 'folder' that end with exactly five digits."""
    pattern = re.compile(r".*\d{5}$")  
    
    try:
        return [int(entry.name[-5:]) for entry in os.scandir(folder) if 
                pattern.match(entry.name) and \
                is_sample_data(os.path.join(folder, entry.name))]
    except FileNotFoundError:
        return [0, 1]