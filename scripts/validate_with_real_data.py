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

def validate_data(csv_path: str, output_dir: str = "outputs"):
    print(f"Loading real-world data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
        
    required_cols = ['ad_text', 'conversions']
    for col in required_cols:
        if col not in df.columns:
            print(f"Missing required column: {col}")
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
    
    grouped = df.groupby('test_id')
    
    report = {
        "total_tests": 0,
        "correct_predictions": 0,
        "tests": []
    }
    
    for test_id, group in grouped:
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
            # Run multi-ad simulation
            sim_result = runner.run_multi_test(ads_payload, channel='facebook')
            predicted_winner = sim_result['winner']['ad_name']
            
            match = (str(actual_winner) == str(predicted_winner))
            
            report['tests'].append({
                "test_id": str(test_id),
                "actual_winner": actual_winner,
                "predicted_winner": predicted_winner,
                "match": match,
                "ad_a_text": group.iloc[0]['ad_text'],
                "ad_b_text": group.iloc[1]['ad_text'] if len(group) > 1 else ""
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
    args = parser.parse_args()
    
    validate_data(args.csv, args.out)
