import os
import json

def convert_dataset():
    # Detect directory
    cwd = os.getcwd()
    if os.path.basename(cwd) == "dataset":
        dataset_dir = "."
    else:
        dataset_dir = "dataset"

    input_file = os.path.join(dataset_dir, "combined.jsonl")
    output_file = os.path.join(dataset_dir, "oumi_train_data.jsonl")

    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist. Please run create_dataset.py first.")
        return False

    print(f"Reading dataset from {input_file}...")
    converted_records = []
    
    with open(input_file, "r", encoding="utf-8") as infile:
        for idx, line in enumerate(infile):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                instruction = record.get("instruction", "").strip()
                response = record.get("response", "").strip()
                
                if not instruction or not response:
                    print(f"Warning: Line {idx+1} is missing instruction or response. Skipping.")
                    continue
                
                # Format into standard Oumi conversation schema
                converted_record = {
                    "messages": [
                        {"role": "user", "content": instruction},
                        {"role": "assistant", "content": response}
                    ]
                }
                converted_records.append(converted_record)
            except Exception as e:
                print(f"Error parsing line {idx+1}: {e}")

    print(f"Writing {len(converted_records)} formatted records to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as outfile:
        for record in converted_records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print("Dataset preparation complete!")
    return True

if __name__ == "__main__":
    convert_dataset()
