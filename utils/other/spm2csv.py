import os


def spm_to_csv(spm_path, csv_path):
    try:
        with open(spm_path, "r") as spm_file:
            next(spm_file)
            content = spm_file.read()

        with open(csv_path, "w", newline="") as csv_file:
            csv_file.write(content)
        return True
    except Exception as e:
        print(f"Error converting {spm_path} to {csv_path}: {e}")
        return False


def get_csv_dimensions(file_path):
    try:
        rows = 0
        cols = None
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    rows += 1
                    if cols is None:
                        cols = len(line.strip().split(","))
        return rows, cols
    except Exception as e:
        print(f"Error getting dimensions for {file_path}: {e}")
        return 0, 0


def main():
    directory_path = os.getcwd()

    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return

    dimensions = set()

    spm_files = [f for f in os.listdir(directory_path) if f.endswith(".spm")]

    if not spm_files:
        print(f"No .spm files found in {directory_path}")
        return

    print(f"Converting {len(spm_files)} .spm files to .csv...")
    for filename in spm_files:
        spm_path = os.path.join(directory_path, filename)
        csv_path = os.path.join(directory_path, filename.replace(".spm", ".csv"))

        if spm_to_csv(spm_path, csv_path):
            rows, cols = get_csv_dimensions(csv_path)
            dimensions.add((rows, cols))

    print("\nCSV file dimensions:")
    for rows, cols in dimensions:
        print(f"Rows: {rows}, Columns: {cols}")


if __name__ == "__main__":
    main()
