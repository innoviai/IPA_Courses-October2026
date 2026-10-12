import csv
from datetime import datetime
from pathlib import Path
import shutil


def generate_cleaned_dataset_and_csv(
    directory_path, master_csv_name="master_file_inventory.csv"
):
    """Scans a local directory, creates a new dated folder, copies and renames files

    (removing spaces), and generates a master CSV inventory.
    """
    base_dir = Path(directory_path).resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        raise ValueError(
            f"The provided path '{directory_path}' is not a valid directory."
        )

    # Get today's date for the new folder name
    today_str = datetime.now().strftime("%Y-%m-%d")
    cleaned_dir_name = f"cleaned_data_{today_str}"

    # Create the new destination directory inside the base directory
    output_dir = base_dir / cleaned_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

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
            # Skip files that are already inside the newly created cleaned folder or the CSV file itself
            try:
                if (
                    output_dir in file_path.parents
                    or file_path.resolve() == Path(master_csv_name).resolve()
                ):
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

            # Create cleaned filename (replacing spaces with underscores)
            cleaned_filename = filename.replace(" ", "_")
            dest_file_path = output_dir / cleaned_filename

            # Handle duplicate filenames if they exist across different subfolders
            if dest_file_path.exists():
                stem = dest_file_path.stem
                suffix = dest_file_path.suffix
                counter = 1
                while dest_file_path.exists():
                    cleaned_filename = f"{stem}_{counter}{suffix}"
                    dest_file_path = output_dir / cleaned_filename
                    counter += 1

            # Copy and rename the file into the new folder (preserving metadata)
            shutil.copy2(file_path, dest_file_path)

            records.append(
                {
                    "id": file_id,
                    "local_directory_url": str(base_dir),
                    "local_file_path": str(file_path),
                    "filename": filename,
                    "format": file_format,
                    "published_date": published_date,
                    "published_time": published_time,
                    "cleaned_file_path": str(dest_file_path),
                    "cleaned_filename": cleaned_filename,
                }
            )
            file_id += 1

    # Write data to CSV file with UTF-8 encoding
    csv_output_path = base_dir / master_csv_name
    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(f"New cleaned folder created at: {output_dir}")
    print(f"Master CSV successfully generated at: {csv_output_path}")
    print(f"Total files processed and copied: {len(records)}")

if __name__ == "__main__":
    # Make sure to use the 'r' prefix for Windows paths containing backslashes!
    target_directory = r"C:\Users\Eddie Chow\Desktop\hkuspace_lab_oct2026"

    # Run the function
    generate_cleaned_dataset_and_csv(target_directory)