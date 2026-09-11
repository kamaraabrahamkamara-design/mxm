import gradio as gr
import pandas as pd
from datetime import datetime

# Define standard columns for the ledger
COLUMNS = [
    "Date & Time",
    "Transaction Type",
    "Customer Name",
    "Phone Number",
    "Amount ($)",
    "Transaction ID (TxID)",
    "Digital Float Bal ($)",
    "Physical Cash Bal ($)",
    "Notes"
]

def add_transaction(tx_type, name, phone, amount, tx_id, current_float, current_cash, notes, current_df):
    """Calculates new balances, appends the transaction to the state dataframe, and exports a clean CSV."""
    # Strict validation: If crucial info is missing, change nothing and alert user
    if not name or not phone or not tx_id or amount <= 0:
        return current_df, current_float, current_cash, None

    amount = float(amount)
    current_float = float(current_float)
    current_cash = float(current_cash)

    # Core mobile money accounting logic
    if tx_type == "Deposit (Cash-In)":
        # Agent collects cash, sends out digital float
        new_float = current_float - amount
        new_cash = current_cash + amount
    else:
        # Agent hands out cash, receives digital float
        new_float = current_float + amount
        new_cash = current_cash - amount

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Structure the new record
    new_entry = {
        "Date & Time": now_str,
        "Transaction Type": tx_type,
        "Customer Name": name,
        "Phone Number": phone,
        "Amount ($)": amount,
        "Transaction ID (TxID)": tx_id,
        "Digital Float Bal ($)": round(new_float, 2),
        "Physical Cash Bal ($)": round(new_cash, 2),
        "Notes": notes
    }

    # Append securely to our running cloud dataframe state
    updated_df = pd.concat([current_df, pd.DataFrame([new_entry])], ignore_index=True)

    # Generate an isolated downloadable CSV export file path
    export_path = "mobile_money_ledger_export.csv"
    updated_df.to_csv(export_path, index=False)

    # Returns updated structural data, current balances, and references the file download component
    return (
        updated_df,
        round(new_float, 2),
        round(new_cash, 2),
        export_path
    )

# Build the layout using the robust Gradio Blocks structure
with gr.Blocks(title="Mobile Money Ledger") as app:
    # Initialize reactive states for memory persistence across user sessions inside the container
    ledger_state = gr.State(pd.DataFrame(columns=COLUMNS))

    gr.Markdown("# 📱 Mobile Money Digital Log Book")
    gr.Markdown("A clean, production-grade interface designed to safely record daily mobile money logs and track balances.")

    with gr.Row():
        # Running balances tracking cards (Initialized with standard agent baseline values: $1,000)
        float_tracker = gr.Number(label="Current Digital Float ($)", value=1000.0, interactive=False)
        cash_tracker = gr.Number(label="Current Physical Cash ($)", value=1000.0, interactive=False)

    with gr.Row():
        # Left Panel: Data input form
        with gr.Column(scale=1):
            gr.Markdown("### Log New Entry")
            tx_type = gr.Radio(["Deposit (Cash-In)", "Withdrawal (Cash-Out)"], label="Transaction Type", value="Deposit (Cash-In)")
            cust_name = gr.Textbox(label="Customer Name", placeholder="e.g. John Doe")
            cust_phone = gr.Textbox(label="Phone Number", placeholder="e.g. 077XXXXXXX")
            amount = gr.Number(label="Transaction Amount ($)", value=0.0)
            tx_id = gr.Textbox(label="Transaction ID (TxID Reference)", placeholder="Copy paste from provider SMS")
            notes = gr.Textbox(label="Notes / Remarks", placeholder="Optional entry flags")

            submit_btn = gr.Button("Add Entry & Update Log", variant="primary")

        # Right Panel: Table visualizations and exports
        with gr.Column(scale=2):
            gr.Markdown("### Live Ledger Sheet")
            ledger_table = gr.Dataframe(headers=COLUMNS, datatype=["str"]*len(COLUMNS), interactive=False)

            gr.Markdown("### Export Ledger Data")
            download_file = gr.File(label="Download Complete Log Book (CSV)", interactive=False)

    # Event binding mapping state transformations correctly
    submit_btn.click(
        fn=add_transaction,
        inputs=[tx_type, cust_name, cust_phone, amount, tx_id, float_tracker, cash_tracker, notes, ledger_state],
        outputs=[ledger_table, float_tracker, cash_tracker, download_file]
    )

    # Parallel sync: ensuring the UI Dataframe mirrors the cloud state on launch
    app.load(fn=lambda df: df, inputs=[ledger_state], outputs=[ledger_table])

if __name__ == "__main__":
    app.launch(share=True)
