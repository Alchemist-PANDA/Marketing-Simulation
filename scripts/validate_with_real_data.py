import pandas as pd
import json
import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.multi_ad_runner import MultiAdRunner

def generate_markdown_report(results, output_path):
    md_content = f"# Validation Report\n\n"
    md_content += f"**Total Tests Analyzed:** {results['total_tests']}\n"
    md_content += f"**Directional Accuracy (Top 1 Match):** {results['directional_accuracy']:.2f}%\n\n"
    
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

def validate_data(csv_path: str, output_dir: str = "outputs", ad_text_fallback_method: str = None, ad_text_placeholder: str = None, mapping_csv_path: str = None, identifier_col: str = None):
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
        if ad_text_fallback_method == 'csv' and mapping_csv_path and identifier_col:
            try:
                mapping_df = pd.read_csv(mapping_csv_path)
                # The user provides a CSV with identifier and text. Find the text column (first non-identifier column)
                text_col = [c for c in mapping_df.columns if c != identifier_col]
                if text_col:
                    mapping_df = mapping_df.rename(columns={text_col[0]: 'ad_text'})
                    df = df.merge(mapping_df[[identifier_col, 'ad_text']], on=identifier_col, how='left')
                else:
                    print("Mapping CSV missing text column.")
            except Exception as e:
                print(f"Error reading mapping CSV: {e}")
        elif ad_text_fallback_method == 'placeholder':
            df['ad_text'] = ad_text_placeholder if ad_text_placeholder else "Facebook Ad"
        elif ad_text_fallback_method == 'skip':
            df['ad_text'] = "Skipped Simulation"

    required_cols = ['ad_text']
    for col in required_cols:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return None
            
    if 'conversions' not in df.columns:
        if 'total_conversion' in df.columns:
            df['conversions'] = df['total_conversion']
        else:
            print("Missing required column: conversions")
            return None
            
    if 'impressions' not in df.columns:
        df['impressions'] = 1000
        
    if 'ad_id' not in df.columns:
        if 'ad_name' in df.columns:
            df['ad_id'] = df['ad_name']
        else:
            df['ad_id'] = [f"Ad_{i}" for i in range(len(df))]
            
    if 'test_id' not in df.columns:
        df['test_id'] = 1
        
    df['cvr'] = df['conversions'] / df['impressions'].replace(0, 1)
    
    # Use MultiAdRunner to handle 2 or more ads
    runner = MultiAdRunner(num_agents=1000)
    
    target_cols = ['age', 'gender', 'interest1', 'interest2', 'interest3']
    for col in target_cols:
        if col not in df.columns:
            df[col] = "unknown"
            
    grouped = df.groupby(target_cols)
    
    report = {
        "total_tests": 0,
        "correct_predictions": 0,
        "tests": []
    }
    
    for group_key, group in grouped:
        test_id = "-".join(str(k) for k in group_key)
        if len(group) < 2:
            print(f"Skipping test {test_id}: Requires at least 2 ads to compare.")
            continue
            
        group = group.sort_values(by='cvr', ascending=False).reset_index(drop=True)
        actual_winner = group.iloc[0]['ad_id']
        
        ads_payload = []
        for _, row in group.iterrows():
            ads_payload.append({
                'name': str(row['ad_id']),
                'text': row['ad_text']
            })
            
        print(f"Simulating Test {test_id} with {len(group)} ads...")
        try:
            if ad_text_fallback_method == 'skip':
                predicted_winner = "Simulation Skipped"
                match = False
                print(f"Skipping simulation for Test {test_id}.")
            else:
                # Run multi-ad simulation
                sim_result = runner.run_multi_test(ads_payload, channel='facebook')
                predicted_winner = sim_result['winner']['ad_name']
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
        
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, 'validation_report.json')
    md_path = os.path.join(output_dir, 'validation_report.md')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    generate_markdown_report(report, md_path)
    
    print(f"\nValidation Complete!")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Directional Accuracy: {report.get('directional_accuracy', 0):.2f}%")
    print(f"Reports saved to {output_dir}/")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate simulation engine against real-world data.")
    parser.add_argument("--csv", required=True, help="Path to CSV file with historical ad data.")
    parser.add_argument("--out", default="outputs", help="Output directory for reports.")
    parser.add_argument("--fallback", default="placeholder", help="Fallback method for ad text.")
    args = parser.parse_args()
    
    validate_data(args.csv, args.out, ad_text_fallback_method=args.fallback, ad_text_placeholder="Facebook Ad")
