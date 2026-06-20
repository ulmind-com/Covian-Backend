with open("app/api/v1/endpoints/candidate.py", "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith('@router.get("/{candidate_id}", response_model=CandidateResponse)'):
        start_idx = i
    if line.startswith('# =============================================================================='):
        if start_idx != -1 and i > start_idx and end_idx == -1:
            end_idx = i

if start_idx != -1 and end_idx != -1:
    block = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]
    
    # Append the block at the end of the file
    lines.extend(block)
    
    with open("app/api/v1/endpoints/candidate.py", "w") as f:
        f.writelines(lines)
    print("Fixed routes order successfully.")
else:
    print("Could not find the block.", start_idx, end_idx)
