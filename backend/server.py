from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
import uuid
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="NutriPlan API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "nutriplan_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 10080))

# Password hashing - using pbkdf2_sha256 for compatibility
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

# LLM Configuration
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# ============ Pydantic Models ============

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    gender: str
    age: int
    weight: float  # in kg
    height: float  # in cm
    activity_level: str  # sedentary, lightly_active, moderately_active, very_active, extremely_active
    fitness_goal: str  # weight_loss, muscle_build, more_fiber, maintain_weight, etc.
    calorie_target: Optional[int] = None
    protein_target: Optional[int] = None
    fiber_target: Optional[int] = None
    dietary_restrictions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

class MealPlanRequest(BaseModel):
    user_id: str

class UpdateMealRequest(BaseModel):
    meal_plan_id: str
    day: int  # 1-7
    meal_type: str  # breakfast, lunch, dinner
    dining_out: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# ============ Authentication Functions ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = plain_password.encode('utf-8')[:72]
    plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        user = await db.users.find_one({"user_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# ============ AI Meal Plan Generation ============

async def generate_meal_plan_with_ai(profile: dict) -> dict:
    """Generate a 7-day meal plan using Claude Sonnet-4"""
    
    # Build a detailed prompt for meal planning
    prompt = f"""You are a professional nutritionist. Generate a detailed 7-day meal plan for a user with the following profile:

Gender: {profile.get('gender', 'Not specified')}
Age: {profile.get('age', 'Not specified')}
Weight: {profile.get('weight', 'Not specified')} kg
Height: {profile.get('height', 'Not specified')} cm
Activity Level: {profile.get('activity_level', 'Not specified')}
Fitness Goal: {profile.get('fitness_goal', 'Not specified')}
Calorie Target: {profile.get('calorie_target', 'Calculate based on profile')} kcal/day
Protein Target: {profile.get('protein_target', 'Calculate based on profile')} g/day
Fiber Target: {profile.get('fiber_target', 'Calculate based on profile')} g/day
Dietary Restrictions: {', '.join(profile.get('dietary_restrictions', [])) or 'None'}
Allergies: {', '.join(profile.get('allergies', [])) or 'None'}

Please create a complete 7-day meal plan with breakfast, lunch, and dinner for each day. For each meal, provide:
1. Meal name
2. Detailed recipe with ingredients and instructions
3. Nutritional information: calories, protein, carbs, fat, fiber, sugar

Return the response as a valid JSON object with this exact structure:
{{
  "days": [
    {{
      "day": 1,
      "breakfast": {{
        "name": "Meal name",
        "recipe": {{
          "ingredients": ["ingredient 1", "ingredient 2"],
          "instructions": ["step 1", "step 2"]
        }},
        "nutrition": {{
          "calories": 400,
          "protein": 25,
          "carbs": 45,
          "fat": 12,
          "fiber": 8,
          "sugar": 5
        }}
      }},
      "lunch": {{ ... }},
      "dinner": {{ ... }}
    }}
  ]
}}

Make sure the total daily nutrition aligns with the user's targets. Return ONLY the JSON object, no additional text."""

    try:
        # Initialize LLM chat with Claude Sonnet-4
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"meal-plan-{uuid.uuid4()}",
            system_message="You are a professional nutritionist who creates detailed meal plans in JSON format."
        ).with_model("anthropic", "claude-sonnet-4-20250514")
        
        # Send message to AI
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        # Remove markdown code blocks if present
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        meal_plan_data = json.loads(response_text)
        return meal_plan_data
        
    except Exception as e:
        print(f"Error generating meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate meal plan: {str(e)}")

# ============ API Endpoints ============

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "NutriPlan API"}

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    new_user = {
        "user_id": user_id,
        "username": user_data.username,
        "password": hashed_password,
        "profile": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.users.insert_one(new_user)
    
    # Create access token
    access_token = create_access_token({"sub": user_id})
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user"""
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token({"sub": user["user_id"]})
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "profile": current_user.get("profile")
    }

@app.post("/api/profile")
async def create_or_update_profile(profile: UserProfile, current_user: dict = Depends(get_current_user)):
    """Create or update user profile"""
    profile_data = profile.dict()
    
    # Update user document with profile
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"profile": profile_data, "updated_at": datetime.utcnow().isoformat()}}
    )
    
    return {"message": "Profile updated successfully", "profile": profile_data}

@app.post("/api/meal-plan/generate")
async def generate_meal_plan(current_user: dict = Depends(get_current_user)):
    """Generate a new 7-day meal plan using AI"""
    
    # Check if user has a profile
    if not current_user.get("profile"):
        raise HTTPException(status_code=400, detail="Please complete your profile first")
    
    profile = current_user["profile"]
    
    # Generate meal plan using AI
    meal_plan_data = await generate_meal_plan_with_ai(profile)
    
    # Add dining_out flag to all meals
    for day in meal_plan_data.get("days", []):
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type in day:
                day[meal_type]["dining_out"] = False
    
    # Save meal plan to database
    meal_plan_id = str(uuid.uuid4())
    meal_plan_doc = {
        "meal_plan_id": meal_plan_id,
        "user_id": current_user["user_id"],
        "meal_plan": meal_plan_data,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.meal_plans.insert_one(meal_plan_doc)
    
    return {
        "meal_plan_id": meal_plan_id,
        "meal_plan": meal_plan_data,
        "message": "Meal plan generated successfully"
    }

@app.get("/api/meal-plan/latest")
async def get_latest_meal_plan(current_user: dict = Depends(get_current_user)):
    """Get the latest meal plan for the current user"""
    
    meal_plan = await db.meal_plans.find_one(
        {"user_id": current_user["user_id"]},
        sort=[("created_at", -1)]
    )
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found. Please generate one first.")
    
    return {
        "meal_plan_id": meal_plan["meal_plan_id"],
        "meal_plan": meal_plan["meal_plan"],
        "created_at": meal_plan["created_at"]
    }

@app.put("/api/meal-plan/update-meal")
async def update_meal_dining_status(request: UpdateMealRequest, current_user: dict = Depends(get_current_user)):
    """Update dining out status for a specific meal"""
    
    meal_plan = await db.meal_plans.find_one({
        "meal_plan_id": request.meal_plan_id,
        "user_id": current_user["user_id"]
    })
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Update the specific meal's dining_out status
    days = meal_plan["meal_plan"]["days"]
    for day in days:
        if day["day"] == request.day:
            if request.meal_type in day:
                day[request.meal_type]["dining_out"] = request.dining_out
                break
    
    # Save updated meal plan
    await db.meal_plans.update_one(
        {"meal_plan_id": request.meal_plan_id},
        {"$set": {"meal_plan.days": days}}
    )
    
    return {"message": "Meal updated successfully"}

@app.get("/api/grocery-list/{meal_plan_id}")
async def get_grocery_list(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    """Generate a grocery list from the meal plan"""
    
    meal_plan = await db.meal_plans.find_one({
        "meal_plan_id": meal_plan_id,
        "user_id": current_user["user_id"]
    })
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Aggregate all ingredients from meals that are not marked as dining_out
    all_ingredients = []
    
    for day in meal_plan["meal_plan"]["days"]:
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type in day:
                meal = day[meal_type]
                # Only include meals that are not dining out
                if not meal.get("dining_out", False):
                    ingredients = meal.get("recipe", {}).get("ingredients", [])
                    all_ingredients.extend(ingredients)
    
    return {
        "meal_plan_id": meal_plan_id,
        "ingredients": all_ingredients
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)