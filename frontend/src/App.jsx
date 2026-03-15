import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CharterRequest from './pages/CharterRequest';
import RouteMap from './pages/RouteMap';
import Negotiation from './pages/Negotiation';
import Analytics from './pages/Analytics';
import CaseStudy from './pages/CaseStudy';
import './index.css';

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/charter" element={<CharterRequest />} />
          <Route path="/routes" element={<RouteMap />} />
          <Route path="/negotiate" element={<Negotiation />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/case-study" element={<CaseStudy />} />
        </Routes>
      </Layout>
    </Router>
  );
}
