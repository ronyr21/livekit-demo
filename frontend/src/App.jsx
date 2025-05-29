import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom'
import './App.css'
import LiveKitModal from './components/LiveKitModal';
import AdminDashboard from './components/AdminDashboard';

// Main component that handles navigation between customer and admin views
const MainApp = () => {
  const [showSupport, setShowSupport] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleSupportClick = () => {
    setShowSupport(true)
  }

  const handleAdminClick = () => {
    navigate('/admin');
  }

  const handleBackToMain = () => {
    navigate('/');
  }

  // Check if we're on admin page
  const isAdminPage = location.pathname.startsWith('/admin');

  return (
    <div className="app">
      <header className={`header ${isAdminPage ? 'admin-header' : ''}`}>
        <div className="logo">
          {isAdminPage ? 'AutoZone Admin' : 'AutoZone'}
        </div>
        {isAdminPage ? (
          <button onClick={handleBackToMain} className="back-to-main-button">
            ← Back to Main Site
          </button>
        ) : (
          <button onClick={handleAdminClick} className="admin-access-button">
            🎛️ Admin
          </button>
        )}
      </header>

      <Routes>
        <Route path="/" element={
          <main>
            <section className="hero">
              <h1>Get the Right Parts. Right Now</h1>
              <p>Free Next Day Delivery on Eligible Orders</p>
              <div className="search-bar">
                <input type="text" placeholder='Enter vehicle or part number'></input>
                <button>Search</button>
              </div>
            </section>

            <button className="support-button" onClick={handleSupportClick}>
              Talk to an Agent!
            </button>

            {showSupport && <LiveKitModal setShowSupport={setShowSupport}/>}
          </main>
        } />
        <Route path="/admin/*" element={<AdminDashboard />} />
      </Routes>
    </div>
  );
};

function App() {
  return (
    <Router>
      <MainApp />
    </Router>
  );
}

export default App
