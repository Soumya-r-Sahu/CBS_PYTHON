"""
Script to perform system maintenance tasks.
"""
def clean_temp_files():
    print("Cleaning temporary files...")
    # Add cleaning logic here

def optimize_system():
    print("Optimizing system performance...")
    # Add optimization logic here

if __name__ == "__main__":
    task = input("Enter task (clean/optimize): ").strip().lower()
    if task == "clean":
        clean_temp_files()
    elif task == "optimize":
        optimize_system()
    else:
        print("Invalid task. Please choose 'clean' or 'optimize'.")
