#!/usr/bin/env python3
"""
Script to merge two CSV files containing repository analysis data,
eliminating duplicates while preserving the maximum number of repositories.
"""

import pandas as pd
import sys
from pathlib import Path

def merge_csv_files(file1_path, file2_path, output_path):
    """
    Merge two CSV files eliminating duplicates based on repository URL.

    Args:
        file1_path: Path to first CSV file
        file2_path: Path to second CSV file
        output_path: Path for the merged output CSV file
    """
    print(f"Reading {file1_path}...")
    df1 = pd.read_csv(file1_path)

    print(f"Reading {file2_path}...")
    df2 = pd.read_csv(file2_path)

    print(f"File 1: {len(df1)} repositories")
    print(f"File 2: {len(df2)} repositories")

    # Combine both dataframes
    combined_df = pd.concat([df1, df2], ignore_index=True)
    print(f"Combined: {len(combined_df)} repositories")

    # Remove duplicates based on URL (unique identifier for repositories)
    # Keep the first occurrence (you can change to 'last' if you prefer newer data)
    merged_df = combined_df.drop_duplicates(subset=['url'], keep='first')

    print(f"After removing duplicates: {len(merged_df)} repositories")
    print(f"Duplicates removed: {len(combined_df) - len(merged_df)}")

    # Sort by stars (descending) to have most popular repositories first
    merged_df = merged_df.sort_values('stars', ascending=False)

    # Reset index
    merged_df = merged_df.reset_index(drop=True)

    # Save to output file
    merged_df.to_csv(output_path, index=False)
    print(f"Merged file saved as: {output_path}")

    # Show some statistics
    print("\n=== MERGE STATISTICS ===")
    print(f"Total unique repositories: {len(merged_df)}")
    print(f"Repositories from file 1: {len(df1)}")
    print(f"Repositories from file 2: {len(df2)}")
    print(f"Overlap (duplicates): {len(df1) + len(df2) - len(merged_df)}")
    print(f"Unique repositories added from file 2: {len(merged_df) - len(df1.drop_duplicates(subset=['url']))}")

    # Show top 5 repositories by stars
    print("\n=== TOP 5 REPOSITORIES BY STARS ===")
    top_repos = merged_df.head(5)[['name', 'owner', 'stars', 'primary_language']]
    for idx, row in top_repos.iterrows():
        print(f"{idx+1}. {row['owner']}/{row['name']} - {row['stars']:,} stars ({row['primary_language']})")

    return merged_df

def main():
    # Define file paths
    file1 = Path("repositories_ck_analysis.csv")
    file2 = Path("repositories_ck_analysis_carol.csv")
    output = Path("repositories_ck_analysis_merged.csv")

    # Check if files exist
    if not file1.exists():
        print(f"Error: {file1} not found!")
        sys.exit(1)

    if not file2.exists():
        print(f"Error: {file2} not found!")
        sys.exit(1)

    try:
        merged_df = merge_csv_files(file1, file2, output)
        print(f"\nSuccessfully merged files! Output: {output}")

    except Exception as e:
        print(f"Error merging files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
