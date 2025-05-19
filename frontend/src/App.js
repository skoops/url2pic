import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentScreenshot, setCurrentScreenshot] = useState(null);
  const [screenshots, setScreenshots] = useState([]);
  const [desktopResolution, setDesktopResolution] = useState("1920×1080");
  const [mobileResolution, setMobileResolution] = useState("375×667");
  const [desktopUserAgent, setDesktopUserAgent] = useState("");
  const [mobileUserAgent, setMobileUserAgent] = useState("");
  const [resolutions, setResolutions] = useState({
    desktop: [],
    mobile: []
  });
  const [userAgents, setUserAgents] = useState({
    desktop: [],
    mobile: []
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [activeTab, setActiveTab] = useState("form");

  useEffect(() => {
    // Fetch available resolutions and user agents
    const fetchData = async () => {
      try {
        const [resolutionsResponse, userAgentsResponse, screenshotsResponse] = await Promise.all([
          axios.get(`${API}/resolutions`),
          axios.get(`${API}/user-agents`),
          axios.get(`${API}/screenshots`)
        ]);
        
        setResolutions(resolutionsResponse.data);
        setUserAgents(userAgentsResponse.data);
        setScreenshots(screenshotsResponse.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        setErrorMessage("Failed to load initial data. Please refresh the page.");
      }
    };
    
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url) {
      setErrorMessage("Please enter a URL");
      return;
    }
    
    // Add protocol if missing
    let processedUrl = url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      processedUrl = 'https://' + url;
    }
    
    setIsLoading(true);
    setErrorMessage("");
    
    try {
      const response = await axios.post(`${API}/screenshots`, {
        url: processedUrl,
        desktop_resolution: desktopResolution,
        mobile_resolution: mobileResolution,
        desktop_user_agent: desktopUserAgent || undefined,
        mobile_user_agent: mobileUserAgent || undefined
      });
      
      setCurrentScreenshot(response.data);
      
      // Refresh the screenshots list
      const screenshotsResponse = await axios.get(`${API}/screenshots`);
      setScreenshots(screenshotsResponse.data);
      
      // Switch to the current tab
      setActiveTab("current");
    } catch (error) {
      console.error("Error capturing screenshot:", error);
      setErrorMessage(error.response?.data?.detail || "Failed to capture screenshot. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this screenshot?")) {
      return;
    }
    
    try {
      await axios.delete(`${API}/screenshots/${id}`);
      
      // If we deleted the current screenshot, clear it
      if (currentScreenshot && currentScreenshot.id === id) {
        setCurrentScreenshot(null);
      }
      
      // Update the screenshots list
      setScreenshots(screenshots.filter(screenshot => screenshot.id !== id));
    } catch (error) {
      console.error("Error deleting screenshot:", error);
      setErrorMessage("Failed to delete screenshot. Please try again.");
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const viewScreenshot = (screenshot) => {
    setCurrentScreenshot(screenshot);
    setActiveTab("current");
  };

  return (
    <div className="App min-h-screen bg-gray-100">
      {isLoading && (
        <div className="loading-overlay">
          <div className="w-full max-w-md px-4">
            <div className="text-center mb-4">
              <div className="w-12 h-12 mx-auto mb-3">
                <div className="loading-spinner"></div>
              </div>
              <h3 className="text-lg font-medium text-gray-800">Capturing Screenshots</h3>
              <p className="text-gray-600 mb-4">This may take a moment...</p>
            </div>
            <div className="bg-gray-200 rounded-full overflow-hidden">
              <div className="progress-bar"></div>
            </div>
            <p className="text-sm text-center text-gray-500 mt-2">
              Processing {url}
            </p>
          </div>
        </div>
      )}
      
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="container mx-auto">
          <h1 className="text-3xl font-bold">Website Screenshot Generator</h1>
          <p className="mt-2">Capture desktop and mobile screenshots of any website</p>
        </div>
      </header>

      <main className="container mx-auto p-4">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex border-b mb-6">
            <button 
              className={`py-2 px-4 font-medium ${activeTab === 'form' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
              onClick={() => setActiveTab('form')}
            >
              New Screenshot
            </button>
            <button 
              className={`py-2 px-4 font-medium ${activeTab === 'current' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
              onClick={() => setActiveTab('current')}
              disabled={!currentScreenshot}
            >
              Current Result
            </button>
            <button 
              className={`py-2 px-4 font-medium ${activeTab === 'gallery' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
              onClick={() => setActiveTab('gallery')}
            >
              Screenshot Gallery
            </button>
          </div>

          {errorMessage && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {errorMessage}
            </div>
          )}

          {activeTab === 'form' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-gray-700 font-medium mb-2" htmlFor="url">
                  Website URL
                </label>
                <input
                  type="text"
                  id="url"
                  className="w-full p-3 border border-gray-300 rounded-md"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Desktop Settings</h3>
                  
                  <div className="mb-4">
                    <label className="block text-gray-700 mb-2" htmlFor="desktopResolution">
                      Resolution
                    </label>
                    <select
                      id="desktopResolution"
                      className="w-full p-3 border border-gray-300 rounded-md"
                      value={desktopResolution}
                      onChange={(e) => setDesktopResolution(e.target.value)}
                    >
                      {resolutions.desktop.map((res) => (
                        <option key={res.label} value={res.label}>
                          {res.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="desktopUserAgent">
                      User Agent (Optional)
                    </label>
                    <select
                      id="desktopUserAgent"
                      className="w-full p-3 border border-gray-300 rounded-md"
                      value={desktopUserAgent}
                      onChange={(e) => setDesktopUserAgent(e.target.value)}
                    >
                      <option value="">Default (Browser's User Agent)</option>
                      {userAgents.desktop.map((agent) => (
                        <option key={agent.name} value={agent.value}>
                          {agent.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Mobile Settings</h3>
                  
                  <div className="mb-4">
                    <label className="block text-gray-700 mb-2" htmlFor="mobileResolution">
                      Resolution
                    </label>
                    <select
                      id="mobileResolution"
                      className="w-full p-3 border border-gray-300 rounded-md"
                      value={mobileResolution}
                      onChange={(e) => setMobileResolution(e.target.value)}
                    >
                      {resolutions.mobile.map((res) => (
                        <option key={res.label} value={res.label}>
                          {res.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="mobileUserAgent">
                      User Agent (Optional)
                    </label>
                    <select
                      id="mobileUserAgent"
                      className="w-full p-3 border border-gray-300 rounded-md"
                      value={mobileUserAgent}
                      onChange={(e) => setMobileUserAgent(e.target.value)}
                    >
                      <option value="">Default (Browser's User Agent)</option>
                      {userAgents.mobile.map((agent) => (
                        <option key={agent.name} value={agent.value}>
                          {agent.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-md font-medium"
                  disabled={isLoading}
                >
                  {isLoading ? 'Capturing...' : 'Capture Screenshots'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'current' && currentScreenshot && (
            <div className="space-y-6">
              <div className="border-b pb-4">
                <h2 className="text-xl font-semibold text-gray-800 mb-2">Screenshot Details</h2>
                <p className="text-gray-600">
                  <strong>URL:</strong> {currentScreenshot.url}
                </p>
                <p className="text-gray-600">
                  <strong>Created:</strong> {formatDate(currentScreenshot.created_at)}
                </p>
                <div className="flex space-x-2 mt-3">
                  <button
                    onClick={() => handleDelete(currentScreenshot.id)}
                    className="bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded-md text-sm font-medium"
                  >
                    Delete Screenshot
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Desktop View ({currentScreenshot.desktop_resolution})</h3>
                  <div className="border border-gray-300 rounded-md overflow-hidden bg-gray-100">
                    <img 
                      src={`${API}/screenshots/${currentScreenshot.id}/desktop?t=${Date.now()}`} 
                      alt="Desktop Screenshot" 
                      className="w-full"
                    />
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Mobile View ({currentScreenshot.mobile_resolution})</h3>
                  <div className="border border-gray-300 rounded-md overflow-hidden bg-gray-100">
                    <img 
                      src={`${API}/screenshots/${currentScreenshot.id}/mobile?t=${Date.now()}`} 
                      alt="Mobile Screenshot" 
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'gallery' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Screenshot Gallery</h2>
              
              {screenshots.length === 0 ? (
                <p className="text-gray-500">No screenshots yet. Capture your first one!</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {screenshots.map((screenshot) => (
                    <div key={screenshot.id} className="border border-gray-300 rounded-md overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
                      <div className="relative h-40 bg-gray-100">
                        <img 
                          src={`${API}/screenshots/${screenshot.id}/desktop?t=${Date.now()}`} 
                          alt="Screenshot Thumbnail" 
                          className="w-full h-full object-cover object-top"
                        />
                      </div>
                      <div className="p-4">
                        <div className="truncate text-gray-800 font-medium mb-1">{screenshot.url}</div>
                        <p className="text-gray-500 text-sm mb-3">{formatDate(screenshot.created_at)}</p>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => viewScreenshot(screenshot)}
                            className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded text-sm"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDelete(screenshot.id)}
                            className="bg-red-500 hover:bg-red-600 text-white py-1 px-3 rounded text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto text-center">
          <p>Website Screenshot Generator &copy; 2025</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
