import { Routes, Route } from "react-router-dom";

import ScrollToTop from "./utils/ScrollToTop";
import NavbarMenu from "./components/NavbarMenu";
import FloatingPlayer from "./components/FloatingPlayer";

import Home from "./pages/Home";
import TrainingDashboard from "./pages/TrainingDashboard";
import MusicGenerator from "./pages/MusicGenerator";
import MusicDatabase from "./pages/MusicDatabase";
import Preprocessing from "./pages/Preprocessing";

import { AudioPlayerProvider } from "./contexts/AudioPlayerContext";

// import Page404 from "./pages/Page404";
// import Notification from "./components/Notification";

//////////////////////////////////////////////////////////////////////////////////////////


export default function App() {
  return (
    <AudioPlayerProvider>
      <div className="min-h-screen">
        <NavbarMenu />
        {/* <Notification /> */}

        <div className="flex flex-col flex-grow">
          <ScrollToTop />
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/training" element={<TrainingDashboard />} />
              <Route path="/preprocessing" element={<Preprocessing />} />
              <Route path="/generator" element={<MusicGenerator />} />
              <Route path="/database" element={<MusicDatabase />} />

              {/* <Route path="/profile" element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              } /> */}

              {/* <Route path="*" element={<Page404 />} /> */}

            </Routes>
          </main>
        </div>

        <FloatingPlayer />
      </div>
    </AudioPlayerProvider>
  );
}