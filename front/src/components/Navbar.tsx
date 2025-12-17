import { Link, useLocation } from 'react-router-dom';
import { FaChartLine, FaMusic, FaDatabase } from 'react-icons/fa';
import APP_NAME from '../constants/AppName';

export default function Navbar() {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  const navItems = [
    { path: '/training', label: 'Training', icon: FaChartLine },
    { path: '/generator', label: 'Generator', icon: FaMusic },
    { path: '/database', label: 'Database', icon: FaDatabase },
  ];

  return (
    <nav className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <FaMusic className="text-2xl" />
            <span className="text-xl font-bold">{APP_NAME}</span>
          </Link>
          
          <div className="flex gap-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                  isActive(path)
                    ? 'bg-white text-indigo-600 font-semibold'
                    : 'hover:bg-white/10'
                }`}
              >
                <Icon />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
