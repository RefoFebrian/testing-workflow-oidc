import subprocess
import os

# Get all unstaged modified, added, or deleted files
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')

groups = {}

for line in lines:
    if not line: continue
    status = line[:2]
    file_path = line[3:]
    
    # Split path to get module name (first directory)
    parts = file_path.split('/')
    if len(parts) > 1:
        module = parts[0]
    else:
        module = "root"
        
    if module not in groups:
        groups[module] = []
    groups[module].append(file_path)

for module, files in groups.items():
    # Add files for this module
    for f in files:
        if '->' in f: # handle renames if any
            f = f.split('->')[1].strip()
        subprocess.run(['git', 'add', f])
        
    # Determine commit message
    if module == 'tw_asset_disposal':
        msg = f"FIX: standardize print layout and date format for Disposal Asset in {module}"
    elif module == 'tw_cash_count':
        msg = f"FIX: standardize cash count print layout and python date formats in {module}"
    else:
        msg = f"STYLE: standardize print reports date format (DD-MM-YYYY) and layout in {module}"
        
    subprocess.run(['git', 'commit', '-m', msg])

print("Finished committing by module.")
