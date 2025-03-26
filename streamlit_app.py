import streamlit as st
import pandas as pd

# Streamlit UI
st.title("Excel Data Checker with Dynamic Column Comparison")

# Upload Correct Data File
st.write("### Upload Correct Data File")
correct_file = st.file_uploader("Upload Correct Excel File", type=["xlsx", "csv"], key="correct_file")

if correct_file:
    file_ext = correct_file.name.split('.')[-1]
    df_correct = pd.read_excel(correct_file, engine='openpyxl') if file_ext == 'xlsx' else pd.read_csv(correct_file, low_memory=False)
    
    st.write("### First 5 Rows of Correct Data File")
    st.dataframe(df_correct.head(5))
    
    # Upload Data Checking File
    st.write("### Upload Data Checking File")
    checking_file = st.file_uploader("Upload Data Checking Excel File", type=["xlsx", "csv"], key="checking_file")

    if checking_file:
        file_ext = checking_file.name.split('.')[-1]
        df_checking = pd.read_excel(checking_file, engine='openpyxl') if file_ext == 'xlsx' else pd.read_csv(checking_file, low_memory=False)
        
        st.write("### First 5 Rows of Data Checking File")
        st.dataframe(df_checking.head(5))

        # Ensure 'unique_cus_num' exists in both dataframes
        if "unique_cus_num" in df_correct.columns and "unique_cus_num" in df_checking.columns:

            # Data Cleaning: Dropping rows with null 'unique_cus_num' values
            df_correct_null = df_correct[df_correct["unique_cus_num"].isnull()]
            df_checking_null = df_checking[df_checking["unique_cus_num"].isnull()]
            
            # Drop rows where 'unique_cus_num' is null in both files
            df_correct = df_correct.dropna(subset=["unique_cus_num"])
            st.write("### Dropped Rows with Null 'unique_cus_num' Values - Correct File")
            st.dataframe(df_correct_null)
            
            df_checking = df_checking.dropna(subset=["unique_cus_num"])
            st.write("### Dropped Rows with Null 'unique_cus_num' Values - Checking File")
            st.dataframe(df_checking_null)

            # Find customers in the Correct File whose 'unique_cus_num' is not in the Checking File
            #checking whether all customer records in the (df_correct) are also present in the  (df_checking) by comparing a "unique_cus_num"
            missing_cus = df_correct[~df_correct["unique_cus_num"].isin(df_checking["unique_cus_num"])]   
            if not missing_cus.empty:
                st.write("### Customers in Correct File but Missing in Checking File")
                st.dataframe(missing_cus)
            else:
                st.success("All customers in the Correct File are present in the Checking File.")
                
            # Drop rows where 'verified_by' is null in both files------------------------------------------------------------------
            df_correct = df_correct.dropna(subset=["verified_by"])
            df_checking = df_checking.dropna(subset=["verified_by"])

            # Display table after dropping rows where 'verified_by' is null
            st.write("### Data After Dropping Rows with Null 'verified_by' Values")
            
            # Ensure required columns exist in both files AFTER dropping nulls
            if "unique_cus_num" in df_correct.columns and "unique_cus_num" in df_checking.columns:
                # Allow users to select multiple columns for comparison
                st.write("### Select Columns to Compare")
                columns = list(df_correct.columns)
                selected_columns = st.multiselect("Select Columns for Comparison", columns)

                if selected_columns:#result will be given from only selected columns------------------------------------------
                    # Function to check exact match
                    def exact_match(val_correct, val_checking):
                        val_correct = str(val_correct).strip() if pd.notna(val_correct) else ""
                        val_checking = str(val_checking).strip() if pd.notna(val_checking) else ""
                        return val_correct == val_checking  # Return True if they match

                    # Merge dataframes on the common key, only for existing values in both###
                    merged_df = df_correct.merge(df_checking, on="unique_cus_num", suffixes=("_correct", "_checking"), how="inner")
                    
                    # Check for mismatches in selected columns
                    for col in selected_columns:
                        merged_df[f"{col}_Match"] = merged_df.apply(lambda row: exact_match(row[f"{col}_correct"], row[f"{col}_checking"]), axis=1)

                    # Filter out rows with mismatches--------------
                    mismatch_cols = [f"{col}_Match" for col in selected_columns]
                    mismatched_data = merged_df[merged_df[mismatch_cols].apply(lambda x: not all(x), axis=1)]

                    # Display mismatched rows
                    if not mismatched_data.empty:
                        st.write("### Mismatched Data")
                        
                        # Define the correct format for displaying mismatches
                        mismatch_display_cols = ["unique_cus_num", "cus_id_checking"]
                        for col in selected_columns:
                            mismatch_display_cols.append(f"{col}_correct")
                            mismatch_display_cols.append(f"{col}_checking")
                            mismatch_display_cols.append(f"{col}_Match")  # Include match indicator

                        # Convert match results to ✅ or ❌ for better readability
                        for col in selected_columns:
                            mismatched_data[f"{col}_Match"] = mismatched_data[f"{col}_Match"].apply(lambda x: "✅" if x else "❌")
                        #st.write("Columns in mismatched_data:", mismatched_data.columns)###-------new 
                        st.dataframe(mismatched_data[mismatch_display_cols])
                        
                        # Additional output table
                        st.write("### Summary of Mismatched Values")
                        summary_table = mismatched_data[["unique_cus_num", "cus_id_checking"] + [f"{col}_correct" for col in selected_columns] + [f"{col}_Match" for col in selected_columns]]

                        # Replace matched values with blanks
                        for col in selected_columns:#checks for mismatches only for customers that exist in both files:
                            summary_table[col] = summary_table.apply(
                                lambda row: "" if row[f"{col}_Match"] == "✅" else row[f"{col}_correct"], axis=1
                            )
                            
                        # Remove the '_correct' and '_checking' columns, keep only the correct values
                        summary_table = summary_table[["unique_cus_num", "cus_id_checking"] + selected_columns]

                        st.dataframe(summary_table)
                    else:
                        st.success("No mismatches found in the selected columns.")
                else:
                    st.warning("Please select at least one column to compare.")
            else:
                st.error("The 'unique_cus_num' column is missing from one of the files.")
        else:
            st.error("The 'unique_cus_num' column is missing from one of the files.")
