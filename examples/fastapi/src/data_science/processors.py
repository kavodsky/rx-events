import asyncio
import time
import random
from typing import Dict, Any
import reactivex as rx
from reactivex import operators as ops

from rx_events import event_bus, EventStatus, EventAck




class DataScienceProcessors:
    def __init__(self):
        self.setup_event_subscriptions()

    def setup_event_subscriptions(self):
        """Subscribe to events and setup ack sending"""

        # User analysis events
        user_channel = event_bus.get_channel("user_analysis")
        user_channel.get_event_stream().pipe(
            ops.filter(lambda event: event.event_type == "user_behavior_analysis"),
            ops.flat_map(lambda event: self._process_with_acks(
                event, "user_analysis", self._process_user_behavior
            ))
        ).subscribe(
            on_error=lambda error: print(f"❌ User analysis stream error: {error}")
        )

        # Recommendation events
        rec_channel = event_bus.get_channel("recommendations")
        rec_channel.get_event_stream().pipe(
            ops.filter(lambda event: event.event_type == "recommendation_request"),
            ops.flat_map(lambda event: self._process_with_acks(
                event, "recommendations", self._process_recommendations
            ))
        ).subscribe(
            on_error=lambda error: print(f"❌ Recommendations stream error: {error}")
        )

        # Analytics events (fire and forget - no acks needed)
        analytics_channel = event_bus.get_channel("analytics")
        analytics_channel.get_event_stream().pipe(
            ops.filter(lambda event: event.event_type == "analytics_processing"),
            ops.map(lambda event: self._process_analytics_sync(event))
        ).subscribe(
            on_next=lambda result: print(f"✅ Analytics completed: {result['uuid']}"),
            on_error=lambda error: print(f"❌ Analytics error: {error}")
        )

    def _process_with_acks(self, event, channel_name: str, processor_func) -> rx.Observable:
        """Wrapper that handles acknowledgments"""

        async def process_and_ack():
            start_time = time.time()

            try:
                # Send "processing started" ack
                await self._send_ack(event.uuid, channel_name, EventStatus.PROCESSING)

                # Do the actual processing
                result = await processor_func(event)

                processing_time = time.time() - start_time

                # Send "completed" ack
                await self._send_ack(
                    event.uuid,
                    channel_name,
                    EventStatus.COMPLETED,
                    result=result,
                    processing_time=processing_time
                )

                return {
                    'uuid': event.uuid,
                    'status': 'completed',
                    'result': result,
                    'processing_time': processing_time
                }

            except Exception as e:
                processing_time = time.time() - start_time
                error_msg = str(e)

                print(f"💥 Processing failed for {event.uuid}: {error_msg}")

                # Send "failed" ack
                await self._send_ack(
                    event.uuid,
                    channel_name,
                    EventStatus.FAILED,
                    error=error_msg,
                    processing_time=processing_time
                )

                return {
                    'uuid': event.uuid,
                    'status': 'failed',
                    'error': error_msg,
                    'processing_time': processing_time
                }

        # Create a task from the coroutine for rx.from_future
        # Use ensure_future which works with both coroutines and futures
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        task = asyncio.ensure_future(process_and_ack(), loop=loop)
        return rx.from_future(task)

    async def _send_ack(self, event_uuid: str, channel_name: str, status: EventStatus,
                        result: Dict[str, Any] = None, error: str = None,
                        processing_time: float = None):
        """Send acknowledgment through event bus"""
        try:
            ack = EventAck(
                event_uuid=event_uuid,
                status=status,
                result=result,
                error=error,
                processing_time=processing_time
            )
            
            success = await event_bus.acknowledge(channel_name, ack)
            if success:
                print(f"✅ Sent ack for {event_uuid}: {status.value}")
            else:
                print(f"⚠️ Failed to send ack for {event_uuid}: event not found")
        except Exception as e:
            print(f"❌ Error sending ack for {event_uuid}: {e}")

    async def _process_user_behavior(self, event) -> Dict[str, Any]:
        """DS team's user behavior analysis"""
        print(f"🧠 Processing user behavior for UUID: {event.uuid}")

        # Simulate complex ML processing
        await asyncio.sleep(random.uniform(1, 4))

        # Simulate occasional failures
        if random.random() < 0.15:  # 15% failure rate
            raise Exception("ML model temporarily unavailable")

        # Extract data
        user_id = event.payload.get('user_id')
        behavior_data = event.payload.get('behavior_data', {})
        session_data = event.payload.get('session_data', {})

        # Complex ML analysis
        risk_score = random.uniform(0, 1)
        behavior_pattern = random.choice(['normal', 'suspicious', 'high_value', 'new_user'])
        anomaly_score = random.uniform(0, 0.3) if behavior_pattern == 'normal' else random.uniform(0.7, 1.0)

        # Feature engineering
        features = {
            'session_length': session_data.get('duration', 0),
            'page_views': behavior_data.get('page_views', 0),
            'click_rate': behavior_data.get('clicks', 0) / max(behavior_data.get('page_views', 1), 1),
            'time_on_site': session_data.get('time_on_site', 0)
        }

        # ML model predictions
        predictions = {
            'churn_probability': random.uniform(0, 1),
            'lifetime_value_estimate': random.uniform(100, 5000),
            'next_best_action': random.choice(['offer_discount', 'recommend_premium', 'send_newsletter', 'no_action'])
        }

        result = {
            'user_id': user_id,
            'risk_score': risk_score,
            'behavior_pattern': behavior_pattern,
            'anomaly_score': anomaly_score,
            'features': features,
            'predictions': predictions,
            'model_version': '2.1.3',
            'confidence': random.uniform(0.7, 0.95)
        }

        # Store results in DS database/cache
        await self._store_user_analysis(result)

        return result

    async def _process_recommendations(self, event) -> Dict[str, Any]:
        """DS team's recommendation engine"""
        print(f"🎯 Generating recommendations for UUID: {event.uuid}")

        # Simulate heavy ML processing
        await asyncio.sleep(random.uniform(2, 6))

        # Simulate failures
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Recommendation model overloaded")

        user_id = event.payload.get('user_id')
        context = event.payload.get('context', {})
        user_history = event.payload.get('user_history', [])

        # Complex recommendation algorithm
        num_recommendations = random.randint(5, 15)

        recommendations = []
        for i in range(num_recommendations):
            rec = {
                'item_id': f"item_{random.randint(1, 10000)}",
                'score': random.uniform(0.5, 1.0),
                'category': random.choice(['electronics', 'books', 'clothing', 'home', 'sports']),
                'price': random.uniform(10, 500),
                'reason': random.choice(['similar_users', 'past_purchases', 'trending', 'personalized'])
            }
            recommendations.append(rec)

        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # A/B testing group
        ab_test_group = random.choice(['control', 'variant_a', 'variant_b'])

        result = {
            'user_id': user_id,
            'recommendations': recommendations,
            'algorithm_version': '3.2.1',
            'ab_test_group': ab_test_group,
            'context_used': context,
            'total_candidates_evaluated': random.randint(1000, 50000),
            'personalization_strength': random.uniform(0.3, 0.9)
        }

        # Store recommendations
        await self._store_recommendations(result)

        return result

    def _process_analytics_sync(self, event) -> Dict[str, Any]:
        """DS team's analytics processing (synchronous, no acks)"""
        try:
            print(f"📊 Processing analytics for UUID: {event.uuid}")

            # Quick analytics processing
            metrics = event.payload.get('metrics', {})
            dimensions = event.payload.get('dimensions', {})

            # Statistical processing
            processed_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    processed_metrics[f"{key}_normalized"] = value / 100.0
                    processed_metrics[f"{key}_moving_avg"] = value * 0.8  # Simplified moving average
                    processed_metrics[f"{key}_trend"] = random.choice(['up', 'down', 'stable'])

            # Aggregations
            aggregations = {
                'total_events': len(metrics),
                'avg_value': sum(v for v in metrics.values() if isinstance(v, (int, float))) / max(len(metrics), 1),
                'max_value': max((v for v in metrics.values() if isinstance(v, (int, float))), default=0),
                'min_value': min((v for v in metrics.values() if isinstance(v, (int, float))), default=0)
            }

            result = {
                'uuid': event.uuid,
                'original_metrics': metrics,
                'processed_metrics': processed_metrics,
                'aggregations': aggregations,
                'dimensions': dimensions,
                'processing_timestamp': time.time(),
                'processor_version': '1.0.2'
            }

            # Store analytics (synchronous)
            self._store_analytics_result(result)
            return result

        except Exception as e:
            print(f"💥 Analytics processing failed for {event.uuid}: {e}")
            return {'uuid': event.uuid, 'error': str(e)}

    async def _store_user_analysis(self, result):
        """Store user analysis results"""
        # Simulate database storage
        await asyncio.sleep(0.1)
        print(f"💾 Stored user analysis for {result['user_id']} (confidence: {result['confidence']:.2f})")

    async def _store_recommendations(self, result):
        """Store recommendation results"""
        # Simulate database/cache storage
        await asyncio.sleep(0.1)
        print(f"💾 Stored {len(result['recommendations'])} recommendations for {result['user_id']}")

    def _store_analytics_result(self, result):
        """Store analytics results (synchronous)"""
        print(f"💾 Stored analytics for {result['uuid']} ({result['aggregations']['total_events']} events)")


# DS processors will be initialized in main.py after channels are created
ds_processors = None