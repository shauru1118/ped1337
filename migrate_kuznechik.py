import os
import shutil
from pathlib import Path

def main():
    root = Path(__file__).parent
    src_dir = root / "kuznechik"
    dest_dir = root / "stego" / "crypto" / "kuznechik"

    print("Migrating Kuznyechik assets...")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy binary tables
    src_tables = src_dir / "gost_tables"
    dest_tables = dest_dir / "gost_tables"
    if src_tables.exists():
        shutil.copy2(src_tables, dest_tables)
        print(f"Copied gost_tables to {dest_tables.relative_to(root)}")
    else:
        print("Warning: gost_tables not found in source directory!")

    # Copy PDF specifications if exist
    src_pdf = src_dir / "GOST_R_3413-2015.pdf"
    dest_pdf = dest_dir / "GOST_R_3413-2015.pdf"
    if src_pdf.exists():
        shutil.copy2(src_pdf, dest_pdf)
        print(f"Copied PDF spec to {dest_pdf.relative_to(root)}")

    # Remove old directory
    if src_dir.exists():
        shutil.rmtree(src_dir)
        print("Removed old kuznechik root directory.")

    # Self-destruct
    try:
        os.remove(__file__)
        print("Migration script self-destructed.")
    except Exception:
        pass

    print("🎉 Kuznyechik migration completed successfully!")

if __name__ == "__main__":
    main()
