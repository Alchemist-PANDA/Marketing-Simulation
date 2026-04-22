import pandas as pd
import os
import sys

def manual_labeling(input_path='data/facebook_ads.csv', output_path='data/manual_labels.csv', target_count=200):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        # Fallback: create synthetic data if missing
        print("Generating small sample for labeling...")
        df = pd.DataFrame({
            'ad_id': range(target_count),
            'text': [f"Sample Ad Text {i}: Discover our amazing new product with exclusive discounts!" for i in range(target_count)]
        })
        os.makedirs('data', exist_ok=True)
        df.to_csv(input_path, index=False)
    else:
        df = pd.read_csv(input_path)

    # Detect text column
    text_col = None
    for col in ['text', 'headline', 'ad_copy', 'ad_text']:
        if col in df.columns:
            text_col = col
            break

    if not text_col:
        print("Could not find text column. Using placeholder.")
        df['ad_text'] = "Placeholder Ad Text"
        text_col = 'ad_text'

    # Load existing labels
    if os.path.exists(output_path):
        labeled_df = pd.read_csv(output_path)
        labeled_texts = set(labeled_df[text_col].tolist())
        print(f"Resuming: {len(labeled_df)} ads already labeled.")
    else:
        labeled_df = pd.DataFrame(columns=[text_col, 'price_score', 'trust_score', 'urgency_score'])
        labeled_texts = set()

    remaining_df = df[~df[text_col].isin(labeled_texts)].reset_index(drop=True)

    print(f"\n--- Marketing Simulation Labeling Tool ---")
    print(f"Goal: Label {target_count} ads. Progress: {len(labeled_df)}/{target_count}")
    print("Instructions: Enter scores from 0.0 to 1.0. Press Enter for default (0.5).")
    print("Press Ctrl+C to save and exit.\n")

    try:
        for idx, row in remaining_df.iterrows():
            if len(labeled_df) >= target_count:
                print("Target reached!")
                break

            print(f"[{len(labeled_df)+1}/{target_count}] AD TEXT:")
            print(f"\" {row[text_col]} \"")

            def get_input(prompt_text):
                val = input(f"{prompt_text} (0-1, default 0.5): ").strip()
                if not val:
                    return 0.5
                try:
                    f_val = float(val)
                    return max(0.0, min(1.0, f_val))
                except ValueError:
                    print("Invalid input, using 0.5")
                    return 0.5

            p = get_input("Price Score (Affordability)")
            t = get_input("Trust Score (Credibility)")
            u = get_input("Urgency Score (Scarcity)")

            new_row = {
                text_col: row[text_col],
                'price_score': p,
                'trust_score': t,
                'urgency_score': u
            }

            labeled_df = pd.concat([labeled_df, pd.DataFrame([new_row])], ignore_index=True)
            # Save after each entry
            labeled_df.to_csv(output_path, index=False)
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nExiting and saving progress...")

    print(f"\nLabeling session finished. Total labeled: {len(labeled_df)}")
    if len(labeled_df) >= 100:
        print("Success: Minimum requirements for retraining met.")

if __name__ == "__main__":
    manual_labeling()
