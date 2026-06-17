import os
os.environ["PYTHONUTF8"] = "1"
import sys
import subprocess


def main():
    print("=== CampusGPT Oumi Training Orchestrator ===")
    
    # 1. Prepare/Format dataset
    print("\n--- Step 1: Preparing and Formatting Dataset ---")
    # Add project root to sys.path to allow imports if run from root directory
    sys.path.append(os.getcwd())
    
    try:
        from dataset.prepare_oumi_dataset import convert_dataset
        success = convert_dataset()
        if not success:
            print("Failed to convert dataset.")
            sys.exit(1)
    except Exception as e:
        print(f"Error importing or running prepare_oumi_dataset: {e}")
        # Fallback to subprocess
        print("Running dataset preparation via subprocess...")
        res = subprocess.run([sys.executable, "dataset/prepare_oumi_dataset.py"], capture_output=True, text=True)
        print(res.stdout)
        if res.returncode != 0:
            print("Subprocess dataset preparation failed:", res.stderr)
            sys.exit(1)
            
    # 2. Check if oumi is installed
    print("\n--- Step 2: Checking Oumi Installation ---")
    try:
        import oumi
        print("Oumi library is installed and importable.")
    except ImportError:
        print("Oumi library is not installed in this environment.")
        print("Please ensure you install it first: pip install oumi")
        sys.exit(1)
        
    # 3. Trigger oumi train SFT
    print("\n--- Step 3: Triggering Oumi Training ---")
    config_path = os.path.join("campusgpt", "oumi_train_config.yaml")
    if not os.path.exists(config_path):
        config_path = "oumi_train_config.yaml"
        if not os.path.exists(config_path):
            print("Config path oumi_train_config.yaml not found.")
            sys.exit(1)
        
    print(f"Running oumi training using config: {config_path}...")
    
    # Run SFT training as a subprocess to keep logs clear and isolate dependencies
    cmd = [sys.executable, "-m", "oumi", "train", "-c", config_path]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run process and stream stdout/stderr in real-time
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1,
            encoding="utf-8",
            errors="replace"
        )
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line, end="")
            sys.stdout.flush()
        process.wait()
        
        if process.returncode == 0:
            print("\nTraining completed successfully!")
            print("Fine-tuned model weights saved in: campusgpt/fine_tuned_model")
        else:
            print(f"\nTraining failed with return code {process.returncode}")
            sys.exit(process.returncode)
    except Exception as e:
        print(f"Error occurred during training execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
