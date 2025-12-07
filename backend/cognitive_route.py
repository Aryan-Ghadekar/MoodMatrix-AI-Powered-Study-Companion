# cognitive_route.py - FIXED Version
import asyncio
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List
from threading import Lock
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cognitive-load", tags=["Cognitive Load"])

# ===========================================================
# GLOBAL VARIABLES - MOVE THESE BEFORE ENDPOINTS
# ===========================================================
# Global variables for cognitive load monitoring
cognitive_load_data = {
    "current_load": 0.0,
    "emotion_load": 0.0,
    "body_load": 0.0,
    "status": "low",
    "last_alert": None,
    "is_monitoring": False,
    "message": "Waiting for data from cognitive fusion script"
}

# WebSocket connections with thread safety
active_connections: List[WebSocket] = []
connections_lock = asyncio.Lock()

# Alert throttling variables
last_alert_time = 0
alert_count = 0
alert_lock = Lock()

def can_send_alert():
    """Check if we can send an alert (max 2 per minute)"""
    global last_alert_time, alert_count
    
    with alert_lock:
        current_time = time.time()
        one_minute = 60  # 1 minute in seconds
        
        # Reset counter if more than 1 minute has passed
        if current_time - last_alert_time > one_minute:
            alert_count = 0
            last_alert_time = current_time
        
        # Check if we can send alert (max 2 per minute)
        if alert_count < 2:
            alert_count += 1
            logger.info(f"[ALERT] Alert allowed: {alert_count}/2 this minute")
            return True
        
        logger.info(f"[ALERT] Alert throttled: {alert_count}/2 alerts this minute")
        return False

class CognitiveLoadMonitor:
    def __init__(self):
        self.alert_threshold = 50.0  # Default threshold
        self.last_status_update = 0
    
    async def _send_alert_to_clients(self, load_value: float):
        """Send alert to all connected WebSocket clients with throttling"""
        if not can_send_alert():
            logger.info(f"[ALERT] Throttled - Load: {load_value:.2f}%")
            return
            
        logger.info(f"[ALERT] Sending alert: {load_value:.2f}%")
        alert_message = {
            "type": "cognitive_load_alert",
            "message": f"High cognitive load detected: {load_value:.1f}%",
            "load_value": load_value,
            "timestamp": time.time(),
            "alert_type": "warning"
        }
        
        async with connections_lock:
            disconnected = []
            for connection in active_connections:
                try:
                    await connection.send_json(alert_message)
                    logger.info(f"[ALERT] Alert sent to client")
                except Exception as e:
                    logger.error(f"[ALERT] Error sending alert to client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                if connection in active_connections:
                    active_connections.remove(connection)
    
    async def _send_status_update(self):
        """Send current status to all connected WebSocket clients every 5 seconds"""
        current_time = time.time()
        
        # Only send status updates every 5 seconds
        if current_time - self.last_status_update < 5:
            return
            
        self.last_status_update = current_time
        logger.debug("[WS] Sending status update to clients")
        
        status_message = {
            "type": "status_update",
            "data": cognitive_load_data
        }
        
        async with connections_lock:
            disconnected = []
            for connection in active_connections:
                try:
                    await connection.send_json(status_message)
                except Exception as e:
                    logger.error(f"[WS] Error sending status update to client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients safely
            for connection in disconnected:
                if connection in active_connections:
                    active_connections.remove(connection)

# Initialize monitor BEFORE using it in endpoints
monitor = CognitiveLoadMonitor()

# ===========================================================
# HTTP ENDPOINTS
# ===========================================================
@router.post("/update")
async def update_cognitive_load(data: dict):
    """Receive cognitive load updates via HTTP POST"""
    try:
        logger.info(f"[HTTP] Received cognitive data: {data.get('current_load', 0):.1f}%")
        
        current_load = float(data.get("current_load", 0))
        
        # Update global data
        cognitive_load_data.update({
            "current_load": current_load,
            "emotion_load": float(data.get("emotion_load", 0)),
            "body_load": float(data.get("body_load", 0)),
            "last_update": time.time(),
            "is_monitoring": True,
            "message": "Real-time data from cognitive fusion"
        })
        
        # Determine status based on threshold
        if current_load > monitor.alert_threshold:
            cognitive_load_data["status"] = "high"
            cognitive_load_data["last_alert"] = time.time()
            logger.warning(f"[ALERT] High cognitive load detected: {current_load:.1f}%")
        else:
            cognitive_load_data["status"] = "low"
            cognitive_load_data["last_alert"] = None
        
        return JSONResponse({
            "success": True,
            "message": "Cognitive load data updated successfully",
            "status": cognitive_load_data["status"]
        })
        
    except Exception as e:
        logger.error(f"[HTTP] Error updating cognitive load: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)

@router.get("/current-status")
async def get_current_cognitive_load():
    """Get current cognitive load status"""
    logger.info(f"[API] Status request - Current load: {cognitive_load_data['current_load']}%")
    return JSONResponse({
        "success": True,
        "data": cognitive_load_data
    })

@router.post("/set-threshold")
async def set_alert_threshold(threshold_data: dict):
    """Set cognitive load alert threshold"""
    threshold = threshold_data.get("threshold", 50.0)
    logger.info(f"[API] Setting threshold to {threshold}%")
    
    if threshold < 0 or threshold > 100:
        logger.warning(f"[API] Invalid threshold: {threshold}")
        return JSONResponse({
            "success": False,
            "message": "Threshold must be between 0 and 100"
        }, status_code=400)
    
    monitor.alert_threshold = threshold
    logger.info(f"[API] Threshold updated to {threshold}%")
    
    return JSONResponse({
        "success": True,
        "message": f"Alert threshold set to {threshold}%",
        "new_threshold": threshold
    })

# ===========================================================
# SIMPLIFIED FRONTEND-FRIENDLY ENDPOINTS
# ===========================================================
@router.get("/simple-status")
async def get_simple_status():
    """Get simplified status - perfect for frontend polling"""
    return JSONResponse({
        "success": True,
        "load": cognitive_load_data["current_load"],
        "status": cognitive_load_data["status"],
        "last_alert": cognitive_load_data["last_alert"],
        "threshold": monitor.alert_threshold,
        "timestamp": time.time()
    })

@router.get("/header-status")
async def get_header_status():
    """Get minimal status for header display"""
    current_load = cognitive_load_data["current_load"]
    status = cognitive_load_data["status"]
    
    # Return minimal data for header
    return JSONResponse({
        "load": round(current_load, 1),
        "status": status,
        "is_high": status == "high",
        "updated_at": cognitive_load_data.get("last_update", time.time())
    })

# ===========================================================
# WEBSOCKET ENDPOINTS (Optional - keep if needed)
# ===========================================================
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time cognitive load updates"""
    logger.info("[WS] New WebSocket connection attempt")
    await websocket.accept()
    
    async with connections_lock:
        active_connections.append(websocket)
    
    logger.info(f"[WS] Connection accepted. Total: {len(active_connections)}")
    
    try:
        await websocket.send_json({
            "type": "status_update",
            "data": cognitive_load_data
        })
        logger.info("[WS] Initial status sent")
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "cognitive_data_update":
                    logger.info(f"[WS] Received cognitive data: {message['current_load']:.1f}%")
                    
                    cognitive_load_data.update({
                        "current_load": message["current_load"],
                        "emotion_load": message.get("emotion_load", 0.0),
                        "body_load": message.get("body_load", 0.0),
                        "last_update": time.time(),
                        "is_monitoring": True,
                        "message": "Real-time data from cognitive fusion"
                    })
                    
                    if message["current_load"] > monitor.alert_threshold:
                        cognitive_load_data["last_alert"] = time.time()
                        cognitive_load_data["status"] = "high"
                        logger.warning(f"[ALERT] High cognitive load detected: {message['current_load']:.1f}%")
                        await monitor._send_alert_to_clients(message["current_load"])
                    else:
                        cognitive_load_data["status"] = "low"
                        
            except json.JSONDecodeError:
                logger.warning("[WS] Received non-JSON message")
                
    except WebSocketDisconnect:
        logger.info("[WS] WebSocket disconnected")
    except Exception as e:
        logger.error(f"[WS] WebSocket error: {e}")
    finally:
        async with connections_lock:
            if websocket in active_connections:
                active_connections.remove(websocket)
                logger.info(f"[WS] Connection removed. Total: {len(active_connections)}")

# ===========================================================
# OTHER ENDPOINTS (Keep existing)
# ===========================================================
@router.get("/history")
async def get_cognitive_load_history():
    """Get cognitive load history (last 6 readings)"""
    logger.debug("[API] History request")
    
    # Simulate some history data
    history = []
    base_time = time.time()
    for i in range(6, 0, -1):
        history.append({
            "timestamp": base_time - (i * 5),  # 5-second intervals
            "load": max(0, cognitive_load_data["current_load"] + (i * 2) - 10)  # Some variation
        })
    
    return JSONResponse({
        "success": True,
        "history": history
    })

@router.get("/system-status")
async def get_system_status():
    """Get complete system status"""
    status = {
        "websocket_connections": len(active_connections),
        "alert_threshold": monitor.alert_threshold,
        "alert_count_this_minute": alert_count,
        "last_alert_time": last_alert_time,
        "last_update": cognitive_load_data.get("last_update"),
        "cognitive_data": cognitive_load_data
    }
    
    return JSONResponse({
        "success": True,
        "data": status
    })

@router.get("/alert-stats")
async def get_alert_stats():
    """Get alert throttling statistics"""
    current_time = time.time()
    time_since_last_alert = current_time - last_alert_time if last_alert_time > 0 else 0
    alerts_remaining = max(0, 2 - alert_count)
    
    stats = {
        "alerts_this_minute": alert_count,
        "alerts_remaining": alerts_remaining,
        "time_since_last_alert": f"{time_since_last_alert:.1f}s",
        "can_send_alert": can_send_alert(),
        "alert_threshold": monitor.alert_threshold
    }
    
    return JSONResponse({
        "success": True,
        "data": stats
    })

async def periodic_status_updates():
    """Send periodic status updates to all connected clients"""
    while True:
        try:
            await monitor._send_status_update()
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"[PERIODIC] Error in status updates: {e}")
            await asyncio.sleep(5)

# Start the periodic updates when the module loads
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_status_updates())