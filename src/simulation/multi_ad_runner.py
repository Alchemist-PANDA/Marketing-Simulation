from typing import Dict, Any, List
from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad
import numpy as np

class MultiAdRunner:
    def __init__(self, num_agents: int = 10000):
        self.num_agents = num_agents

    def run_multi_test(self, ads_data: List[Dict[str, str]], channel: str = 'facebook', benchmarks: Dict[str, Any] = None, target_audience: dict = None, learned_weights: dict = None) -> Dict[str, Any]:
        """
        Run a simulation across N independent ads.
        ads_data should be a list of dicts: [{'name': 'Ad 1', 'text': '...'}, ...]
        """
        sim = MaxSimulation(num_agents=self.num_agents, target_audience=target_audience, learned_weights=learned_weights)
        
        results = []
        for ad_info in ads_data:
            ad_obj = Ad(
                text=ad_info['text'],
                channel=channel,
                creative_type='text',
                target_interest=ad_info.get('target_interest')
            )
            sim_res = sim.simulate_exposure(ad_obj)
            sim_res['ad_name'] = ad_info['name']
            sim_res['ad_text'] = ad_info['text']
            # Calculate metrics
            total_agents = sim_res.get('total_agents', self.num_agents)
            likes = sim_res.get('likes', 0)
            conversions = sim_res.get('conversions', 0)
            
            sim_res['conversion_rate'] = (conversions / total_agents) * 100 if total_agents > 0 else 0
            sim_res['engagement_rate'] = (likes / total_agents) * 100 if total_agents > 0 else 0
            
            results.append(sim_res)
            
        # Sort by conversion rate descending
        results.sort(key=lambda x: x['conversion_rate'], reverse=True)
        
        return {
            'ranked_results': results,
            'winner': results[0] if results else None,
            'total_ads_tested': len(results)
        }
