import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [mealPlan, setMealPlan] = useState(null);
  const [mealPlanId, setMealPlanId] = useState(null);
  const [groceryList, setGroceryList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedMeal, setSelectedMeal] = useState(null);

  // Auth Form States
  const [authForm, setAuthForm] = useState({ username: '', password: '' });

  // Profile Form States
  const [profileForm, setProfileForm] = useState({
    gender: 'male',
    age: 25,
    weight: 70,
    height: 170,
    activity_level: 'moderately_active',
    fitness_goal: 'maintain_weight',
    calorie_target: 2000,
    protein_target: 150,
    fiber_target: 25,
    dietary_restrictions: [],
    allergies: []
  });

  const [dietaryInput, setDietaryInput] = useState('');
  const [allergyInput, setAllergyInput] = useState('');

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_URL}/api/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setProfile(data.profile);
        if (data.profile) {
          setCurrentPage('dashboard');
          fetchLatestMealPlan();
        } else {
          setCurrentPage('profile');
        }
      } else {
        throw new Error('Failed to fetch profile');
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      handleLogout();
    }
  };

  const fetchLatestMealPlan = async () => {
    try {
      const response = await fetch(`${API_URL}/api/meal-plan/latest`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMealPlan(data.meal_plan);
        setMealPlanId(data.meal_plan_id);
      }
    } catch (err) {
      console.error('No meal plan found:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileForm)
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfile(data.profile);
        setCurrentPage('dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save profile');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMealPlan = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/meal-plan/generate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMealPlan(data.meal_plan);
        setMealPlanId(data.meal_plan_id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate meal plan');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleDiningOut = async (day, mealType) => {
    const dayData = mealPlan.days.find(d => d.day === day);
    const currentStatus = dayData[mealType].dining_out;
    
    try {
      const response = await fetch(`${API_URL}/api/meal-plan/update-meal`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          meal_plan_id: mealPlanId,
          day: day,
          meal_type: mealType,
          dining_out: !currentStatus
        })
      });
      
      if (response.ok) {
        // Update local state
        const updatedMealPlan = { ...mealPlan };
        const dayIndex = updatedMealPlan.days.findIndex(d => d.day === day);
        updatedMealPlan.days[dayIndex][mealType].dining_out = !currentStatus;
        setMealPlan(updatedMealPlan);
      }
    } catch (err) {
      console.error('Error updating meal:', err);
    }
  };

  const handleFetchGroceryList = async () => {
    if (!mealPlanId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/grocery-list/${mealPlanId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGroceryList(data.ingredients);
        setCurrentPage('grocery');
      }
    } catch (err) {
      setError('Failed to fetch grocery list');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setProfile(null);
    setMealPlan(null);
    setMealPlanId(null);
    setCurrentPage('login');
  };

  const addDietaryRestriction = () => {
    if (dietaryInput.trim()) {
      setProfileForm({
        ...profileForm,
        dietary_restrictions: [...profileForm.dietary_restrictions, dietaryInput.trim()]
      });
      setDietaryInput('');
    }
  };

  const removeDietaryRestriction = (index) => {
    setProfileForm({
      ...profileForm,
      dietary_restrictions: profileForm.dietary_restrictions.filter((_, i) => i !== index)
    });
  };

  const addAllergy = () => {
    if (allergyInput.trim()) {
      setProfileForm({
        ...profileForm,
        allergies: [...profileForm.allergies, allergyInput.trim()]
      });
      setAllergyInput('');
    }
  };

  const removeAllergy = (index) => {
    setProfileForm({
      ...profileForm,
      allergies: profileForm.allergies.filter((_, i) => i !== index)
    });
  };

  const openMealDetail = (day, mealType) => {
    setSelectedDay(day);
    setSelectedMeal(mealType);
  };

  const closeMealDetail = () => {
    setSelectedDay(null);
    setSelectedMeal(null);
  };

  // ============ RENDER FUNCTIONS ============

  const renderLogin = () => (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="heading-1">NutriPlan</h1>
        <p className="body-medium" style={{ marginBottom: '32px', color: 'var(--text-secondary)' }}>
          Your personalized meal planning assistant
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="body-medium">Username</label>
            <input
              type="text"
              className="input-field"
              value={authForm.username}
              onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label className="body-medium">Password</label>
            <input
              type="password"
              className="input-field"
              value={authForm.password}
              onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
              required
            />
          </div>
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Loading...' : 'Login'}
          </button>
        </form>
        
        <p className="body-small" style={{ marginTop: '24px', textAlign: 'center' }}>
          Don't have an account?{' '}
          <button className="link-text" onClick={() => setCurrentPage('register')} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            Register here
          </button>
        </p>
      </div>
    </div>
  );

  const renderRegister = () => (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="heading-1">Create Account</h1>
        <p className="body-medium" style={{ marginBottom: '32px', color: 'var(--text-secondary)' }}>
          Start your personalized nutrition journey
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label className="body-medium">Username</label>
            <input
              type="text"
              className="input-field"
              value={authForm.username}
              onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label className="body-medium">Password</label>
            <input
              type="password"
              className="input-field"
              value={authForm.password}
              onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
              required
            />
          </div>
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Loading...' : 'Register'}
          </button>
        </form>
        
        <p className="body-small" style={{ marginTop: '24px', textAlign: 'center' }}>
          Already have an account?{' '}
          <button className="link-text" onClick={() => setCurrentPage('login')} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            Login here
          </button>
        </p>
      </div>
    </div>
  );

  const renderProfile = () => (
    <div className="profile-container">
      <div className="profile-card">
        <h1 className="heading-2">Complete Your Profile</h1>
        <p className="body-medium" style={{ marginBottom: '32px', color: 'var(--text-secondary)' }}>
          Help us create your perfect meal plan
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleProfileSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="body-medium">Gender</label>
              <select
                className="input-field"
                value={profileForm.gender}
                onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="form-group">
              <label className="body-medium">Age</label>
              <input
                type="number"
                className="input-field"
                value={profileForm.age}
                onChange={(e) => setProfileForm({ ...profileForm, age: parseInt(e.target.value) })}
                required
              />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label className="body-medium">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                className="input-field"
                value={profileForm.weight}
                onChange={(e) => setProfileForm({ ...profileForm, weight: parseFloat(e.target.value) })}
                required
              />
            </div>
            
            <div className="form-group">
              <label className="body-medium">Height (cm)</label>
              <input
                type="number"
                step="0.1"
                className="input-field"
                value={profileForm.height}
                onChange={(e) => setProfileForm({ ...profileForm, height: parseFloat(e.target.value) })}
                required
              />
            </div>
          </div>
          
          <div className="form-group">
            <label className="body-medium">Activity Level</label>
            <select
              className="input-field"
              value={profileForm.activity_level}
              onChange={(e) => setProfileForm({ ...profileForm, activity_level: e.target.value })}
            >
              <option value="sedentary">Sedentary (little or no exercise)</option>
              <option value="lightly_active">Lightly Active (1-3 days/week)</option>
              <option value="moderately_active">Moderately Active (3-5 days/week)</option>
              <option value="very_active">Very Active (6-7 days/week)</option>
              <option value="extremely_active">Extremely Active (athlete)</option>
            </select>
          </div>
          
          <div className="form-group">
            <label className="body-medium">Fitness Goal</label>
            <select
              className="input-field"
              value={profileForm.fitness_goal}
              onChange={(e) => setProfileForm({ ...profileForm, fitness_goal: e.target.value })}
            >
              <option value="weight_loss">Weight Loss</option>
              <option value="muscle_build">Muscle Build</option>
              <option value="more_fiber">Increase Fiber Intake</option>
              <option value="maintain_weight">Maintain Weight</option>
              <option value="general_health">General Health</option>
            </select>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label className="body-medium">Daily Calorie Target</label>
              <input
                type="number"
                className="input-field"
                value={profileForm.calorie_target}
                onChange={(e) => setProfileForm({ ...profileForm, calorie_target: parseInt(e.target.value) })}
              />
            </div>
            
            <div className="form-group">
              <label className="body-medium">Daily Protein Target (g)</label>
              <input
                type="number"
                className="input-field"
                value={profileForm.protein_target}
                onChange={(e) => setProfileForm({ ...profileForm, protein_target: parseInt(e.target.value) })}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label className="body-medium">Daily Fiber Target (g)</label>
            <input
              type="number"
              className="input-field"
              value={profileForm.fiber_target}
              onChange={(e) => setProfileForm({ ...profileForm, fiber_target: parseInt(e.target.value) })}
            />
          </div>
          
          <div className="form-group">
            <label className="body-medium">Dietary Restrictions</label>
            <div className="tag-input-container">
              <input
                type="text"
                className="input-field"
                placeholder="e.g., vegetarian, gluten-free"
                value={dietaryInput}
                onChange={(e) => setDietaryInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDietaryRestriction())}
              />
              <button type="button" className="btn-secondary" onClick={addDietaryRestriction}>
                Add
              </button>
            </div>
            <div className="tag-list">
              {profileForm.dietary_restrictions.map((item, index) => (
                <span key={index} className="tag">
                  {item}
                  <button type="button" onClick={() => removeDietaryRestriction(index)}>×</button>
                </span>
              ))}
            </div>
          </div>
          
          <div className="form-group">
            <label className="body-medium">Allergies</label>
            <div className="tag-input-container">
              <input
                type="text"
                className="input-field"
                placeholder="e.g., peanuts, dairy"
                value={allergyInput}
                onChange={(e) => setAllergyInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
              />
              <button type="button" className="btn-secondary" onClick={addAllergy}>
                Add
              </button>
            </div>
            <div className="tag-list">
              {profileForm.allergies.map((item, index) => (
                <span key={index} className="tag">
                  {item}
                  <button type="button" onClick={() => removeAllergy(index)}>×</button>
                </span>
              ))}
            </div>
          </div>
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save Profile & Continue'}
          </button>
        </form>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard-container">
      <nav className="navbar">
        <h2 className="heading-3">NutriPlan</h2>
        <div className="nav-links">
          <button className="nav-link" onClick={() => setCurrentPage('dashboard')}>
            Meal Plan
          </button>
          {mealPlanId && (
            <button className="nav-link" onClick={handleFetchGroceryList}>
              Grocery List
            </button>
          )}
          <button className="nav-link" onClick={() => setCurrentPage('profile')}>
            Profile
          </button>
          <button className="btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>
      
      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h1 className="heading-2">Your 7-Day Meal Plan</h1>
            <p className="body-medium" style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
              {profile && `Goal: ${profile.fitness_goal.replace('_', ' ')} | ${profile.calorie_target} kcal/day`}
            </p>
          </div>
          <button 
            className="btn-primary" 
            onClick={handleGenerateMealPlan}
            disabled={loading}
          >
            {loading ? 'Generating...' : mealPlan ? 'Regenerate Plan' : 'Generate Meal Plan'}
          </button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        {loading && !mealPlan && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p className="body-large">Generating your personalized meal plan...</p>
            <p className="body-small" style={{ color: 'var(--text-secondary)' }}>This may take up to 30 seconds</p>
          </div>
        )}
        
        {mealPlan && (
          <div className="meal-plan-grid">
            {mealPlan.days.map((day) => (
              <div key={day.day} className="day-card">
                <h3 className="heading-4">Day {day.day}</h3>
                
                {['breakfast', 'lunch', 'dinner'].map((mealType) => {
                  const meal = day[mealType];
                  if (!meal) return null;
                  
                  return (
                    <div key={mealType} className={`meal-card ${meal.dining_out ? 'dining-out' : ''}`}>
                      <div className="meal-header">
                        <span className="meal-type">{mealType.charAt(0).toUpperCase() + mealType.slice(1)}</span>
                        <label className="dining-out-toggle">
                          <input
                            type="checkbox"
                            checked={meal.dining_out}
                            onChange={() => handleToggleDiningOut(day.day, mealType)}
                          />
                          <span className="caption">Dining Out</span>
                        </label>
                      </div>
                      
                      <h4 className="body-large" style={{ fontWeight: 600, margin: '8px 0' }}>
                        {meal.name}
                      </h4>
                      
                      <div className="nutrition-summary">
                        <div className="nutrition-item">
                          <span className="caption">Calories</span>
                          <span className="body-small">{meal.nutrition.calories}</span>
                        </div>
                        <div className="nutrition-item">
                          <span className="caption">Protein</span>
                          <span className="body-small">{meal.nutrition.protein}g</span>
                        </div>
                        <div className="nutrition-item">
                          <span className="caption">Fiber</span>
                          <span className="body-small">{meal.nutrition.fiber}g</span>
                        </div>
                      </div>
                      
                      <button 
                        className="view-recipe-btn"
                        onClick={() => openMealDetail(day.day, mealType)}
                      >
                        View Recipe
                      </button>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
        
        {!mealPlan && !loading && (
          <div className="empty-state">
            <p className="body-large">No meal plan yet. Click "Generate Meal Plan" to get started!</p>
          </div>
        )}
      </div>
      
      {selectedDay !== null && selectedMeal !== null && (
        <div className="modal-overlay" onClick={closeMealDetail}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {(() => {
              const dayData = mealPlan.days.find(d => d.day === selectedDay);
              const meal = dayData[selectedMeal];
              
              return (
                <>
                  <div className="modal-header">
                    <h2 className="heading-3">{meal.name}</h2>
                    <button className="close-btn" onClick={closeMealDetail}>×</button>
                  </div>
                  
                  <div className="modal-body">
                    <div className="nutrition-details">
                      <h3 className="heading-4">Nutrition Facts</h3>
                      <div className="nutrition-grid">
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Calories</span>
                          <span className="body-large">{meal.nutrition.calories} kcal</span>
                        </div>
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Protein</span>
                          <span className="body-large">{meal.nutrition.protein}g</span>
                        </div>
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Carbs</span>
                          <span className="body-large">{meal.nutrition.carbs}g</span>
                        </div>
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Fat</span>
                          <span className="body-large">{meal.nutrition.fat}g</span>
                        </div>
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Fiber</span>
                          <span className="body-large">{meal.nutrition.fiber}g</span>
                        </div>
                        <div className="nutrition-detail-item">
                          <span className="body-medium">Sugar</span>
                          <span className="body-large">{meal.nutrition.sugar}g</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="recipe-section">
                      <h3 className="heading-4">Ingredients</h3>
                      <ul className="ingredient-list">
                        {meal.recipe.ingredients.map((ingredient, index) => (
                          <li key={index} className="body-medium">{ingredient}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="recipe-section">
                      <h3 className="heading-4">Instructions</h3>
                      <ol className="instruction-list">
                        {meal.recipe.instructions.map((instruction, index) => (
                          <li key={index} className="body-medium">{instruction}</li>
                        ))}
                      </ol>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );

  const renderGroceryList = () => (
    <div className="dashboard-container">
      <nav className="navbar">
        <h2 className="heading-3">NutriPlan</h2>
        <div className="nav-links">
          <button className="nav-link" onClick={() => setCurrentPage('dashboard')}>
            Meal Plan
          </button>
          <button className="nav-link" onClick={handleFetchGroceryList}>
            Grocery List
          </button>
          <button className="nav-link" onClick={() => setCurrentPage('profile')}>
            Profile
          </button>
          <button className="btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>
      
      <div className="dashboard-content">
        <h1 className="heading-2">Your Grocery List</h1>
        <p className="body-medium" style={{ color: 'var(--text-secondary)', marginTop: '8px', marginBottom: '32px' }}>
          Ingredients for meals you're cooking this week
        </p>
        
        {groceryList.length > 0 ? (
          <div className="grocery-list-card">
            <ul className="grocery-list">
              {groceryList.map((ingredient, index) => (
                <li key={index} className="grocery-item body-medium">
                  <span className="grocery-bullet">•</span>
                  {ingredient}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="empty-state">
            <p className="body-large">No items in your grocery list</p>
          </div>
        )}
      </div>
    </div>
  );

  // Main render
  return (
    <div className="App">
      {!token && currentPage === 'login' && renderLogin()}
      {!token && currentPage === 'register' && renderRegister()}
      {token && currentPage === 'profile' && renderProfile()}
      {token && currentPage === 'dashboard' && renderDashboard()}
      {token && currentPage === 'grocery' && renderGroceryList()}
    </div>
  );
}

export default App;