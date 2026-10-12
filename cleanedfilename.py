import csv
from datetime import datetime
from pathlib import Path


def generate_master_csv(directory_path, output_csv_path="master_file_inventory.csv"):
    """Scans a local directory and generates a master CSV inventory of all files.

    Args:
        directory_path (str): Path to the local directory (e.g.,
          r"C:\\Users\\a")
        output_csv_path (str): Filename/path for the output CSV file.
    """
    base_dir = Path(directory_path).resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        raise ValueError(
            f"The provided path '{directory_path}' is not a valid directory."
        )

    # Define standard CSV headings
    fields = [
        "id",
        "local_directory_url",
        "local_file_path",
        "filename",
        "format",
        "published_date",
        "published_time",
        "cleaned_file_path",
        "cleaned_filename",
    ]

    records = []
    file_id = 1

    # rglob('*') recursively scans all subdirectories and files inside the folder
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            # Skip generating/scanning the output CSV if it happens to be in the same folder
            try:
                if file_path.resolve() == Path(output_csv_path).resolve():
                    continue
            except Exception:
                pass

            filename = file_path.name
            file_format = file_path.suffix.lstrip(".")

            # Retrieve file modification timestamp
            stat = file_path.stat()
            dt = datetime.fromtimestamp(stat.st_mtime)
            published_date = dt.strftime("%Y-%m-%d")
            published_time = dt.strftime("%H:%M:%S")

            #print(filename)

            # Create cleaned filename and path (replacing spaces with underscores)
            cleaned_filename = filename.replace(" ", "_")
            #print(cleaned_filename)
            cleaned_file_path = str(file_path.parent / cleaned_filename)

            records.append(
                {
                    "id": file_id,
                    "local_directory_url": str(base_dir),
                    "local_file_path": str(file_path),
                    "filename": filename,
                    "format": file_format,
                    "published_date": published_date,
                    "published_time": published_time,
                    "cleaned_file_path": cleaned_file_path,
                    "cleaned_filename": cleaned_filename,
                }
            )
            file_id += 1

    # Write data to CSV file with UTF-8 encoding
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(f"Master CSV successfully generated at: {Path(output_csv_path).resolve()}")
    print(f"Total files processed: {len(records)}")

if __name__ == "__main__":
    # Example usage:
    # Replace with your actual directory path (using raw string 'r' for Windows paths)
    target_directory = r"C:\Users\Eddie Chow\Desktop\hkuspace_lab_oct2026"

    # Run the function
    generate_master_csv(target_directory, output_csv_path="master_files.csv")