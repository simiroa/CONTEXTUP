import sys

# Read the file
with open('src/scripts/manager_gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix indentation for lines 1182-1201 (0-indexed: 1181-1200)
# These lines need to be indented by 4 more spaces to be inside the try block
for i in range(1181, 1201):
    if i < len(lines):
        # Add 4 spaces to the beginning of each line (except empty lines)
        if lines[i].strip():
            lines[i] = '    ' + lines[i]

# Write back
with open('src/scripts/manager_gui.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed indentation")
