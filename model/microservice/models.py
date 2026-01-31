import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, '..', 'part1', 'artifacts', 'ab_test')
        
        self.data_dir = os.path.abspath(data_dir)
        self.model_a = None
        self.model_b = None
        self._load_models()
    
    def _load_models(self):
        try:
            model_a_path = os.path.join(self.data_dir, 'model_baseline.csv')
            model_b_path = os.path.join(self.data_dir, 'model_advanced2.csv')
            
            if os.path.exists(model_a_path):
                self.model_a = pd.read_csv(model_a_path)
                self.model_a['listing_id'] = self.model_a['listing_id'].astype(int)
                logger.info(f"Model A: {len(self.model_a)} records, {self.model_a['listing_id'].nunique()} listings")
            else:
                logger.error(f"Model A not found: {model_a_path}")
            
            if os.path.exists(model_b_path):
                self.model_b = pd.read_csv(model_b_path)
                self.model_b['listing_id'] = self.model_b['listing_id'].astype(int)
                logger.info(f"Model B: {len(self.model_b)} records, {self.model_b['listing_id'].nunique()} listings")
            else:
                logger.error(f"Model B not found: {model_b_path}")
                
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise
    
    def is_loaded(self):
        return self.model_a is not None and self.model_b is not None
    
    def predict(self, listing_id, top_k=3, variant='A'):
        try:
            listing_id = int(listing_id)
            model_data = self.model_a if variant == 'A' else self.model_b
            
            if model_data is None:
                return None
            
            listing_data = model_data[model_data['listing_id'] == listing_id]
            if listing_data.empty:
                return None
            
            # Group by aspect and aggregate
            aspect_scores = listing_data.groupby('aspect').agg({
                'score': 'sum',
                'positive': 'sum',
                'neutral': 'sum',
                'negative': 'sum',
                'total_mentions': 'sum'
            }).reset_index()
            
            top_aspects = aspect_scores.sort_values('score', ascending=False).head(top_k).to_dict('records')
            bottom_aspects = aspect_scores.sort_values('score', ascending=True).head(top_k).to_dict('records')
            
            return {
                'top_aspects': self._format_aspects(top_aspects),
                'bottom_aspects': self._format_aspects(bottom_aspects),
                'model_variant': variant
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return None
    
    def _format_aspects(self, aspects):
        return [{
            'aspect': a['aspect'],
            'score': float(a['score']),
            'positive': int(a.get('positive', 0)),
            'neutral': int(a.get('neutral', 0)),
            'negative': int(a.get('negative', 0)),
            'total_mentions': int(a['total_mentions'])
        } for a in aspects]
    
    def get_available_listings(self, variant='A'):
        model_data = self.model_a if variant == 'A' else self.model_b
        return sorted(model_data['listing_id'].unique().tolist()) if model_data is not None else []
    
    def get_timeline_data(self, listing_id):
        try:
            listing_id = int(listing_id)
            result = {
                'baseline': {'dates': [], 'counts': [], 'scores': []},
                'advanced': {'dates': [], 'counts': [], 'scores': []}
            }
            
            if self.model_a is not None and 'date' in self.model_a.columns:
                listing_data = self.model_a[self.model_a['listing_id'] == listing_id]
                if not listing_data.empty:
                    timeline = listing_data.groupby('date').agg({
                        'aspect': 'count',
                        'score': 'sum'
                    }).reset_index().rename(columns={'aspect': 'count'}).sort_values('date')
                    
                    result['baseline']['dates'] = timeline['date'].tolist()
                    result['baseline']['counts'] = timeline['count'].tolist()
                    result['baseline']['scores'] = timeline['score'].tolist()
            
            if self.model_b is not None and 'date' in self.model_b.columns:
                listing_data = self.model_b[self.model_b['listing_id'] == listing_id]
                if not listing_data.empty:
                    timeline = listing_data.groupby('date').agg({
                        'aspect': 'count',
                        'score': 'sum'
                    }).reset_index().rename(columns={'aspect': 'count'}).sort_values('date')
                    
                    result['advanced']['dates'] = timeline['date'].tolist()
                    result['advanced']['counts'] = timeline['count'].tolist()
                    result['advanced']['scores'] = timeline['score'].tolist()
            
            return result
            
        except Exception as e:
            logger.error(f"Timeline error: {str(e)}")
            return {
                'baseline': {'dates': [], 'counts': [], 'scores': []},
                'advanced': {'dates': [], 'counts': [], 'scores': []}
            }
