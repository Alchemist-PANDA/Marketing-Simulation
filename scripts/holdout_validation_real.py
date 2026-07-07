import pandas as pd
import json
import argparse
import sys
import os
from sklearn.model_selection import train_test_split
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.multi_ad_runner import MultiAdRunner

def generate_markdown_report(results, output_path):
    md_content = f"# Strict Holdout Validation Report (Real Data)\n\n"
    md_content += f"**Total Holdout Tests Analyzed:** {results['total_tests']}\n"
    md_content += f"**Directional Accuracy (Top 1 Match):** {results['directional_accuracy']:.2f}%\n\n"
    
    if results['directional_accuracy'] >= 80.0:
        md_content += f"🎉 **SUCCESS: 80% accuracy target achieved!**\n\n"
    else:
        md_content += f"⚠️ **Not quite there.** Needs more tuning.\n\n"

    md_content += "## Test Breakdown\n\n"
    for test in results['tests']:
        md_content += f"### Test: {test['test_id']}\n"
        md_content += f"- **Actual Winner:** Ad {test['actual_winner']}\n"
        md_content += f"- **Predicted Winner:** Ad {test['predicted_winner']}\n"
        md_content += f"- **Match:** {'✅ YES' if test['match'] else '❌ NO'}\n"
        md_content += f"\n**Actual #1 Text:** {test.get('ad_a_text', '')}\n"
        md_content += f"**Actual #2 Text:** {test.get('ad_b_text', '')}\n\n"
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def validate_data(csv_path: str, mapping_csv_path: str, identifier_col: str, output_dir: str = "outputs"):
    print(f"Loading real-world data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
        
    # Fix column shift bug for rows where campaign_id contains a dash (age strings)
    mask = df['campaign_id'].astype(str).str.contains('-', na=False)
    if mask.any():
        print(f"Found {mask.sum()} rows with column shift bug. Fixing data alignment...")
        shifted = df[mask].copy()
        
        shifted['approved_conversion'] = shifted['spent']
        shifted['total_conversion'] = shifted['clicks']
        shifted['spent'] = shifted['impressions']
        shifted['clicks'] = shifted['interest3']
        shifted['impressions'] = shifted['interest2']
        shifted['interest3'] = shifted['interest1']
        shifted['interest2'] = shifted['gender']
        shifted['interest1'] = shifted['age']
        shifted['gender'] = shifted['fb_campaign_id']
        shifted['age'] = shifted['campaign_id']
        shifted['fb_campaign_id'] = pd.NA
        shifted['campaign_id'] = pd.NA
        
        df.update(shifted)
        
    if 'ad_text' not in df.columns:
        if mapping_csv_path and identifier_col:
            try:
                mapping_df = pd.read_csv(mapping_csv_path)
                text_col = [c for c in mapping_df.columns if c != identifier_col]
                if text_col:
                    mapping_df = mapping_df.rename(columns={text_col[0]: 'ad_text'})
                    df = df.merge(mapping_df[[identifier_col, 'ad_text']], on=identifier_col, how='left')
                    df['ad_text'] = df['ad_text'].fillna('Placeholder Ad').astype(str)
                else:
                    print("Mapping CSV missing text column.")
            except Exception as e:
                print(f"Error reading mapping CSV: {e}")

    if 'conversions' not in df.columns:
        if 'total_conversion' in df.columns:
            # Drop rows with missing conversions
            df = df.dropna(subset=['total_conversion'])
            df['conversions'] = df['total_conversion']
            
    if 'impressions' not in df.columns:
        df['impressions'] = 1000
        
    if 'ad_id' not in df.columns:
        df['ad_id'] = [f"Ad_{i}" for i in range(len(df))]
            
    df['cvr'] = df['conversions'] / df['impressions'].replace(0, 1)
    
    target_cols = ['age', 'gender', 'interest1', 'interest2', 'interest3']
    for col in target_cols:
        if col not in df.columns:
            df[col] = "unknown"
            
    # Remove groups with less than 2 ads
    df['group_id'] = df[target_cols].astype(str).agg('-'.join, axis=1)
    group_sizes = df.groupby('group_id').size()
    valid_groups = group_sizes[group_sizes >= 2].index.tolist()
    
    df = df[df['group_id'].isin(valid_groups)]
    
    print(f"Found {len(valid_groups)} valid A/B test groups.")
    
    # 70/30 Train/Holdout split of the GROUPS
    np.random.seed(42)
    np.random.shuffle(valid_groups)
    split_idx = int(len(valid_groups) * 0.7)
    train_groups = valid_groups[:split_idx]
    holdout_groups = valid_groups[split_idx:]
    
    train_df = df[df['group_id'].isin(train_groups)]
    holdout_df = df[df['group_id'].isin(holdout_groups)]
    
    print(f"Split into {len(train_groups)} training groups and {len(holdout_groups)} holdout groups.")
    
    os.makedirs(output_dir, exist_ok=True)
    train_df.to_csv(os.path.join(output_dir, 'train_data.csv'), index=False)
    holdout_df.to_csv(os.path.join(output_dir, 'holdout_data.csv'), index=False)
    
    # Run simulation on Holdout set
    runner = MultiAdRunner(num_agents=1000)
    
    grouped = holdout_df.groupby('group_id')
    
    report = {
        "total_tests": 0,
        "correct_predictions": 0,
        "tests": []
    }
    
    for test_id, group in grouped:
        group = group.sort_values(by='cvr', ascending=False).reset_index(drop=True)
        actual_winner = group.iloc[0]['ad_id']
        
        ads_payload = []
        for _, row in group.iterrows():
            ads_payload.append({
                'name': str(row['ad_id']),
                'text': row['ad_text']
            })
            
        target_audience = {
            'age': group.iloc[0]['age'],
            'gender': group.iloc[0]['gender'],
            'interest1': group.iloc[0].get('interest1'),
            'interest2': group.iloc[0].get('interest2'),
            'interest3': group.iloc[0].get('interest3')
        }
        
        # Shuffle group payload to prevent run_multi_test tie-breaker bias
        import random
        random.seed(42)
        random.shuffle(ads_payload)
        
        print(f"Simulating Holdout Test {test_id} with {len(group)} ads...")
        try:
            # Run multi-ad simulation
            sim_result = runner.run_multi_test(ads_payload, channel='facebook', target_audience=target_audience)
            predicted_winner = sim_result['winner']['ad_name']
            
            print(f"Predicted: {predicted_winner} | Actual: {actual_winner}")
            print("Sim Results:", [(r['ad_name'], r['conversion_rate']) for r in sim_result['ranked_results']])
            
            match = (str(actual_winner) == str(predicted_winner))
            
            report['tests'].append({
                "test_id": str(test_id),
                "actual_winner": str(actual_winner),
                "predicted_winner": str(predicted_winner),
                "match": match,
                "ad_a_text": str(group.iloc[0]['ad_text']),
                "ad_b_text": str(group.iloc[1]['ad_text']) if len(group) > 1 else ""
            })
            
            report['total_tests'] += 1
            if match:
                report['correct_predictions'] += 1
                
        except Exception as e:
            print(f"Error simulating test {test_id}: {e}")
            continue
            
    if report['total_tests'] > 0:
        report['directional_accuracy'] = (report['correct_predictions'] / report['total_tests']) * 100
    else:
        report['directional_accuracy'] = 0.0
        
    json_path = os.path.join(output_dir, 'holdout_validation_report.json')
    md_path = os.path.join('HOLDOUT_VALIDATION_REPORT.md')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    generate_markdown_report(report, md_path)
    
    print(f"\nValidation Complete!")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Directional Accuracy: {report.get('directional_accuracy', 0):.2f}%")
    print(f"Report saved to HOLDOUT_VALIDATION_REPORT.md")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strict holdout validation on real data.")
    parser.add_argument("--csv", required=True, help="Path to CSV file with historical ad data.")
    parser.add_argument("--mapping_csv", required=True, help="Path to mapping CSV to add text")
    parser.add_argument("--identifier_col", required=True, help="Identifier column to merge on")
    parser.add_argument("--out", default="outputs", help="Output directory for reports.")
    args = parser.parse_args()
    
    validate_data(
        args.csv, 
        mapping_csv_path=args.mapping_csv,
        identifier_col=args.identifier_col,
        output_dir=args.out
    )
