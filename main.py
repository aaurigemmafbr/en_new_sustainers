import pandas as pd
import streamlit as st
from datetime import datetime
import os
import sys

# Month mapping for output filename
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

COLUMNS_TO_KEEP = [
    "Supporter ID", "Supporter Email", "Campaign ID", "Organization or Company",
    "First Name", "Last Name", "Partner Name", "Address 1", "City", "State",
    "ZIP Code", "Raisers Edge Constituent ID","Assigned Region", "Campaign Data 4", "Campaign Data 16"
]

COLUMNS_TO_RENAME = {
    "Campaign Data 4": "Donation Amount",
    "Campaign Data 16": "Monthly Donation Start Date"
}

def reformat_date_string(d):
    """Rearranges a date string from D/M/YYYY to MM/DD/YYYY as a string"""
    try:
        parts = str(d).strip().split("/")
        if len(parts) == 3:
            day, month, year = parts
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
    except:
        pass
    return ""

def parse_date_column(date_str):
    """Parse date string in D/M/Y format to extract month"""
    try:
        # Handle different date formats and potential issues
        date_str = str(date_str).strip()
        if pd.isna(date_str) or date_str == 'nan':
            return None
        
        # Split by '/' and parse
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            return int(month)
        return None
    except:
        return None

def process_csv(csv_file, target_month):
    """Process CSV file: filter by month, sort, keep & rename columns."""
    try:
        df = pd.read_csv(csv_file)

        if "Campaign Data 16" not in df.columns:
            raise ValueError("Column 'Campaign Data 16' not found in CSV file")

        # Parse dates and extract month
        df["parsed_date"] = pd.to_datetime(df["Campaign Data 16"], errors='coerce', dayfirst=True)
        df['parsed_month'] = df["parsed_date"].dt.month

        # Filter by target month
        filtered_df = df[df['parsed_month'] == target_month].copy()

        # Sort by parsed date
        filtered_df = filtered_df.sort_values(by="parsed_date")

        # Keep only desired columns
        filtered_df = filtered_df[COLUMNS_TO_KEEP]

        # Rename columns
        filtered_df = filtered_df.rename(columns=COLUMNS_TO_RENAME)

        # Format date column as string MM/DD/YYYY
        filtered_df["Monthly Donation Start Date"] = filtered_df["Monthly Donation Start Date"].apply(reformat_date_string)

        return filtered_df

    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

def save_filtered_csv(filtered_df, target_month, output_dir="."):
    """Save filtered dataframe to CSV with specified naming convention"""
    month_name = MONTH_NAMES[target_month]
    filename = f"{month_name} New EN Monthly Donors.csv"
    filepath = os.path.join(output_dir, filename)
    
    filtered_df.to_csv(filepath, index=False)
    return filepath

def run_streamlit_app():
    """Streamlit web interface"""
    st.title("EN New Sustainers by Month")
    st.write('''
    1. In Engaging Networks, navigate to Data & Reports --> Export --> Monthly Donor Reports --> New Monthly Donor Report  
    2. Edit the query Participation Date to include the target month  
    3. Click Use Query  
    4. Use the following Export Options:  
        Format = Transaction  
        File Type = csv  
        Custom Reference Names = checked  
        Supporter Data Columns = checked  
        Use Export Group = Monthly Donor Reports  
        Use Export Version = version 2  
    5. Download the report from the Job monitor and upload below
    ''')
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    # Month selection
    month_options = {f"{i} - {MONTH_NAMES[i]}": i for i in range(1, 13)}
    selected_month_key = st.selectbox("Select Month", list(month_options.keys()))
    selected_month = month_options[selected_month_key]
    
    if uploaded_file is not None:
        try:
            # Process the CSV
            filtered_df = process_csv(uploaded_file, selected_month)
            
            # Display results
            st.success(f"Found {len(filtered_df)} records for {MONTH_NAMES[selected_month]}")
            
            if len(filtered_df) > 0:
                # Show preview
                st.subheader("Preview of filtered data:")
                st.dataframe(filtered_df.head())
                
                # Prepare download
                month_name = MONTH_NAMES[selected_month]
                filename = f"{month_name} New EN Monthly Donors.csv"
                csv_data = filtered_df.to_csv(index=False)
                
                st.download_button(
                    label="Download Filtered CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                st.warning(f"No records found for {MONTH_NAMES[selected_month]}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

def run_cli():
    """Command line interface for local testing"""
    print("CLI Mode")
    print("=" * 40)
    
    # Get CSV file path
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = input("Enter CSV file path: ").strip()
    
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found")
        return
    
    # Get month selection
    if len(sys.argv) > 2:
        try:
            target_month = int(sys.argv[2])
        except ValueError:
            print("Error: Month must be a number between 1-12")
            return
    else:
        print("\nAvailable months:")
        for i, month in MONTH_NAMES.items():
            print(f"{i}: {month}")
        
        try:
            target_month = int(input("\nEnter month number (1-12): "))
        except ValueError:
            print("Error: Please enter a valid number")
            return
    
    if target_month < 1 or target_month > 12:
        print("Error: Month must be between 1 and 12")
        return
    
    try:
        # Process CSV
        print(f"\nProcessing CSV file: {csv_file}")
        print(f"Filtering for month: {MONTH_NAMES[target_month]}")
        
        filtered_df = process_csv(csv_file, target_month)
        
        # Save results
        output_path = save_filtered_csv(filtered_df, target_month)
        
        print(f"\nSuccess!")
        print(f"Found {len(filtered_df)} records for {MONTH_NAMES[target_month]}")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        # Try accessing Streamlit's session_state; if it works, we're in Streamlit
        _ = st.session_state
        run_streamlit_app()
    except RuntimeError:
        # If accessing session_state fails, run CLI
        run_cli()
