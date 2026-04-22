import pandas as pd
import os
import sys
from tqdm import tqdm

def label_ads(input_path='data/facebook_ads.csv', output_path='data/labeled_ads.csv', num_to_label=200):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    df = pd.read_csv(input_path)

    # Check if we have an existing labeled file to resume from
    if os.path.exists(output_path):
        labeled_df = pd.read_csv(output_path)
        print(f"Resuming from existing labeled data: {len(labeled_df)} ads already labeled.")
    else:
        labeled_df = pd.DataFrame(columns=['text', 'price_score', 'trust_score', 'urgency_score'])

    labeled_texts = set(labeled_df['text'].tolist())
    remaining_df = df[~df['text'].isin(labeled_texts)].sample(frac=1).reset_index(drop=True)

    count = 0
    try:
        for idx, row in remaining_df.iterrows():
            if len(labeled_df) >= num_to_label:
                print(f"\nTarget of {num_to_label} labels reached!")
                break

            print(f"\n--- Ad {len(labeled_df) + 1}/{num_to_label} ---")
            print(f"Text: {row['text']}")

            try:
                p = float(input("Price Score (0-1) [cheap/affordable]: "))
                t = float(input("Trust Score (0-1) [credible/guaranteed]: "))
                u = float(input("Urgency Score (0-1) [FOMO/limited]: "))

                new_row = {
                    'text': row['text'],
                    'price_score': max(0.0, min(1.0, p)),
                    'trust_score': max(0.0, min(1.0, t)),
                    'urgency_score': max(0.0, min(1.0, u))
                }
                labeled_df = pd.concat([labeled_df, pd.DataFrame([new_row])], ignore_index=True)
                labeled_df.to_csv(output_path, index=False) # Checkpoint
                count += 1
            except ValueError:
                print("Invalid input. Skipping this ad.")
                continue
            except KeyboardInterrupt:
                print("\nInterrupted. Saving progress...")
                break

    finally:
        labeled_df.to_csv(output_path, index=False)
        print(f"\nFinished. Total labeled ads: {len(labeled_df)}")

if __name__ == "__main__":
    print("Welcome to the Ad Labeling Tool.")
    print("Enter values between 0.0 and 1.0 for each score.")
    label_ads()
