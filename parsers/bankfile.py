"""
Process different files that contain transaction histories.

Companion/Contemporary to logfile.
"""
import csv

CSV_TYPES: dict[str, list] = {
    "apple_fields": [
        "Transaction Date",
        "Clearing Date",
        "Description",
        "Merchant",
        "Category",
        "Type",
        "Amount (USD)",
        "Purchased By"
        ],
    "elan_fields": [
        "Date",
        "Transaction",
        "Name",
        "Memo",
        "Amount"
        ],
    "df_fields": [
        "Transaction ID",
        "Posting Date",
        "Effective Date",
        "Transaction Type",
        "Amount",
        "Check Number",
        "Reference Number",
        "Description",
        "Transaction Category",
        "Type",
        "Balance",
        "Memo",
        "Extended Description"
        ],
}
def bank_2_blob(filename: str) -> BankBlob:
    """Parse a bank file and place the data into bankblips."""
    # Open the file
    with open(filename, encoding='UTF-8') as csvfile:
        bankreader = csv.DictReader(csvfile, dialect='excel')
        # Determine the type of csv file
        first_row = next(bankreader)
        csv_type = get_csv_type(list(first_row))

        # Populate blips
        if csv_type ==

    # Add Blips to Blob

    # Return Blob


def elan_2_blip(bank_data: dict) -> BankBlip:
    pass


def apple_2_blip(bank_data: dict) -> BankBlip:
    pass


def df_2_blip(bank_data: dict) -> BankBlip:
    pass


def compare_lists(this_list: list, that_list: list):
    """Return true if all items in this_list match those in that_list."""
    for element in this_list:
        if element not in that_list:
            return False
    # Inverse to be sure two lists are exactly the same
    for element in that_list:
        if element not in this_list:
            return False
    return True


def get_csv_type(field_list: list) -> str:
    """Determine what type of csv file matches the list of fields.

    Args:
        field_list (list): Normally the first row from a csv file.

    Returns:
        str: a key from the dictionary of csv types
    """
    # Compare field list to all lists in csv types
    for csv_type, columns in CSV_TYPES.items():
        if compare_lists(columns, field_list):
            return csv_type
    return 'NO_MATCH'
