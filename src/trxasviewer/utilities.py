import re
import os
from .trxas_dataset import is_sample_data


def get_valid_file_index(folder):
    """Returns a list of filenames in 'folder' that end with exactly five digits."""
    pattern = re.compile(r".*\d{5}$")  
    file_index = []
    prefix = []
    try:
        for entry in os.scandir(folder):
            if is_sample_data(os.path.join(folder, entry.name)):
                if pattern.match(entry.name):
                    file_index.append(int(entry.name[-5:]))
                    prefix.append(entry.name[:-5])
        file_index.sort()
        prefix = list(set(prefix))
        if len(prefix) > 1:
            raise ValueError("Multiple prefixes found in folder")
        return os.path.join(folder, prefix[0]), file_index
    except FileNotFoundError:
        return 'none', [0, 1]