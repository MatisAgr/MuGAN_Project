import { useState } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Music } from 'lucide-react';
import APP_NAME from '../constants/AppName';
import { Menu, MenuItem, ProductItem, HoveredLink } from './ui/navbar-menu';

export default function NavbarMenu() {
  const [active, setActive] = useState<string | null>(null);

  return (
    <div className="fixed top-8 inset-x-0 z-40 flex justify-center pointer-events-none">
      <div className="pointer-events-auto">
      <Menu setActive={setActive}>
        <Link to="/">
          <div className="flex items-center gap-2 cursor-pointer">
            <Music className="w-5 h-5 text-purple-400" />
            <span className="text-sm font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              {APP_NAME}
            </span>
          </div>
        </Link>
        
        <MenuItem setActive={setActive} active={active} item="Training">
          <div className="text-sm grid grid-cols-2 gap-6 p-4">
            <ProductItem
              title="Training Dashboard"
              href="/training"
              src="https://www.01net.com/app/uploads/2023/06/ia-musique-musicgen.jpg"
              description="Monitor AI model training with real-time metrics and visualizations"
            />
            <ProductItem
              title="Data Preprocessing"
              href="/preprocessing"
              src="https://bowwe.com/upload/domain/37991/images/060_AI-Stats/EN/Artificial-Intelligence-Statistics.webp"
              description="Extract notes from MIDI files, create sequences and generate statistics"
            />
          </div>
        </MenuItem>
        
        <Link to="/generator">
          <MenuItem setActive={setActive} active={active} item="Generator">
            <div className="flex flex-col space-y-3 p-2">
              <HoveredLink href="/generator" className="flex items-center gap-2 text-base font-medium">
                <Music className="w-5 h-5 text-purple-400" />
                <span>Music Generator</span>
              </HoveredLink>
              <p className="text-sm text-neutral-400 max-w-xs">
                Generate beautiful piano compositions with AI and visualize the audio spectrum
              </p>
            </div>
          </MenuItem>
        </Link>
        
        <MenuItem setActive={setActive} active={active} item="Database">
          <div className="text-sm grid grid-cols-2 gap-6 p-4">
            <ProductItem
              title="Training Data"
              href="/database?filter=training"
              src="https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=200&fit=crop"
              description="Browse the dataset used for training the AI model"
            />
            <ProductItem
              title="Generated Music"
              href="/database?filter=generated"
              src="https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=400&h=200&fit=crop"
              description="Explore music created by the community and AI"
            />
          </div>
        </MenuItem>
      </Menu>
      </div>
    </div>
  );
}
