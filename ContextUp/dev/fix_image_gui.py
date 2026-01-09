from pathlib import Path

target_file = Path("c:/Users/HG/Documents/HG_context_v2/ContextUp/src/features/image/convert_gui.py")

if not target_file.exists():
    print(f"File not found: {target_file}")
    exit(1)

lines = target_file.read_text(encoding='utf-8').splitlines()

start_marker = '            threading.Thread(target=_process_all, daemon=True).start()'
end_marker = '        def finish_conversion(self, count, errors):'

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if start_marker in line:
        start_idx = i
    if end_marker in line:
        end_idx = i

if start_idx != -1 and end_idx != -1:
    # Find ALL occurrences
    start_indices = [i for i, line in enumerate(lines) if start_marker in line]
    print(f"Start markers found at: {start_indices}")
    
    end_indices = [i for i, line in enumerate(lines) if end_marker in line]
    print(f"End markers found at: {end_indices}")

    if len(start_indices) >= 2:
        # We have the duplication case: [Start1, Junk, Start2, End]
        # We want to keep Start1, and jump to End.
        # But wait, Start2 is likely near End.
        
        # Scenario:
        # Line 353: Start1
        # ... junk ...
        # Line 411: Start2
        # Line 413: End
        
        # If we take lines[:Start1+1] + lines[End:], we remove everything between Start1 and End.
        # That removes the Junk AND Start2. This is what we want.
        
        real_start = start_indices[0]
        real_end = end_indices[0]
        
        print(f"Keeping line {real_start} and line {real_end}. Removing between.")
        new_lines = lines[:real_start+1] + [''] + lines[real_end:]
        target_file.write_text('\n'.join(new_lines), encoding='utf-8')
        print("File fixed (aggressive remove).")
    
    elif len(start_indices) == 1:
        print("Only one start marker found. Maybe looking at wrong place?")
        # Let's print lines around start
        idx = start_indices[0]
        print(f"Around {idx}:")
        for k in range(max(0, idx-2), min(len(lines), idx+5)):
            print(f"{k}: {lines[k]}")
