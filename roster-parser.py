import sqlite3
import pandas as pd
import os

def load_and_clean_data(file_path):
    data = pd.read_csv(file_path, skiprows=1)
    data.drop(index=0, inplace=True)
    data.columns = data.columns.str.strip()
    expected_columns = {
        '#': 'id',
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'Role': 'role',
        'Date of Birth (mm/dd/yyyy)': 'date_of_birth',
        'T-Shirt Size': 't_shirt_size',
        'Pant Size': 'pant_size',
        'Dietary Restrictions': 'dietary_restrictions',
        'Other Dietary Restrictions/Allergies': 'other_dietary_allergies',
        'Dancer Specified Allergies': 'dancer_allergies',
        'Email (xyz@abc.com)': 'email',
        'Phone Number (123-456-7890)': 'phone_number',
        'Vaccination Status (Boosted, Vaccinated, Unvaccinated)': 'vaccination_status',
        'Afterparty (Y/N)': 'afterparty',
        'Data Format Check (no action needed)': 'data_format_check'
    }
    data.rename(columns=expected_columns, inplace=True)

    for col in expected_columns.values():
        if col not in data.columns:
            data[col] = ""

    # Remove entries that do not have both a first and last name
    data = data.dropna(subset=['first_name', 'last_name'])
    data = data[(data['first_name'].str.strip() != '') & (data['last_name'].str.strip() != '')]

    team_name = os.path.splitext(os.path.basename(file_path))[0].upper()
    data['team'] = team_name

    return data


def create_database(conn, data_columns):
    cursor = conn.cursor()
    
    # Drop table to ensure schema consistency
    cursor.execute("DROP TABLE IF EXISTS roster")
    
    create_table_query = f'''
    CREATE TABLE roster (
        id INTEGER PRIMARY KEY,
        {", ".join([f'"{col}" TEXT' for col in data_columns if col != 'id'])}
    )
    '''
    cursor.execute(create_table_query)
    conn.commit()


def insert_data(conn, data):
    cursor = conn.cursor()
    columns = data.columns
    for _, row in data.iterrows():
        placeholders = ", ".join(["?" for _ in columns if _ != 'id'])
        insert_query = f'''
        INSERT INTO roster ({", ".join([f'"{col}"' for col in columns if col != 'id'])})
        VALUES ({placeholders})
        '''
        cursor.execute(insert_query, tuple(row.drop('id').fillna('')))
    conn.commit()


def calculate_team_metrics(data):
    if data.empty:
        return {}

    team_name = data['team'].iloc[0]
    total_roster = len(data)
    total_ap_count = data['afterparty'].astype(str).str.lower().value_counts().get('yes', 0)
    
    shirt_size_counts = data['t_shirt_size'].value_counts().to_dict() if 't_shirt_size' in data.columns else {}
    pant_size_counts = data['pant_size'].value_counts().dropna().to_dict() if 'pant_size' in data.columns else {}
    dietary_restrictions = data['dietary_restrictions'].value_counts(dropna=False).to_dict() if 'dietary_restrictions' in data.columns else {}
    dancer_allergies = data['dancer_allergies'].value_counts(dropna=False).to_dict() if 'dancer_allergies' in data.columns else {}

    metrics = {
        "team": team_name,
        "total_roster": total_roster,
        "total_ap_count": total_ap_count,
        "shirt_size_counts": shirt_size_counts,
        "pant_size_counts": pant_size_counts,
        "dietary_restrictions": dietary_restrictions,
        "dancer_allergies": dancer_allergies  # New metric
    }
    return metrics


def save_all_metrics_to_csv(metrics_list, output_path):    
    t_shirt_order = ['XS', 'S', 'M', 'L', 'XL']
    pant_size_order = ['N', 'XS', 'S', 'M', 'L', 'XL']

    flattened_metrics = []
    
    for metrics in metrics_list:
        flat_metrics = {
            "Team": metrics["team"],
            "Total Roster Count": metrics["total_roster"],
            "Total Afterparty Count": metrics["total_ap_count"]
        }

        for size in t_shirt_order:
            flat_metrics[f"T-Shirt Size - {size}"] = metrics["shirt_size_counts"].get(size, 0)

        for size in pant_size_order:
            flat_metrics[f"Pant Size - {size}"] = metrics["pant_size_counts"].get(size, 0)

        dietary_restrictions = metrics["dietary_restrictions"]
        for restriction in sorted(dietary_restrictions.keys(), key=str):
            flat_metrics[f"Dietary - {restriction}"] = dietary_restrictions[restriction]

        dancer_allergies = metrics["dancer_allergies"]
        for allergy in sorted(dancer_allergies.keys(), key=str):
            flat_metrics[f"Dancer Allergy - {allergy}"] = dancer_allergies[allergy]

        flattened_metrics.append(flat_metrics)

    df_metrics = pd.DataFrame(flattened_metrics)
    df_metrics.to_csv(output_path, index=False)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    rosters_dir = os.path.join(base_dir, "scraper/rosters")
    db_path = os.path.join(base_dir, "roster.db")
    output_csv = os.path.join(base_dir, "team_metrics.csv")

    csv_files = [os.path.join(rosters_dir, f) for f in os.listdir(rosters_dir) if f.endswith('.csv')]

    conn = sqlite3.connect(db_path)

    try:
        metrics_list = []

        # Create the database table only once
        if csv_files:
            sample_data = load_and_clean_data(csv_files[0])
            create_database(conn, sample_data.columns)

        for file_path in csv_files:
            data = load_and_clean_data(file_path)

            insert_data(conn, data)
            metrics = calculate_team_metrics(data)
            if metrics:
                metrics_list.append(metrics)

        if metrics_list:
            save_all_metrics_to_csv(metrics_list, output_csv)
            print(f"Metrics saved to {output_csv}")
        else:
            print("No valid teams found. No metrics file created.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()