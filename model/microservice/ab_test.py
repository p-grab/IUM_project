import pandas as pd
import os
import json
import logging
import hashlib
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class ABTestManager:
    def __init__(self, log_file='ab_log.csv'):
        self.log_file = log_file
        self.assignments = {}
        self.interaction_count = defaultdict(int)
        self._load_log()
    
    def _load_log(self):
        if os.path.exists(self.log_file):
            try:
                self.log_df = pd.read_csv(self.log_file)
                logger.info(f"Loaded A/B log: {len(self.log_df)} records")
            except Exception as e:
                logger.warning(f"Could not load log: {e}")
                self.log_df = pd.DataFrame()
        else:
            self.log_df = pd.DataFrame()
    
    def assign_variant(self, listing_id):
        if listing_id in self.assignments:
            return self.assignments[listing_id]
        
        listing_hash = int(hashlib.md5(str(listing_id).encode()).hexdigest(), 16)
        variant = 'A' if listing_hash % 2 == 0 else 'B'
        
        self.assignments[listing_id] = variant
        self.interaction_count[variant] += 1
        
        return variant
    
    def log_interaction(self, listing_id, variant, top_aspects, bottom_aspects):
        try:
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'listing_id': listing_id,
                'variant': variant,
                'top_aspects': json.dumps([a['aspect'] for a in top_aspects]),
                'bottom_aspects': json.dumps([a['aspect'] for a in bottom_aspects]),
                'top_scores': json.dumps([a['score'] for a in top_aspects]),
                'bottom_scores': json.dumps([a['score'] for a in bottom_aspects]),
            }
            
            self.log_df = pd.concat([self.log_df, pd.DataFrame([interaction])], ignore_index=True)
            self.log_df.to_csv(self.log_file, index=False)
            
        except Exception as e:
            logger.error(f"Log interaction error: {str(e)}")
    
    def log_feedback(self, listing_id, rating, comment=''):
        try:
            variant = self.assignments.get(listing_id, 'unknown')
            
            feedback = {
                'timestamp': datetime.now().isoformat(),
                'listing_id': listing_id,
                'variant': variant,
                'rating': rating,
                'comment': comment,
                'feedback': True
            }
            
            self.log_df = pd.concat([self.log_df, pd.DataFrame([feedback])], ignore_index=True)
            self.log_df.to_csv(self.log_file, index=False)
            
        except Exception as e:
            logger.error(f"Log feedback error: {str(e)}")
    
    def get_statistics(self):
        try:
            if self.log_df.empty:
                return {
                    "total_interactions": 0,
                    "variant_A": {"count": 0},
                    "variant_B": {"count": 0}
                }
            
            interactions = self.log_df[self.log_df.get('feedback') != True] if 'feedback' in self.log_df.columns else self.log_df
            
            stats = {
                "total_interactions": len(interactions),
                "variant_A": {
                    "count": len(interactions[interactions['variant'] == 'A']),
                    "unique_listings": int(interactions[interactions['variant'] == 'A']['listing_id'].nunique()) if 'listing_id' in interactions.columns else 0
                },
                "variant_B": {
                    "count": len(interactions[interactions['variant'] == 'B']),
                    "unique_listings": int(interactions[interactions['variant'] == 'B']['listing_id'].nunique()) if 'listing_id' in interactions.columns else 0
                }
            }
            
            if 'feedback' in self.log_df.columns and 'rating' in self.log_df.columns:
                feedback = self.log_df[self.log_df['feedback'] == True]
                if not feedback.empty:
                    for variant in ['A', 'B']:
                        variant_feedback = feedback[feedback['variant'] == variant]
                        if not variant_feedback.empty:
                            stats[f"variant_{variant}"]["avg_rating"] = float(variant_feedback['rating'].mean())
                            stats[f"variant_{variant}"]["feedback_count"] = len(variant_feedback)
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistics error: {str(e)}")
            return {"error": str(e)}
    
    def get_log(self, variant=None, limit=None):
        try:
            df = self.log_df.copy()
            
            if variant:
                df = df[df['variant'] == variant]
            
            if limit:
                df = df.tail(limit)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Get log error: {str(e)}")
            return []
