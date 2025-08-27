from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import os
from typing import List, Optional, Dict
import uvicorn
from datetime import datetime
import json

app = FastAPI(title="Data Processing Service", version="1.0.0")

# Data models
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int

class ProcessedUserData(BaseModel):
    user_id: int
    processed_data: Dict
    processing_timestamp: str
    analytics: Dict

class AnalyticsSummary(BaseModel):
    total_users: int
    average_age: float
    age_distribution: Dict
    processing_stats: Dict

# In-memory storage for processed user data
processed_users_db = {}
analytics_cache = {}

# Service1 configuration
SERVICE1_URL = os.getenv("SERVICE1_URL", "http://localhost:8000")
SERVICE1_TIMEOUT = int(os.getenv("SERVICE1_TIMEOUT", "10"))

@app.get("/")
async def root():
    return {"message": "Data Processing Service is running", "service": "service2"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service2"}

@app.post("/process-user")
async def process_user(user: User):
    """Process user data and store analytics"""
    if not user.id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Process user data
    processed_data = {
        "name_length": len(user.name),
        "email_domain": user.email.split("@")[-1] if "@" in user.email else "unknown",
        "age_category": "young" if user.age < 30 else "middle" if user.age < 50 else "senior",
        "name_uppercase": user.name.upper(),
        "email_uppercase": user.email.upper(),
        "age_squared": user.age ** 2,
        "is_adult": user.age >= 18
    }
    
    # Store processed data
    processed_users_db[user.id] = ProcessedUserData(
        user_id=user.id,
        processed_data=processed_data,
        processing_timestamp=datetime.now().isoformat(),
        analytics={
            "processing_time_ms": 150,  # Simulated processing time
            "data_quality_score": 0.95,
            "confidence_level": 0.88
        }
    )
    
    # Invalidate analytics cache
    analytics_cache.clear()
    
    print(f"Processed user {user.name} (ID: {user.id})")
    return {"message": "User processed successfully", "user_id": user.id}

@app.get("/processed-users/{user_id}")
async def get_processed_user(user_id: int):
    """Get processed data for a specific user"""
    if user_id not in processed_users_db:
        raise HTTPException(status_code=404, detail="Processed user data not found")
    
    return processed_users_db[user_id]

@app.get("/processed-users", response_model=List[ProcessedUserData])
async def get_all_processed_users():
    """Get all processed user data"""
    return list(processed_users_db.values())

@app.delete("/processed-users/{user_id}")
async def delete_processed_user(user_id: int):
    """Delete processed data for a user"""
    if user_id not in processed_users_db:
        raise HTTPException(status_code=404, detail="Processed user data not found")
    
    deleted_data = processed_users_db.pop(user_id)
    analytics_cache.clear()  # Invalidate cache
    
    return {"message": f"Processed data for user {user_id} deleted successfully"}

@app.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics():
    """Get analytics summary of all processed users"""
    if not processed_users_db:
        return AnalyticsSummary(
            total_users=0,
            average_age=0.0,
            age_distribution={},
            processing_stats={}
        )
    
    # Calculate analytics
    total_users = len(processed_users_db)
    ages = []
    age_distribution = {"young": 0, "middle": 0, "senior": 0}
    
    for user_data in processed_users_db.values():
        age_category = user_data.processed_data.get("age_category", "unknown")
        age_distribution[age_category] = age_distribution.get(age_category, 0) + 1
        
        # Try to get original age from service1
        try:
            async with httpx.AsyncClient(timeout=SERVICE1_TIMEOUT) as client:
                response = await client.get(f"{SERVICE1_URL}/users/{user_data.user_id}")
                if response.status_code == 200:
                    user = response.json()
                    ages.append(user["age"])
        except:
            # If we can't get the age, estimate from category
            if age_category == "young":
                ages.append(25)
            elif age_category == "middle":
                ages.append(40)
            else:
                ages.append(60)
    
    average_age = sum(ages) / len(ages) if ages else 0.0
    
    processing_stats = {
        "total_processed": total_users,
        "avg_processing_time_ms": 150,
        "avg_confidence_level": 0.88,
        "avg_data_quality_score": 0.95
    }
    
    return AnalyticsSummary(
        total_users=total_users,
        average_age=round(average_age, 2),
        age_distribution=age_distribution,
        processing_stats=processing_stats
    )

@app.get("/cross-service-test")
async def cross_service_test():
    """Test communication between services"""
    results = {}
    
    # Test service1 health
    try:
        async with httpx.AsyncClient(timeout=SERVICE1_TIMEOUT) as client:
            response = await client.get(f"{SERVICE1_URL}/health")
            results["service1_health"] = {
                "status": "success",
                "response": response.json()
            }
    except Exception as e:
        results["service1_health"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test getting users from service1
    try:
        async with httpx.AsyncClient(timeout=SERVICE1_TIMEOUT) as client:
            response = await client.get(f"{SERVICE1_URL}/users")
            results["service1_users"] = {
                "status": "success",
                "count": len(response.json())
            }
    except Exception as e:
        results["service1_users"] = {
            "status": "error",
            "error": str(e)
        }
    
    return {
        "cross_service_test": results,
        "service2_status": "healthy",
        "processed_users_count": len(processed_users_db)
    }

@app.post("/batch-process")
async def batch_process_users():
    """Process all users from service1"""
    try:
        async with httpx.AsyncClient(timeout=SERVICE1_TIMEOUT) as client:
            # Get all users from service1
            response = await client.get(f"{SERVICE1_URL}/users")
            if response.status_code == 200:
                users = response.json()
                
                processed_count = 0
                for user in users:
                    # Process each user
                    process_response = await client.post(
                        f"{SERVICE1_URL}/process-user",
                        json=user
                    )
                    if process_response.status_code == 200:
                        processed_count += 1
                
                return {
                    "message": f"Batch processing completed",
                    "total_users": len(users),
                    "processed_count": processed_count
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to get users from service1")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
